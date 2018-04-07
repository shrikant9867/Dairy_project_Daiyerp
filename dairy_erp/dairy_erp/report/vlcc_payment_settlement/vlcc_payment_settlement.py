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
from dairy_erp import dairy_utils as utils
from frappe import _
import json

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
				format(dairy,get_conditions(filters)),filters,as_list=True,debug=1)

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

	if filters.get('vlcc'):
		conditions += " and g1.party = %(vlcc)s"
	conditions += " and g1.posting_date between %(start_date)s and %(end_date)s"

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
	
	# set_payble_amt(filters=filters)
	make_payble_payment(data=data,row_data=row_data,filters=filters,company=dairy,payble_list=payble_list)
	make_receivable_payment(data=data,row_data=row_data,filters=filters,company=dairy,recv_list=recv_list)
	make_manual_payment(data=data,row_data=row_data,filters=filters,company=dairy,payble_list=payble_list)
	make_payment_log(data=data,filters=filters)
	# calculate_percentage(filters=filters)


def make_payment_log(**kwargs):

	amt = 0.0
	amt_ = 0.0

	amt_ = flt(kwargs.get('data').get('set_amt'))+flt(kwargs.get('data').get('set_amt_manual')) if kwargs.get('data').get('set_amt_manual') else flt(kwargs.get('data').get('set_amt') )
	logs = frappe.db.sql_list("""select name from `tabVLCC Payment Log` where cycle = %s""",(kwargs.get('filters').get('cycle')))

	for log in logs:
		l = frappe.get_doc("VLCC Payment Log",log)
		payble_amt = flt(l.settled_amount)+flt(l.set_amt_manual) if l.set_amt_manual else flt(l.settled_amount)
		amt += payble_amt

	total_paid = amt + amt_

	try:
		log_doc = frappe.new_doc("VLCC Payment Log")
		log_doc.total_pay = set_payble_amt(kwargs.get('filters'))
		log_doc.payble = kwargs.get('data').get('payble')
		log_doc.receivable = kwargs.get('data').get('receivable') 
		log_doc.settled_amount = kwargs.get('data').get('set_amt') 
		log_doc.set_amt_manual = kwargs.get('data').get('set_amt_manual') 
		log_doc.start_date = kwargs.get('filters').get('start_date') 
		log_doc.end_date = kwargs.get('filters').get('end_date') 
		log_doc.cycle = kwargs.get('filters').get('cycle')
		log_doc.month = kwargs.get('filters').get('cycle').split("-")[1]
		log_doc.vlcc = kwargs.get('filters').get('vlcc')
		log_doc.set_per = (total_paid/log_doc.total_pay) * 100
		log_doc.flags.ignore_permissions = True
		log_doc.save()
	except Exception,e: 
		utils.make_dairy_log(title="ZeroDivisionError-Dairy",method="set_percentage", status="Error",
					 message=e, traceback=frappe.get_traceback())

def calculate_percentage(**kwargs):

	amt = 0.0

	logs = frappe.db.sql_list("""select name from `tabVLCC Payment Log` where cycle = %s""",(kwargs.get('filters').get('cycle')))

	for log in logs:
		l = frappe.get_doc("VLCC Payment Log",log)
		payble_amt = flt(l.settled_amount)+flt(l.set_amt_manual) if l.set_amt_manual else flt(l.settled_amount)
		amt += payble_amt

	try:
		date_doc = frappe.get_doc("Cyclewise Date Computation",kwargs.get('filters').get('cycle'))
		date_doc.set_per = (amt/date_doc.amount) * 100
		date_doc.outstanding_amount = date_doc.amount - amt
		date_doc.flags.ignore_permissions = True
		date_doc.save()
	except Exception,e: 
		utils.make_dairy_log(title="ZeroDivisionError-Dairy",method="set_percentage", status="Error",
					 message=e, traceback=frappe.get_traceback())


def set_payble_amt(filters):

	dairy = frappe.db.get_value("Company",{"is_dairy":1},'name')

	credit = frappe.db.sql("""select sum(g.credit) as credit
			from 
				`tabGL Entry` g,`tabPurchase Invoice` p 
			where 
				g.party = %s and g.against_voucher_type in ('Purchase Invoice') 
				and (g.party is not null and g.party != '') and 
				g.docstatus < 2 and p.name = g.voucher_no and g.company = %s 
				and p.posting_date between %s and %s 
				group by g.against_voucher, 
				g.party having credit > 0""",(filters.get('vlcc'),dairy,filters.get('start_date'),
				filters.get('end_date')),as_dict=1)

	credit_list = [i.get('credit') for i in credit]
	return sum(credit_list)
	# date_doc = frappe.get_doc("Cyclewise Date Computation",kwargs.get('filters').get('cycle'))
	# date_doc.amount = sum(credit_list)
	# date_doc.flags.ignore_permissions = True
	# date_doc.save()


def make_payble_payment(**kwargs):

	party_account = get_party_account("Supplier", kwargs.get('filters').get('vlcc'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt'):
		make_payment_entry(payment_type='Pay',args=kwargs,party_type='Supplier',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,ref_no="Auto Payble Settlement")
	
def make_receivable_payment(**kwargs):

	party_account = get_party_account("Customer", kwargs.get('filters').get('vlcc'), kwargs.get('company'))
	default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(kwargs.get('company'), "Cash")
	party_account_currency = get_account_currency(party_account)

	if kwargs.get('data').get('set_amt'):
		make_payment_entry(payment_type='Receive',args=kwargs,party_type='Customer',bank=default_bank_cash_account,
					party_account=party_account,party_account_currency=party_account_currency,ref_no="Auto Receivable Settlement")

def make_manual_payment(**kwargs):

	party_account = get_party_account("Supplier", kwargs.get('filters').get('vlcc'), kwargs.get('company'))
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

	count = frappe.db.sql("""select count(1) as count from `tabVLCC Payment Log` where vlcc = %s and 
			set_per between 90 and 99""",(filters.get('vlcc')),as_dict=1,debug=1)

	if count:
		limit_count = int(count[0].get('count')) + 1 

		return frappe.db.sql("""select c.name,CONCAT(iFnull(max(round(l.set_per,2)),0),' %') as set_per,l.vlcc 
					from 
						`tabCyclewise Date Computation` as c
		 			left join 
		 				(select l1.vlcc, l1.cycle,max(l1.set_per) as set_per 
		 				from 
		 					`tabVLCC Payment Log` l1 
		 				group by l1.vlcc, l1.cycle) as l on c.name = l.cycle 
		 				where 
		 				(l.vlcc = '{0}' or l.vlcc is NULL) and 
		 				(l.set_per<100 or l.set_per is NULL) and 
					c.end_date < curdate() 
					order by c.end_date limit {1}""".
					format(filters.get('vlcc'),limit_count),as_list=True,debug=1)
	return []