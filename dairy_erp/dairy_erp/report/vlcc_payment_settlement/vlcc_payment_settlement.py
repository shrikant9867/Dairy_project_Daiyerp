# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from erpnext.accounts.doctype.journal_entry.journal_entry \
	import get_average_exchange_rate, get_default_bank_cash_account
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_outstanding_invoices, get_account_currency, get_balance_on
from frappe import _
import json

def execute(filters=None):
	# columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):

	columns = [
		_("") + ":Data:40",_("Posting Date") + ":Date:90", _("Account") + ":Link/Account:200",
		 _("Party Type") + "::80", _("Party") + "::150",
		_("Voucher Type") + "::120", _("Voucher No") + ":Dynamic Link/"+_("Voucher Type")+":160",
		_("Against Voucher Type") + "::120", _("Against Voucher") + ":Dynamic Link/"+_("Against Voucher Type")+":160",
		_("Debit") + ":Float:100", _("Credit") + ":Float:100",
		_("Remarks") + "::400",_("Name") + ":Data:100",
	]

	return columns

def get_data(filters):

	data = frappe.db.sql("""select 'test' as test,posting_date, account, party_type, party,voucher_type, 
						voucher_no, against_voucher_type, against_voucher,
						sum(debit) as debit, sum(credit) as credit,remarks,name
						from `tabGL Entry` where  {0} docstatus < 2 and (party is not null and party != '') group by voucher_type, voucher_no, 
						against_voucher_type, against_voucher, party order by posting_date,party,voucher_type""".format(get_conditions(filters)),filters,as_list=1)

	return data

def get_conditions(filters):

	conditions = ""
	vlcc =  [ '"%s"'%data.get('name') for data in frappe.get_all("Village Level Collection Centre", fields=["name"]) ]

	if filters.get('vlcc'):
		conditions = "party = %(vlcc)s and "

	else : conditions = "party in ({vlcc}) and ".format(vlcc=','.join(vlcc))

	return conditions

@frappe.whitelist()
def get_cycles():

	cycles = frappe.db.sql("""select field,value from `tabSingles` where doctype = 'VLCC Payment Cycle' and field = 'no_of_cycles'""",as_dict=1)
	return cycles

@frappe.whitelist()
def get_payment_amt(row_data):

	row_data = json.loads(row_data)
	payble = 0.0
	receivable = 0.0

	for data in row_data:
		gl_doc = frappe.get_doc("GL Entry",data)

		if gl_doc.voucher_type == "Purchase Invoice":
			payble += gl_doc.credit
		if gl_doc.voucher_type == "Sales Invoice":
			receivable += gl_doc.debit
	
	return {"payble":payble,"receivable":receivable,"set_amt":min(payble,receivable)}

@frappe.whitelist()
def make_payment(data,row_data,filters):
	pass

	# data = json.loads(data)
	# row_data = json.loads(row_data)
	# filters = json.loads(filters)
	# dairy = frappe.db.get_value("Company",{"is_dairy":1},'name')
	# party_account = get_party_account("Supplier", filters.get('vlcc'), dairy)
	# bank = get_default_bank_cash_account(dairy, "Bank")
	# party_account_currency = get_account_currency(party_account)
	# # allocated_amount = abs(filters.get('payble')-filters.get('receivable'))

	# print party_account,"account.......\n\n"
	# print bank,"bank......\n\n"


	# pe = frappe.new_doc("Payment Entry")
	# pe.payment_type = "Pay"
	# pe.company = dairy
	# pe.posting_date = nowdate()
	# # pe.mode_of_payment = doc.get("mode_of_payment")
	# pe.party_type = "Supplier"
	# pe.party = filters.get('vlcc')
	# pe.paid_from = bank.account#party_account if payment_type=="Receive" else bank.account
	# pe.paid_to = party_account 
	# pe.paid_from_account_currency = bank.account_currency
	# pe.paid_to_account_currency = party_account_currency #if payment_type=="Pay" else bank.account_currency
	# pe.paid_amount = filters.get('set_amt')
	# # pe.received_amount = received_amount
	# pe.allocate_payment_amount = 1
	# # pe.letter_head = doc.get("letter_head")

	# for row in row_data:
	# 	gl_doc = frappe.get_doc("GL Entry",row)

	# 	if gl_doc.voucher_type == "Purchase Invoice":
	# 		if filters.get('set_amt') < gl_doc.credit:
	# 			allocated_amount = gl_doc.credit - filters.get('set_amt')

	# 		pe.append("references", {
	# 			"reference_doctype": gl_doc.voucher_type,
	# 			"reference_name": gl_doc.voucher_no,
	# 			# "bill_no": doc.get("bill_no"),
	# 			"due_date":nowdate(),
	# 			"total_amount": grand_total,
	# 			"outstanding_amount": outstanding_amount,
	# 			"allocated_amount": allocated_amount
	# 		})

	# pe.flags.ignore_permissions = True
	# pe.flags.ignore_mandatory = True
	# pe.save()
	# pe.submit()

	

@frappe.whitelist()
def test():
	pass
	# days = frappe.db.sql("""select start_day,end_day from `tabVLCC Payment Child` where parent = 'VLCC Payment Cycle'""",as_dict=1)
	# for row in days:
		# start_date = str(nowdate().split("-")[0]) + "-" +str(nowdate().split("-")[1]) + + str(row.get('start_day'))
	# 	end_date = str(nowdate().split("-")[0]) + str(nowdate().split("-")[1]) + str(row.get('end_day'))
	# 	row.update({"start_date":start_date,"end_date":end_date})

