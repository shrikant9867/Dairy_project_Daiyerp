# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,add_days,random_string
from erpnext.accounts.doctype.journal_entry.journal_entry \
	import get_average_exchange_rate, get_default_bank_cash_account
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_outstanding_invoices, get_account_currency, get_balance_on
from erpnext.accounts.doctype.payment_entry.payment_entry import get_outstanding_reference_documents
from frappe import _
import json
from dairy_erp.dairy_utils import  make_dairy_log
from dairy_erp.customization.payment_integration.payment_integration import pay_to_farmers_account
import calendar


def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():

	columns = [
		_("") + ":Data:40",_("Posting Date") + ":Date:90", _("Account") + ":Link/Account:200",
		 _("Party Type") + "::80", _("Party") + "::150",
		_("Debit") + ":Float:100", _("Credit") + ":Float:100",
		_("Voucher Type") + "::120", _("Voucher No") + ":Dynamic Link/"+_("Voucher Type")+":160",
		_("Against Voucher Type") + "::120", _("Against Voucher") + ":Dynamic Link/"+_("Against Voucher Type")+":160",
		_("Remarks") + "::400",_("Name") + ":Data:100",
	]

	return columns

def get_data(filters):
	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')

	supplier_data = frappe.db.sql(""" select 'test' as test,
		g3.posting_date, g3.account,g3.party_type,g3.party,0 as debit,
		(g3.credit-g3.debit)  as credit, g3.voucher_type,g3.voucher_no,
		g3.against_voucher_type, g3.against_voucher,g3.remarks,g3.name 
		from  
			(select g1.account,g1.party_type,g1.party,g1.voucher_type,g1.voucher_no,
			g1.against_voucher_type, g1.against_voucher,g1.remarks,g1.name,
			g1.posting_date,g1.credit,
			(select sum(debit) 
				from 
					`tabGL Entry` pe  
				where  
					pe.against_voucher=g1.voucher_no 
					group by pe.against_voucher) as debit  
			from  
					`tabGL Entry` g1  
			where  
				g1.voucher_type='Purchase Invoice' and g1.company = '{0}'
				{1}
				group by g1.against_voucher, g1.party 
				order by g1.posting_date,g1.party,g1.voucher_type)  g3 having credit > 0 """.
				format(vlcc,get_conditions(filters)),filters,as_list=True)

	customer_data = frappe.db.sql(""" select 'test' as test,
		g3.posting_date, g3.account,g3.party_type,g3.party,(g3.debit-g3.credit) as debit,
		 0 as credit, g3.voucher_type,g3.voucher_no,
		g3.against_voucher_type, g3.against_voucher,g3.remarks,g3.name 
		from  
			(select g1.account,g1.party_type,g1.party,g1.voucher_type,g1.voucher_no,
			g1.against_voucher_type, g1.against_voucher,g1.remarks,g1.name,
			g1.posting_date,g1.debit,
			(select sum(credit) 
				from 
					`tabGL Entry` pe  
				where  
					pe.against_voucher=g1.voucher_no 
					group by pe.against_voucher) as credit  
			from  
					`tabGL Entry` g1  
			where  
				g1.voucher_type='Sales Invoice' and g1.company = '{0}'
				{1}
				group by g1.against_voucher, g1.party  
				order by g1.posting_date,g1.party,g1.voucher_type)  g3 having debit > 0""".
				format(vlcc,get_conditions(filters)),filters,as_list=True)
		

	jv_data = frappe.db.sql("""select 'test' as test,g3.posting_date, g3.account,g3.party_type,
			g3.party,(g3.debit - ifnull((select sum(credit) from `tabGL Entry` where against_voucher = g3.voucher_no
			and against_voucher_type = g3.voucher_type and party_type = g3.party_type 
			and party=g3.party), 0)) as debit, 0 as credit, g3.voucher_type,g3.voucher_no,
			g3.against_voucher_type, g3.against_voucher,g3.remarks,g3.name 
		from 
			`tabGL Entry` g3
		where 
			voucher_type = 'Journal Entry' and company = '{0}' {1}
		having debit > 0
		""".format(vlcc,get_conditions_jv(filters)),filters,as_list=1,debug=0)
	return supplier_data + customer_data + jv_data 



