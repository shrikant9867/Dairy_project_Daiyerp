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
from frappe import _
import json
from dairy_erp import dairy_utils as utils

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

	supplier_data = frappe.db.sql("""select 'test' as test,posting_date, 
			account, party_type, party,0 as debit, sum(credit) - sum(debit) as credit,
			voucher_type, voucher_no, 
			against_voucher_type, against_voucher,remarks,name
		from 
			`tabGL Entry` 
		where  
			docstatus < 2 and against_voucher_type in ('Purchase Invoice')
			and (party is not null and party != '') and company = '{0}' {1}
			group by against_voucher, party
			having credit > 0
			order by posting_date,party,voucher_type""".format(vlcc,get_conditions(filters)),filters,as_list=True,debug=1)

	customer_data = frappe.db.sql("""select 'test' as test,posting_date, 
			account, party_type, party,sum(debit) - sum(credit) as debit, 0 as credit,
			voucher_type, voucher_no, 
			against_voucher_type, against_voucher,remarks,name
		from 
			`tabGL Entry` 
		where  
			docstatus < 2 and against_voucher_type in ('Sales Invoice')
			and (party is not null and party != '') and company = '{0}' {1}
			group by against_voucher, party
			having debit > 0
			order by posting_date,party,voucher_type""".format(vlcc,get_conditions(filters)),filters,as_list=True,debug=1)

	return supplier_data + customer_data

def get_conditions(filters):

	conditions = " and 1=1"

	if filters.get('farmer'):
		farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")
		conditions += " and party = '{farmer_name}'".format(farmer_name=farmer_name)
	conditions += " and posting_date between %(start_date)s and %(end_date)s"

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
	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')
	farmer_name = frappe.db.get_value("Farmer",filters.get('farmer'),"full_name")
	filters.update({"farmer":farmer_name})

	payble_list, recv_list = [], []

	for d in row_data:
		gl_doc = frappe.get_doc('GL Entry',d)
		if gl_doc.voucher_type == 'Purchase Invoice':
			payble_list.append(gl_doc.voucher_no)
		elif gl_doc.voucher_type == 'Sales Invoice':
			recv_list.append(gl_doc.voucher_no)
	
	set_payble_amt(filters=filters)
	make_payble_payment(data=data,row_data=row_data,filters=filters,company=vlcc,payble_list=payble_list)
	make_receivable_payment(data=data,row_data=row_data,filters=filters,company=vlcc,recv_list=recv_list)
	make_manual_payment(data=data,row_data=row_data,filters=filters,company=vlcc,payble_list=payble_list)
	make_payment_log(data=data,filters=filters)
	calculate_percentage(filters=filters)


def make_payment_log(**kwargs):

	log_doc = frappe.new_doc("Farmer Payment Log")
	log_doc.payble = kwargs.get('data').get('payble')
	log_doc.receivable = kwargs.get('data').get('receivable') 
	log_doc.settled_amount = kwargs.get('data').get('set_amt') 
	log_doc.set_amt_manual = kwargs.get('data').get('set_amt_manual') 
	log_doc.start_date = kwargs.get('filters').get('start_date') 
	log_doc.end_date = kwargs.get('filters').get('end_date') 
	log_doc.cycle = kwargs.get('filters').get('cycle')
	log_doc.month = kwargs.get('filters').get('cycle').split("-")[0]
	log_doc.flags.ignore_permissions = True
	log_doc.save()


def calculate_percentage(**kwargs):

	amt = 0.0

	logs = frappe.db.sql_list("""select name from `tabFarmer Payment Log` where cycle = %s""",(kwargs.get('filters').get('cycle')))

	for log in logs:
		l = frappe.get_doc("Farmer Payment Log",log)
		payble_amt = flt(l.settled_amount)+flt(l.set_amt_manual) if l.set_amt_manual else flt(l.settled_amount)
		amt += payble_amt

	try:
		date_doc = frappe.get_doc("Farmer Date Computation",kwargs.get('filters').get('cycle'))
		date_doc.set_per = (amt/date_doc.amount) * 100
		date_doc.outstanding_amount = date_doc.amount - amt
		date_doc.flags.ignore_permissions = True
		date_doc.save()
	except Exception,e: 
		utils.make_dairy_log(title="ZeroDivisionError-Dairy",method="set_percentage", status="Error",
					 message=e, traceback=frappe.get_traceback())


def set_payble_amt(**kwargs):

		vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')

		credit = frappe.db.sql("""select sum(g.credit) as credit,g.voucher_no ,p.posting_date
				from 
					`tabGL Entry` g,`tabPurchase Invoice` p 
				where 
					g.party = %s and g.against_voucher_type in ('Purchase Invoice') 
					and (g.party is not null and g.party != '') and 
					g.docstatus < 2 and p.name = g.voucher_no and g.company = %s and
					p.status!='Paid' and p.posting_date between %s and %s 
					group by g.against_voucher, 
					g.party having credit > 0""",(kwargs.get('filters').get('farmer'),vlcc,kwargs.get('filters').get('start_date'),
					kwargs.get('filters').get('end_date')),as_dict=1)

		credit_list = [i.get('credit') for i in credit]
		date_doc = frappe.get_doc("Farmer Date Computation",kwargs.get('filters').get('cycle'))
		date_doc.amount = sum(credit_list)
		date_doc.flags.ignore_permissions = True
		date_doc.save()


def make_payble_payment(**kwargs):

	party_account = get_party_account("Supplier", kwargs.get('filters').get('farmer'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt'):
		make_payment_entry(payment_type='Pay',args=kwargs,party_type='Supplier',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,ref_no="Auto Payble Settlement")
	
def make_receivable_payment(**kwargs):

	party_account = get_party_account("Customer", kwargs.get('filters').get('farmer'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt'):
		make_payment_entry(payment_type='Receive',args=kwargs,party_type='Customer',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,ref_no="Auto Receivable Settlement")

def make_manual_payment(**kwargs):

	party_account = get_party_account("Supplier", kwargs.get('filters').get('farmer'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt_manual'):
		make_payment_entry(payment_type='Pay',args=kwargs,party_type='Supplier',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,is_manual=True)

def make_payment_entry(**kwargs):

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = kwargs.get('payment_type')
	pe.company = kwargs.get('args').get('company')
	pe.posting_date = nowdate()
	pe.mode_of_payment = kwargs.get('args').get('data').get('mode_of_payment')
	pe.party_type = kwargs.get('party_type')
	pe.party = kwargs.get('args').get('filters').get('farmer')
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

	return frappe.db.sql("""select name,ifnull(round(set_per,2),'0') as set_per,
		ifnull(round(outstanding_amount,2),0) from `tabFarmer Date Computation` 
		where set_per<100 and name like '{txt}' """.format(txt= "%%%s%%" % txt),as_list=1)

@frappe.whitelist()
def get_default_cycle():
	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')
	due_date = frappe.db.sql("""select min(due_date) as date,name 
						from   
							`tabPurchase Invoice` 
						where   
							status in ('Overdue','Unpaid') and company = %s and  
							due_date between '2018-01-01' and '2018-12-31'""",
							(vlcc),as_dict=True)
	if due_date[0].get('name'):
		# try:
		return frappe.db.sql("""select name,start_date,end_date 
	 						from 
	 							`tabFarmer Date Computation` 
 							where 
	 							%s between start_date and end_date 
								and name is not null and name!= '' """,(due_date[0].get('date')),as_dict=True)
		# except Exception,e: 
		# 	return []
