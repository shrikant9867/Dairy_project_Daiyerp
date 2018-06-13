# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from erpnext.accounts.doctype.journal_entry.journal_entry \
	import get_average_exchange_rate, get_default_bank_cash_account
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_outstanding_invoices, get_account_currency, get_balance_on
from erpnext.accounts.doctype.payment_entry.payment_entry import get_outstanding_reference_documents
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from dairy_erp import dairy_utils as utils
from frappe import _
import json
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

	dairy = frappe.db.get_value("Company",{"is_dairy":1},'name')

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
				format(dairy,get_conditions(filters)),filters,as_list=True)

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
				format(dairy,get_conditions(filters)),filters,as_list=True)

	return supplier_data + customer_data

def get_conditions(filters):

	conditions = " and 1=1"

	if filters.get('vlcc') and filters.get('prev_transactions'):
		conditions += " and g1.posting_date <= %(end_date)s and g1.party = %(vlcc)s"
	elif filters.get('vlcc') and filters.get('cycle') and not filters.get('prev_transactions'):
		conditions += " and g1.party = %(vlcc)s and g1.posting_date between %(start_date)s and %(end_date)s"

	return conditions

@frappe.whitelist()
def get_payment_amt(row_data,filters):

	report_data = get_data(json.loads(filters))
	row_data = json.loads(row_data)

	payble = 0.0
	receivable = 0.0
	set_amt = 0.0

	for data in report_data:
		if data[12] in row_data:
			if data[9] == "Purchase Invoice":
				payble += data[6]
			if data[9] == "Sales Invoice":
				receivable += data[5]

	return {"payble":payble,"receivable":receivable,"set_amt": min(payble,receivable)}

@frappe.whitelist()
def make_payment(data,row_data,filters):
	
	data = json.loads(data)
	row_data = json.loads(row_data)
	filters = json.loads(filters)
	dairy = frappe.db.get_value("Company",{"is_dairy":1},'name')

	payble_list, recv_list = [], []

	for d in row_data:
		gl_doc = frappe.get_doc('GL Entry',d)
		if gl_doc.voucher_type == 'Purchase Invoice':
			payble_list.append(gl_doc.voucher_no)
		elif gl_doc.voucher_type == 'Sales Invoice':
			recv_list.append(gl_doc.voucher_no)
	
	try:
		payable = make_payble_payment(data=data,row_data=row_data,filters=filters,company=dairy,payble_list=payble_list)
		receivable = make_receivable_payment(data=data,row_data=row_data,filters=filters,company=dairy,recv_list=recv_list)
		due_pay = make_manual_payment(data=data,row_data=row_data,filters=filters,company=dairy,payble_list=payble_list)
		
		voucher_nos = [payable, receivable, due_pay]
		make_payment_log(data=data,filters=filters, row_data= row_data, voucher_nos=voucher_nos)
		return {"payable":payable,"receivable":receivable,"due_pay":due_pay}
	except Exception,e:
		frappe.db.rollback()  
		utils.make_dairy_log(title="VLCC Payment Entry Error",method="make_payment", status="Error",
					 message=e, traceback=frappe.get_traceback())


def make_payment_log(**kwargs):

	cycle_list = frappe.get_all('Cyclewise Date Computation',
		fields=["name", "start_date", "end_date"])

	vlcc_payment_log = {}
	for d in kwargs.get('row_data'):
		gl_doc = frappe.get_doc('GL Entry',d)
		cycle = get_cycle(gl_doc.posting_date, cycle_list)
		if cycle:
			field = ('sales_voucher_no' if gl_doc.voucher_type == 'Sales Invoice' 
				else 'purchase_voucher_no')

			if cycle.name not in vlcc_payment_log:
				args = {
					'start_date': cycle.start_date,
					'end_date': cycle.end_date,
					'vlcc': kwargs.get('filters').get('vlcc'),
					'company': frappe.db.get_value("Company",{"is_dairy":1},'name')
				}

				vlcc_payment_log.setdefault(cycle.name, {})
				vlcc_payment_log[cycle.name][field] = [gl_doc.voucher_no]
				vlcc_payment_log[cycle.name]['total_pay'] = set_payble_amt(args)
				vlcc_payment_log[cycle.name]['payment_entry'] = kwargs.get('voucher_nos')
				vlcc_payment_log[cycle.name]['payable'] = gl_doc.credit
				vlcc_payment_log[cycle.name]['receivable'] = gl_doc.debit
				vlcc_payment_log[cycle.name].update(args)
			else:
				if not vlcc_payment_log[cycle.name].get(field):
					 vlcc_payment_log[cycle.name][field] = [gl_doc.voucher_no]
				else:
					vlcc_payment_log[cycle.name][field].append(gl_doc.voucher_no)
				vlcc_payment_log[cycle.name]['payable'] += gl_doc.credit
				vlcc_payment_log[cycle.name]['receivable'] += gl_doc.debit

	for cycle, args in vlcc_payment_log.items():
		make_vlcc_voucher_log(cycle, args)