def get_conditions_jv(filters):


	conditions = " and 1=1"

	if filters.get('farmer') and filters.get('prev_transactions'):
		farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")
		conditions += " and g3.posting_date <= %(end_date)s and g3.party = '{farmer_name}'".format(farmer_name=farmer_name)
	elif filters.get('farmer') and filters.get('cycle') and not filters.get('prev_transactions'):
		farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")
		conditions += " and g3.party = '{farmer_name}' and g3.posting_date between %(start_date)s and %(end_date)s".format(farmer_name=farmer_name)

	return conditions

def get_conditions(filters):


	conditions = " and 1=1"

	if filters.get('farmer') and filters.get('prev_transactions'):
		farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")
		conditions += " and g1.posting_date <= %(end_date)s and g1.party = '{farmer_name}'".format(farmer_name=farmer_name)
	elif filters.get('farmer') and filters.get('cycle') and not filters.get('prev_transactions'):
		farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")
		conditions += " and g1.party = '{farmer_name}' and g1.posting_date between %(start_date)s and %(end_date)s".format(farmer_name=farmer_name)

	return conditions

@frappe.whitelist()
def get_payment_amt(row_data,filters):

	report_data = get_data(json.loads(filters))
	row_data = json.loads(row_data)
	payble, receivable, set_amt = 0.0, 0.0, 0.0

	for data in report_data:
		if data[12] in row_data:
			if data[9] == "Purchase Invoice": payble += data[6]
			if data[9] == "Sales Invoice": receivable += data[5]
			if data[7] == "Journal Entry": receivable += data[5]

	return {"payble":payble,"receivable":receivable,"set_amt": min(payble,receivable)}

@frappe.whitelist()
def make_payment(data,row_data,filters):
	
	payable_data = get_payment_amt(row_data,filters)
	data = json.loads(data)
	row_data = json.loads(row_data)
	filters = json.loads(filters)
	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')
	farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")
	filters.update({"farmer":farmer_name})

	payble_list, recv_list = [], []

	for d in row_data:
		gl_doc = frappe.get_doc('GL Entry',d)
		if gl_doc.voucher_type == 'Purchase Invoice':
			payble_list.append(gl_doc.voucher_no)
		elif gl_doc.voucher_type in ['Sales Invoice','Journal Entry']:
			recv_list.append(gl_doc.voucher_no)
	
	try:
		payable = make_payble_payment(data=data,row_data=row_data,filters=filters,company=vlcc,payble_list=payble_list)
		receivable = make_receivable_payment(data=data,row_data=row_data,filters=filters,company=vlcc,recv_list=recv_list)
		due_pay = make_manual_payment(data=data,row_data=row_data,filters=filters,company=vlcc,payble_list=payble_list)

		voucher_nos = [payable, receivable, due_pay]
		make_payment_log(data=data,filters=filters, row_data= row_data, voucher_nos=voucher_nos,payable_data=payable_data)
		return {"payable":payable,"receivable":receivable,"due_pay":due_pay}
	except Exception,e:
		frappe.db.rollback() 
		make_dairy_log(title="Farmer Payment Entry Error",method="make_payment", status="Error",
					 message=e, traceback=frappe.get_traceback())


def make_payment_log(**kwargs):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)

	cycle_list = frappe.get_all('Farmer Date Computation',
		fields=["name", "start_date", "end_date"],filters = {"vlcc":user_doc.get('company')})

	farmer_payment_log = {}
	for d in kwargs.get('row_data'):
		gl_doc = frappe.get_doc('GL Entry',d)
		cycle = get_cycle(gl_doc.posting_date, cycle_list)
		if cycle:
			field = ('sales_voucher_no' if gl_doc.voucher_type in ['Sales Invoice','Journal Entry']
				else 'purchase_voucher_no')

			if cycle.name not in farmer_payment_log:
				args = {
					'start_date': cycle.start_date,
					'end_date': cycle.end_date,
					'farmer': kwargs.get('filters').get('farmer'),
					'company': frappe.db.get_value("User",{"name":frappe.session.user},'company'),
					'payable_data':kwargs.get('payable_data')
				}

				farmer_payment_log.setdefault(cycle.name, {})
				farmer_payment_log[cycle.name][field] = [gl_doc.voucher_no]
				farmer_payment_log[cycle.name]['total_pay'] = set_payble_amt(args)
				farmer_payment_log[cycle.name]['payment_entry'] = kwargs.get('voucher_nos')
				farmer_payment_log[cycle.name]['payable'] = gl_doc.credit
				farmer_payment_log[cycle.name]['receivable'] = gl_doc.debit
				farmer_payment_log[cycle.name].update(args)
			else:
				if not farmer_payment_log[cycle.name].get(field):
					 farmer_payment_log[cycle.name][field] = [gl_doc.voucher_no]
				else:
					farmer_payment_log[cycle.name][field].append(gl_doc.voucher_no)
				farmer_payment_log[cycle.name]['payable'] += gl_doc.credit
				farmer_payment_log[cycle.name]['receivable'] += gl_doc.debit

	for cycle, args in farmer_payment_log.items():
		make_farmer_voucher_log(cycle, args)

def make_farmer_voucher_log(cycle, args):

	try:
		sales_amount, purchase_amount = get_cycle_sales_purchase_paid_amt(args)
		if sales_amount > 0 or purchase_amount > 0:
			log_doc = frappe.new_doc("Farmer Payment Log")
			log_doc.total_pay = args.get('total_pay')
			log_doc.payble = args.get('payable_data').get('payble')#args.get('payable')
			log_doc.receivable = args.get('receivable')  
			log_doc.start_date = args.get('start_date') 
			log_doc.end_date = args.get('end_date') 
			log_doc.cycle = cycle
			log_doc.month = cycle.split("-")[1]
			log_doc.farmer = args.get('farmer')
			log_doc.vlcc = args.get('company')
			log_doc.settlement_date = nowdate()


			auto, manual = 0, purchase_amount
			if purchase_amount > sales_amount:
				manual = purchase_amount - sales_amount
				auto = sales_amount
			elif sales_amount > purchase_amount:
				manual = 0
				auto = purchase_amount

			log_doc.sales_amount = sales_amount
			log_doc.purchase_amount = purchase_amount
			log_doc.settled_amount = auto 
			log_doc.set_amt_manual = manual

			previous_amt = get_previous_amt(cycle, args.get('farmer'))
			total_pay = auto + manual + previous_amt

			log_doc.set_per = (total_pay/args.get('total_pay')) * 100
			log_doc.flags.ignore_permissions = True
			log_doc.save()
	except Exception, e:
		make_dairy_log(title="Farmer Payment Log Error",method="make_farmer_voucher_log", status="Error",
							 message=e, traceback=frappe.get_traceback())

def get_previous_amt(cycle, farmer):
	previous_amt = frappe.db.sql("""select ifnull(sum(settled_amount),0) +
		ifnull(sum(set_amt_manual), 0) from `tabFarmer Payment Log` where
		cycle = %s and farmer = %s""", (cycle, farmer), as_list=1)

	return previous_amt[0][0] if previous_amt and previous_amt[0] else 0

def get_cycle_sales_purchase_paid_amt(args):
	sales_amount = frappe.get_all('GL Entry', fields= ['ifnull(sum(credit),0) as amt'], 
		filters = {'voucher_no': ('in', args.get('payment_entry')),
			'against_voucher': ('in', args.get('sales_voucher_no')), 
			'against_voucher_type': ('in', ['Sales Invoice','Journal Entry']), 'voucher_type': 'Payment Entry'})

	sales_amount = sales_amount[0]['amt'] if sales_amount else 0


	purchase_amount = frappe.get_all('GL Entry', fields= ['ifnull(sum(debit), 0) as amt'], 
		filters = {'voucher_no': ('in', args.get('payment_entry')),
			'against_voucher': ('in', args.get('purchase_voucher_no')), 
			'against_voucher_type': 'Purchase Invoice', 'voucher_type': 'Payment Entry'})

	purchase_amount = purchase_amount[0]['amt'] if purchase_amount else 0

	return sales_amount, purchase_amount