def make_vlcc_voucher_log(cycle, args):

	try:
		sales_amount, purchase_amount = get_cycle_sales_purchase_paid_amt(args)
		if sales_amount > 0 or purchase_amount > 0:
			log_doc = frappe.new_doc("VLCC Payment Log")
			log_doc.total_pay = args.get('total_pay')
			log_doc.payble = args.get('payable')
			log_doc.receivable = args.get('receivable')  
			log_doc.start_date = args.get('start_date') 
			log_doc.end_date = args.get('end_date') 
			log_doc.cycle = cycle
			log_doc.month = cycle.split("-")[1]
			log_doc.vlcc = args.get('vlcc')


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

			previous_amt = get_previous_amt(cycle, args.get('vlcc'))
			total_pay = auto + manual + previous_amt

			log_doc.set_per = (total_pay/args.get('total_pay')) * 100
			log_doc.flags.ignore_permissions = True
			log_doc.save()
	except Exception, e:
		utils.make_dairy_log(title="VLCC Payment Log Error",method="make_vlcc_voucher_log", status="Error",
							 message=e, traceback=frappe.get_traceback())

def get_previous_amt(cycle, vlcc):
	previous_amt = frappe.db.sql(""" select ifnull(sum(settled_amount),0) +
		ifnull(sum(set_amt_manual), 0) from `tabVLCC Payment Log` where
		cycle = %s and vlcc = %s""", (cycle, vlcc), as_list=1)

	return previous_amt[0][0] if previous_amt and previous_amt[0] else 0