def get_cycle(date, cycle_list):
	for d in cycle_list:
		if (getdate(d.start_date) <= getdate(date) 
			and getdate(date) <= getdate(d.end_date)):
			return d

def set_payble_amt(args):
	credit = frappe.db.sql("""select sum(g.credit) as credit
			from 
				`tabGL Entry` g,`tabPurchase Invoice` p 
			where 
				g.party = %(farmer)s and g.against_voucher_type in ('Purchase Invoice') 
				and (g.party is not null and g.party != '') and 
				g.docstatus < 2 and p.name = g.voucher_no and g.company = %(company)s 
				and p.posting_date between %(start_date)s and %(end_date)s 
				group by g.against_voucher, 
				g.party having credit > 0""",(args),as_dict=1)

	credit_list = [i.get('credit') for i in credit]

	return sum(credit_list)


def make_payble_payment(**kwargs):

	party_account = get_party_account("Supplier", kwargs.get('filters').get('farmer'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt'):
		amt = make_payment_entry(payment_type='Pay',args=kwargs,party_type='Supplier',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,ref_no="Auto Payble Settlement")
		return amt
	
def make_receivable_payment(**kwargs):

	party_account = get_party_account("Customer", kwargs.get('filters').get('farmer'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt'):
		amt = make_payment_entry(payment_type='Receive',args=kwargs,party_type='Customer',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,ref_no="Auto Receivable Settlement",)
		return amt

def make_manual_payment(**kwargs):

	party_account = get_party_account("Supplier", kwargs.get('filters').get('farmer'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt_manual'):
		amt = make_payment_entry(payment_type='Pay',args=kwargs,party_type='Supplier',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,is_manual=True)
		return amt

def make_payment_entry(**kwargs):

	try:
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = kwargs.get('payment_type')
		pe.company = kwargs.get('args').get('company')
		pe.posting_date = nowdate()
		pe.mode_of_payment = kwargs.get('args').get('data').get('mode_of_payment')
		pe.party_type = kwargs.get('party_type')
		pe.party = kwargs.get('args').get('filters').get('farmer')
		pe.paid_from = kwargs.get('party_account') if kwargs.get('payment_type')=="Receive" else kwargs.get('bank').account
		pe.paid_to = kwargs.get('party_account') if kwargs.get('payment_type')=="Pay" else kwargs.get('bank').account
		pe.flags.ignore_credit_validation = True if kwargs.get('payment_type') == 'Receive' else False
		pe.paid_from_account_currency = kwargs.get('party_account_currency') \
			if kwargs.get('payment_type')=="Receive" else kwargs.get('bank').account_currency
		pe.paid_to_account_currency = kwargs.get('party_account_currency') \
			if kwargs.get('payment_type')=="Pay" else kwargs.get('bank').account_currency 
		
		if (kwargs.get('payment_type')=="Pay" or kwargs.get('payment_type')=="Receive") and not kwargs.get('is_manual'):
			pe.paid_amount =kwargs.get('args').get('data').get('set_amt')
			pe.received_amount = kwargs.get('args').get('data').get('set_amt')
		elif kwargs.get('args').get('data').get('set_amt_manual'):
			pe.paid_amount =kwargs.get('args').get('data').get('set_amt_manual')
			pe.received_amount = kwargs.get('args').get('data').get('set_amt_manual')
		

		pe.allocate_payment_amount = 1


		args = {
			"posting_date": nowdate(),
			"company": pe.company,
			"party_type": pe.party_type,
			"payment_type": pe.payment_type,
			"party": pe.party,
			"party_account": pe.paid_from if pe.payment_type=="Receive" else pe.paid_to
		}
		outstanding_invoices = get_outstanding_reference_documents(args)
		party_amount = pe.paid_amount if pe.payment_type=="Receive" else pe.received_amount
		voucher_no_list = kwargs.get('args').get('payble_list') if kwargs.get('payment_type')=="Pay" else kwargs.get('args').get('recv_list')  #[frappe.db.get_value('GL Entry', d, 'voucher_no') for d in kwargs.get('args').get('row_data')]

		for d in outstanding_invoices:
			if d.voucher_no in voucher_no_list and party_amount > 0:
				allocated_amount = (d.outstanding_amount 
					if party_amount > d.outstanding_amount else party_amount)

				pe.append('references', {
					"reference_doctype": d.voucher_type,
					"reference_name": d.voucher_no,
					"due_date":d.due_date,
					"total_amount": d.invoice_amount,
					"outstanding_amount": d.outstanding_amount,
					"exchange_rate":d.exchange_rate,
					"allocated_amount":allocated_amount
				})

				party_amount -= allocated_amount

		if kwargs.get('args').get('data').get('set_amt_manual'):	
			pe.reference_no = kwargs.get('args').get('data').get('ref_no')
			pe.reference_date = kwargs.get('args').get('data').get('ref_date')
		else:
			pe.reference_no = kwargs.get('ref_no')
			pe.reference_date = nowdate()
		pe.flags.ignore_permissions = True
		pe.flags.ignore_mandatory = True
		pe.total_allocated_amount = party_amount
		pe.erp_ref_no = random_string(10)
		pe.save()
		vlcc_setting = frappe.get_doc("VLCC Settings",pe.company)
		if vlcc_setting.enable and kwargs.get('is_manual'):
			pay_to_farmers_account(pe)
		if not vlcc_setting.enable:
			pe.submit()
		if not kwargs.get('is_manual'):
			#payment integration settlement
			pe.submit()
		return pe.name
	except Exception,e: 
		make_dairy_log(title="Payment Entry Creation Error in Farmer Payment",method="make_payment_entry", status="Error",
					 message=e, traceback=frappe.get_traceback())

@frappe.whitelist()
def get_dates(filters):
	filters = json.loads(filters)
	return frappe.db.sql("""select start_date,end_date 
				from 
					`tabFarmer Date Computation` 
				where 
					name = %s""",(filters.get('cycle')),as_dict=1)

@frappe.whitelist()
def get_settlement_per(doctype,txt,searchfields,start,pagelen,filters):

	farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")
	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')

	conditions = " 1=1"
	per = frappe.db.sql("""select min_set_per from `tabFarmer Payment Cycle` where vlcc =%s""",
			(vlcc),as_dict=1) 
	if per: 
		if per[0].get('min_set_per') and per[0].get('min_set_per') != 100:
			conditions += " and set_per between {0} and 99".format(per[0].get('min_set_per'))

	count = frappe.db.sql("""select count(1) as count from `tabFarmer Payment Log` 
		where {0} and farmer =  '{1}' and vlcc = '{2}'
		""".format(conditions,farmer_name,vlcc),as_dict=True)


	if count:
		limit_count = int(count[0].get('count')) + 1 

		if farmer_name:
			cycles =frappe.db.sql("""select cy.name, 
						CONCAT(iFnull(round(cy.set_per,2),0),' %') as set_per, 
						cy.farmer from 
						(select c.name,CONCAT(iFnull(round(l.set_per,2),0),' %') as set_per,l.farmer 
						from 
							`tabFarmer Date Computation` as c
			 			left join 
			 				(select l1.farmer, l1.cycle,max(l1.set_per) as set_per 
			 				from 
			 					`tabFarmer Payment Log` l1
			 				where l1.farmer = '{farmer_name}' and l1.vlcc = '{vlcc}'
			 				group by l1.farmer, l1.cycle) as l on c.name = l.cycle 
			 				where 
			 				(l.farmer = '{farmer_name}' or l.farmer is NULL) and 
			 				(l.set_per<100 or l.set_per is NULL) and 
						c.end_date < curdate() and c.vlcc = '{vlcc}'
						order by c.end_date limit {limit_count}) as cy where cy.name like '{txt}'""".
						format(farmer_name=farmer_name,limit_count=limit_count,
							vlcc=vlcc,txt= "%%%s%%" % txt),as_list=True)

			cycle_list = frappe.db.sql_list("""select name from 
				`tabFarmer Date Computation` where vlcc = %s""",(vlcc))

			if cycles:
				return cycles
			else:
				if not cycle_list:
					frappe.throw("Please define cycle from <b>Farmer Payment Cycle</b> first")

	return []

@frappe.whitelist()
def skip_cycle(row_data,filters):

	row_data = json.loads(row_data)
	filters = json.loads(filters)

	farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")

	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')

	pi = frappe.db.sql("""select name  
		from    
			`tabPurchase Invoice`  
		where    
			status in ('Overdue','Unpaid') and 
			company = '{0}' and 
			not isnull(name) and supplier = '{1}' and posting_date between '{2}' and '{3}'""".
			format(vlcc,farmer_name,filters.get('start_date'),filters.get('end_date')),as_dict=True)

	si = frappe.db.sql("""select name  
		from    
			`tabSales Invoice`  
		where    
			status in ('Overdue','Unpaid') and 
			company = '{0}' and 
			not isnull(name) and customer = '{1}' and posting_date between '{2}' and '{3}'""".
			format(vlcc,farmer_name,filters.get('start_date'),filters.get('end_date')),as_dict=True)

	pi_list = [d.name for d in pi]

	si_list = [d.name for d in si]

	invoice_list = pi_list+si_list


	if farmer_name and filters.get('cycle'):
		log = frappe.db.get_value("Farmer Payment Log",{"farmer":farmer_name,"cycle":filters.get('cycle')},"name")
		if not log:
			if invoice_list:
				frappe.throw("You cannot skip the cycle because invoice are yet to settled.")
			else:
				log_doc = frappe.new_doc("Farmer Payment Log")
				log_doc.start_date = filters.get('start_date') 
				log_doc.end_date = filters.get('end_date') 
				log_doc.cycle = filters.get('cycle')
				log_doc.set_per = 100
				log_doc.month = filters.get('cycle').split("-")[1]
				log_doc.farmer = farmer_name
				log_doc.vlcc = vlcc
				log_doc.settlement_date = nowdate()
				log_doc.flags.ignore_permissions = True
				log_doc.save()
				frappe.msgprint(_("Cycle has been skipped"))
		else:
			frappe.throw("You cannot skip the cycle because invoice are yet to settled.")

@frappe.whitelist()
def check_cycle(row_data,filters):


	row_data = json.loads(row_data)
	filters = json.loads(filters)
	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')
	get_config = frappe.db.get_value('VLCC Settings',{'vlcc':vlcc},'cycle_hours') or 0
	month_list, receivable_list = [] , []
	cycle_msg,msg = "" , ""
	days = 0

	month_list = []

	for d in row_data:
		gl_doc = frappe.get_doc('GL Entry',d)

		receivable_list.append(gl_doc.against_voucher_type)

		if getdate(gl_doc.posting_date) < getdate(filters.get('start_date')):
			month_list.append({calendar.month_abbr[getdate(gl_doc.posting_date).month]:gl_doc.fiscal_year})

	if month_list:
		months = []
		for mon_dict in month_list:
			for month,year in mon_dict.items():
				cycle = frappe.db.get_value("Farmer Date Computation",{"month":month,"fiscal_year":year},"name")
				if cycle is None: 
					months.append(month+"("+str(year)+")")
		if months:
			cycle_msg = "Please add cycle for <b>{0}</b>".format(",".join(months))

	days = int(get_config)/24
	settlement_day = add_days(getdate(filters.get('end_date')),days)

	if getdate(nowdate()) <= getdate(settlement_day):
		msg = "Settlement can be done after <b>{0}</b>".format(settlement_day)

	recv_msg = check_receivable(receivable_list)

	return {"cycle_msg":cycle_msg,"recv_msg":recv_msg,"msg":msg}

def check_receivable(recv_list):
	
	if 'Sales Invoice' in recv_list and 'Purchase Invoice' not in recv_list:
		return "You can not settle only Receivable Amount"


@frappe.whitelist()
def generate_incentive(filters):
	filters = json.loads(filters)
	farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'), 'full_name')
	if not frappe.db.get_value("Purchase Invoice", {'cycle':filters.get('cycle'),\
		 'supplier': farmer_name, 'company': get_vlcc()},'name'):
		fmcr =  frappe.db.sql("""
			select ifnull(sum(amount),0) as total,
			ifnull(sum(milkquantity),0) as qty
		from 
			`tabFarmer Milk Collection Record`
		where 
			associated_vlcc = '{0}' and rcvdtime between '{1}' and '{2}' and farmerid= '{3}'
			""".format(get_vlcc(), filters.get('start_date'), filters.get('end_date'), filters.get('farmer')),as_dict=1)
		if fmcr[0].get('total') != 0:
			incentive = get_incentives(fmcr[0].get('total'), fmcr[0].get('qty'), get_vlcc())
			create_pi(filters, incentive)
			frappe.msgprint(_("Incentive Generated"))
	else:
		frappe.throw(_("Incentive already generated for this cycle"))

def create_pi(filters, total):
	pi = frappe.new_doc("Purchase Invoice")
	pi.supplier = frappe.db.get_value("Farmer",filters.get('farmer'), 'full_name')  
	pi_posting_date = filters.get('end_date')
	pi.company = get_vlcc()
	pi.cycle = filters.get('cycle')
	pi.pi_type = "Incentive"
	pi.append("items",
		{
			"qty":1,
			"item_code": "Milk Incentives",
			"rate": total,
			"amount": total,
			"cost_center": frappe.db.get_value("Company", get_vlcc(), "cost_center")
		})
	pi.flags.ignore_permissions = True
	pi.save()
	pi.submit()
	#updating date for current cycle
	gl_stock = frappe.db.get_value("Company", pi.company, 'stock_received_but_not_billed')
	gl_credit = frappe.db.get_value("Company", pi.company, 'default_payable_account')
	gl_name = frappe.db.get_value("GL Entry",{'account':gl_credit,'voucher_no':pi.name},'name')
	frappe.db.set_value("Purchase Invoice", pi.name, 'posting_date', filters.get('end_date'))
	frappe.db.set_value("GL Entry",{'account': gl_stock,'voucher_no':pi.name}, 'posting_date', filters.get('end_date'))
	frappe.db.get_value("GL Entry",gl_name, 'posting_date', filters.get('end_date'))
	frappe.db.sql("""update `tabGL Entry` set posting_date = '{0}' where name = '{1}'
		""".format(filters.get('end_date'),gl_name))

def get_incentives(amount, qty, vlcc=None):
	if vlcc and amount and qty:
		incentive = 0
		name = frappe.db.get_value("Farmer Settings", {'vlcc':vlcc}, 'name')
		farmer_settings = frappe.get_doc("Farmer Settings",name)
		if farmer_settings.enable_local_setting and not farmer_settings.enable_local_per_litre:
			incentive = (float(farmer_settings.local_farmer_incentive ) * float(amount)) / 100	
		if farmer_settings.enable_local_setting and farmer_settings.enable_local_per_litre:
			incentive = (float(farmer_settings.local_per_litre) * float(qty))
		if not farmer_settings.enable_local_setting and not farmer_settings.enable_per_litre:
			incentive = (float(farmer_settings.farmer_incentives) * float(amount)) / 100
		if not farmer_settings.enable_local_setting and farmer_settings.enable_per_litre:
			incentive = (float(farmer_settings.per_litre) * float(qty))
		return incentive



def get_vlcc():
	return frappe.db.get_value("User",frappe.session.user,'company')

@frappe.whitelist()
def is_fpcr_generated(filters):
	filters = json.loads(filters)
	si_records = frappe.get_all("Sales Invoice",fields=['name'],filters={'cycle_': filters.get('cycle'),\
	 	'type': ('in', ['Loan','Advance']),'customer': frappe.db.get_value("Farmer",filters.get('farmer'),'full_name')})

	if filters.get('cycle') and filters.get('farmer'):
		fpcr_records = frappe.get_all("Farmer Payment Cycle Report",fields=['count(name) as count']\
				,filters={'cycle': filters.get('cycle'), 'farmer_id': filters.get('farmer')})
		if len(si_records) and fpcr_records[0].get('count') == 0:
			return "creat"
		elif not len(si_records):
			return "ncreat"