def get_cycle_sales_purchase_paid_amt(args):
	sales_amount = frappe.get_all('GL Entry', fields= ['ifnull(sum(credit),0) as amt'], 
		filters = {'voucher_no': ('in', args.get('payment_entry')),
			'against_voucher': ('in', args.get('sales_voucher_no')), 
			'against_voucher_type': 'Sales Invoice', 'voucher_type': 'Payment Entry'})

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
				g.party = %(vlcc)s and g.against_voucher_type in ('Purchase Invoice') 
				and (g.party is not null and g.party != '') and 
				g.docstatus < 2 and p.name = g.voucher_no and g.company = %(company)s 
				and p.posting_date between %(start_date)s and %(end_date)s 
				group by g.against_voucher, 
				g.party having credit > 0""",(args),as_dict=1)

	credit_list = [i.get('credit') for i in credit]

	return sum(credit_list)

def make_payble_payment(**kwargs):

	party_account = get_party_account("Supplier", kwargs.get('filters').get('vlcc'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt'):
		amt = make_payment_entry(payment_type='Pay',args=kwargs,party_type='Supplier',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,ref_no="Auto Payble Settlement")
		return amt
	
def make_receivable_payment(**kwargs):

	party_account = get_party_account("Customer", kwargs.get('filters').get('vlcc'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt'):
		amt = make_payment_entry(payment_type='Receive',args=kwargs,party_type='Customer',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,ref_no="Auto Receivable Settlement")
		return amt

def make_manual_payment(**kwargs):

	party_account = get_party_account("Supplier", kwargs.get('filters').get('vlcc'), kwargs.get('company'))
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
		pe.party = kwargs.get('args').get('filters').get('vlcc')
		pe.paid_from = kwargs.get('party_account') if kwargs.get('payment_type')=="Receive" else kwargs.get('bank').account
		pe.paid_to = kwargs.get('party_account') if kwargs.get('payment_type')=="Pay" else kwargs.get('bank').account
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
		pe.save()
		pe.submit()

		make_pe_against_invoice(pe.name,kwargs)

		return pe.name
	except Exception,e: 
		utils.make_dairy_log(title="Payment Entry Creation Error in VLCC Payment",method="make_payment_entry", status="Error",
					 message=e, traceback=frappe.get_traceback())

def make_pe_against_invoice(pe,kwargs):
	dairy = frappe.db.get_value("Company",{"is_dairy":1},'name')
	pe_doc = frappe.get_doc("Payment Entry",pe)
	for row in pe_doc.references:
		if row.reference_doctype == 'Purchase Invoice':
			pi_doc = frappe.get_doc("Purchase Invoice",row.reference_name)
			si = frappe.db.get_value("Sales Invoice",
					{"vlcc_milk_collection_record":pi_doc.vlcc_milk_collection_record},"name")
			if si:
				si_doc = frappe.get_doc("Sales Invoice",si)
				create_payment_entry(si_doc,row,kwargs)
		elif row.reference_doctype == 'Sales Invoice':
			si_doc = frappe.get_doc("Sales Invoice",row.reference_name)
			
			if si_doc.purchase_invoice:
				pi_doc = frappe.get_doc("Purchase Invoice",si_doc.purchase_invoice)
				create_payment_entry(pi_doc,row,kwargs)

def create_payment_entry(doc,row,kwargs):

	party_type = ""
	if row.reference_doctype == 'Purchase Invoice':
		party_account = get_party_account("Customer", doc.customer, doc.company)
		party_type = "Customer"
		party = doc.customer
		ref_doc = "Sales Invoice"
		payment_type = "Receive"
		ref_no = 'Auto Settlement on PI'
		default_bank_cash_account = get_default_bank_cash_account(doc.company, "Bank")
		if not default_bank_cash_account:
			default_bank_cash_account = get_default_bank_cash_account(doc.company, "Cash")
		party_account_currency = get_account_currency(party_account)
	elif row.reference_doctype == 'Sales Invoice':
		party_account = get_party_account("Supplier", doc.supplier, doc.company)
		party_type = "Supplier"
		party = doc.supplier
		ref_doc = "Purchase Invoice"
		payment_type = "Pay"
		ref_no = 'Auto Settlement on SI'
		default_bank_cash_account = get_default_bank_cash_account(doc.company, "Bank")
		if not default_bank_cash_account:
			default_bank_cash_account = get_default_bank_cash_account(doc.company, "Cash")
		party_account_currency = get_account_currency(party_account)
	
	try:
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = payment_type
		pe.company = doc.company
		pe.posting_date = nowdate()
		pe.mode_of_payment = kwargs.get('args').get('data').get('mode_of_payment')
		pe.party_type = party_type
		pe.party = party
		pe.paid_from = party_account if payment_type=="Receive" else default_bank_cash_account.account
		pe.paid_to = party_account if payment_type=="Pay" else default_bank_cash_account.account
		pe.paid_from_account_currency = party_account_currency \
			if payment_type=="Receive" else default_bank_cash_account.account_currency
		pe.paid_to_account_currency = party_account_currency \
			if payment_type=="Pay" else default_bank_cash_account.account_currency
		
		pe.paid_amount = row.allocated_amount
		pe.received_amount = row.allocated_amount

		pe.allocate_payment_amount = 1	
		party_amount = pe.paid_amount if pe.payment_type=="Receive" else pe.received_amount

		pe.append('references', {
			"reference_doctype": ref_doc,
			"reference_name": doc.name,
			"due_date":doc.due_date,
			"total_amount": doc.grand_total,
			"outstanding_amount": doc.outstanding_amount,
			"allocated_amount":row.allocated_amount
		})
		
		pe.reference_no = ref_no
		pe.reference_date = nowdate()
		pe.flags.ignore_permissions = True
		pe.flags.ignore_mandatory = True
		pe.total_allocated_amount = party_amount
		pe.save()
		pe.submit()

	except Exception,e: 
		utils.make_dairy_log(title="Payment Entry Creation Error Against SI in VLCC Payment",method="make_payment_entry", status="Error",
					 message=e, traceback=frappe.get_traceback())


@frappe.whitelist()
def get_dates(filters):

	filters = json.loads(filters)
	return frappe.db.sql("""select start_date,end_date 
				from 
					`tabCyclewise Date Computation` 
				where 
					name = %s""",(filters.get('cycle')),as_dict=1)


@frappe.whitelist()
def get_settlement_per(doctype,txt,searchfields,start,pagelen,filters):

	conditions = " 1=1"
	cycle = frappe.db.get_singles_dict('VLCC Payment Cycle')
	if cycle.get('min_set_per') and cycle.get('min_set_per') != 100:
		conditions += " and set_per between {0} and 99".format(cycle.get('min_set_per'))

	count = frappe.db.sql("""select count(1) as count from `tabVLCC Payment Log` 
		where {0} and vlcc = '{1}'
		""".format(conditions,filters.get('vlcc')),as_dict=1)

	if count:
		limit_count = int(count[0].get('count')) + 1 

		if filters.get('vlcc'):
			cycles = frappe.db.sql("""select cy.name, 
						CONCAT(iFnull(round(cy.set_per,2),0),' %') as set_per, 
						cy.vlcc from 
						(select c.name,CONCAT(iFnull(round(l.set_per,2),0),' %') as set_per,l.vlcc 
						from 
							`tabCyclewise Date Computation` as c
			 			left join 
			 				(select l1.vlcc, l1.cycle,max(l1.set_per) as set_per 
			 				from 
			 					`tabVLCC Payment Log` l1
			 				where l1.vlcc = '{vlcc}'
			 				group by l1.vlcc, l1.cycle) as l on c.name = l.cycle 
			 				where 
			 				(l.vlcc = '{vlcc}' or l.vlcc is NULL) and 
			 				(l.set_per<100 or l.set_per is NULL) and 
						c.end_date < curdate()
						order by c.end_date limit {limit_count}) as cy where cy.name like '{txt}'""".
						format(vlcc=filters.get('vlcc'),limit_count=limit_count,txt= "%%%s%%" % txt),as_list=True)

			cycle_list = frappe.db.sql_list("""select name from 
				`tabCyclewise Date Computation`""")

			if cycles:
				return cycles
			else:
				if not cycle_list:
					frappe.throw("Please define cycle from <b>VLCC Payment Cycle</b> first")
	return []


@frappe.whitelist()
def skip_cycle(row_data,filters):

	row_data = json.loads(row_data)
	filters = json.loads(filters)

	dairy = frappe.db.get_value("Company",{"is_dairy":1},'name')

	pi = frappe.db.sql("""select name  
		from    
			`tabPurchase Invoice`  
		where    
			status in ('Overdue','Unpaid') and 
			company = '{0}' and 
			not isnull(name) and supplier = '{1}' and posting_date between '{2}' and '{3}'""".
			format(dairy,filters.get('vlcc'),filters.get('start_date'),filters.get('end_date')),as_dict=True)

	si = frappe.db.sql("""select name  
		from    
			`tabSales Invoice`  
		where    
			status in ('Overdue','Unpaid') and 
			company = '{0}' and 
			not isnull(name) and customer = '{1}' and posting_date between '{2}' and '{3}'""".
			format(dairy,filters.get('vlcc'),filters.get('start_date'),filters.get('end_date')),as_dict=True)

	pi_list = [d.name for d in pi]

	si_list = [d.name for d in si]

	invoice_list = pi_list+si_list


	if filters.get('vlcc') and filters.get('cycle'):
		log =frappe.db.get_value("VLCC Payment Log",{"vlcc":filters.get('vlcc'),"cycle":filters.get('cycle')},"name")
		if not log:
			if invoice_list:
				frappe.throw("You cannot skip the cycle because invoice are yet to settled.")
			else:
				log_doc = frappe.new_doc("VLCC Payment Log")
				log_doc.start_date = filters.get('start_date') 
				log_doc.end_date = filters.get('end_date') 
				log_doc.cycle = filters.get('cycle')
				log_doc.set_per = 100
				log_doc.month = filters.get('cycle').split("-")[1]
				log_doc.vlcc = filters.get('vlcc')
				log_doc.flags.ignore_permissions = True
				log_doc.save()
				frappe.msgprint(_("Cycle has been skipped"))
		else:
			frappe.throw("You cannot skip the cycle because invoice are yet to settled.")


@frappe.whitelist()
def check_cycle(row_data,filters):

	row_data = json.loads(row_data)
	filters = json.loads(filters)
	month_list, receivable_list = [] , []
	cycle_msg = ""

	for d in row_data:
		gl_doc = frappe.get_doc('GL Entry',d)

		receivable_list.append(gl_doc.against_voucher_type)

		if getdate(gl_doc.posting_date) < getdate(filters.get('start_date')):
			month_list.append({calendar.month_abbr[getdate(gl_doc.posting_date).month]:gl_doc.fiscal_year})

	if month_list:
		months = []
		for mon_dict in month_list:
			for month,year in mon_dict.items():
				cycle = frappe.db.get_value("Cyclewise Date Computation",{"month":month,"fiscal_year":year},"name")
				if cycle is None: 
					months.append(month+"("+str(year)+")")
		if months:
			cycle_msg = "Please add cycle for <b>{0}</b>".format(",".join(months))

	recv_msg = check_receivable(receivable_list)

	return {"cycle_msg":cycle_msg,"recv_msg":recv_msg}

def check_receivable(recv_list):
	
	if 'Sales Invoice' in recv_list and 'Purchase Invoice' not in recv_list:
		return "You can not settle only Receivable Amount"