# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.stock_balance import get_balance_qty_from_sle
from frappe.utils import flt, now_datetime, cstr,has_common

@frappe.whitelist()
def get_local_customer(company):
	data = fetch_balance_qty()
	data.update({'customer':frappe.db.get_value("Customer",company+"-"+"Local",'name')})
	return data


@frappe.whitelist()
def get_farmer_config(farmer, invoice):
	data = fetch_balance_qty()
	farmer_doc = frappe.get_doc("Farmer",farmer)
	eff_credit = get_effective_credit(farmer_doc.full_name, invoice)
	percent_eff_credit = eff_credit * (farmer_doc.percent_effective_credit/100) if farmer_doc.percent_effective_credit else eff_credit
	data.update({'eff_credit': eff_credit, "percent_eff_credit":percent_eff_credit,'customer': frappe.db.get_value("Farmer",farmer,'full_name')})
	return data


@frappe.whitelist()
def fetch_balance_qty():
	row_ =""
	items_dict = {}
	item = ["COW Milk","BUFFALO Milk"]
	company = frappe.db.get_value("User",frappe.session.user,"company")
	warehouse = frappe.db.get_value("Village Level Collection Centre",company,"warehouse")
	print "warehouse",get_balance_qty_from_sle("COW Milk",warehouse)
	for row in item:
		if row == "COW Milk":
			row_ = "cow_milk"
		elif row == "BUFFALO Milk":
			row_ = "buff_milk"
		items_dict.update({row_ : get_balance_qty_from_sle(row,warehouse)})

	return items_dict

@frappe.whitelist()
def get_effective_credit(customer, invoice=None):
	# SIdhant code for effective credit
	company = frappe.db.get_value("User", frappe.session.user, "company")
	purchase = frappe.db.sql("""select sum(outstanding_amount) as pur_amnt from `tabPurchase Invoice` where company = '{0}' and supplier = '{1}' and status not in ('Paid') and docstatus = '1' and name <> '{2}'""".format(company, customer, invoice),as_dict=1)
	sales = frappe.db.sql("""select sum(outstanding_amount) as si_amnt from `tabSales Invoice` where company = '{0}' and customer = '{1}' and status not in ('Paid') and docstatus = '1' and name <> '{2}'""".format(company, customer, invoice),as_dict=1)
	if purchase[0].get('pur_amnt') == None:
		eff_amt = 0.0
		return round(eff_amt,2)

	if purchase[0].get('pur_amnt') and sales[0].get('si_amnt'):
		eff_amt = flt(purchase[0].get('pur_amnt')) - flt(sales[0].get('si_amnt'))
		return round(eff_amt,2)

	elif purchase[0].get('pur_amnt') == None and sales[0].get('si_amnt'):
		eff_amt = 0.0
		return round(eff_amt,2)
	
	elif purchase[0].get('pur_amnt') and sales[0].get('si_amnt') == None:
		eff_amt = flt(purchase[0].get('pur_amnt'))
		return round(eff_amt,2)
	
	else:
		eff_amt = 0.0
		return round(eff_amt,2)

@frappe.whitelist()
def validate_local_sale(doc, method):
	if doc.effective_credit <= 0.000 and doc.service_note == 1:
		frappe.throw(_("Service Note cannot be created if <b>'Effective Credit' </b> is zero"))
	elif (doc.grand_total > doc.effective_credit and doc.service_note and not doc.by_cash) \
	or (doc.service_note and doc.by_credit and doc.by_credit > doc.grand_total ):
		frappe.throw(_("Service note cannot be created if Outstanding amount  greater than Effective Credit "))

	if doc.local_sale:
		if doc.customer_or_farmer == "Farmer":
			doc.customer = frappe.db.get_value('Farmer',doc.farmer,'full_name')
		elif doc.customer_or_farmer == "Vlcc Local Customer":
			doc.customer = frappe.db.get_value("Customer",doc.company+"-"+"Local",'name')
		warehouse = frappe.db.get_value('Village Level Collection Centre',doc.company,'warehouse')
		doc.debit_to = frappe.db.get_value("Company",doc.company, 'default_receivable_account')
		for row in doc.items:
			row.warehouse = warehouse
			row.cost_center = frappe.db.get_value('Company',doc.company,'cost_center')

@frappe.whitelist()
def payment_entry(doc, method):
	input_ = doc.effective_credit or 0
	if doc.local_sale and doc.customer_or_farmer == "Farmer" and input_ == 0:
		frappe.throw(_("Cannot create local sale, If <b>Effective Credit</b>  zero, use Multimode Payment option for cash "))
	if doc.local_sale and doc.customer_or_farmer == "Farmer" and doc.by_credit > input_ and doc.by_credit and doc.multimode_payment:
		frappe.throw(_("<b>By Credit - {0}</b> Amount must be less than OR equal to <b>Effective Credit</b>.{1}".format(doc.by_credit, input_)))
	if (doc.local_sale or doc.service_note) and doc.customer_or_farmer == "Farmer" and not doc.multimode_payment and doc.grand_total > input_:
		frappe.throw(_("Outstanding amount should not be greater than Effective Credit"))
	if (doc.local_sale or doc.service_note) and doc.customer_or_farmer == "Farmer" and doc.by_credit and doc.by_credit > input_:
		frappe.throw(_("By Credit Amount must be less than or equal to Effective Credit."))
	if doc.local_sale and not doc.update_stock:
		frappe.throw(_("Please set <b>Update Stock</b> checked"))
	if (doc.local_sale or doc.service_note) and has_common(["Farmer", "Vlcc Local Customer"], doc.customer_or_farmer)\
	and (doc.by_cash or not doc.multimode_payment):
		make_payment_entry(doc)

@frappe.whitelist()
def make_payment_entry(si_doc):
	si_payment = frappe.new_doc("Payment Entry")
	si_payment.paid_to = frappe.db.get_value("Account",{"company":si_doc.company,"account_type":'Cash'},"name")
	si_payment.posting_date = si_doc.posting_date
	si_payment.company = si_doc.company
	si_payment.mode_of_payment = "Cash"
	si_payment.payment_type = "Receive"
	si_payment.party_type = "Customer"
	si_payment.party_name = si_doc.customer
	si_payment.party = si_doc.customer

	si_payment.append("references",
		{
			"reference_doctype": si_doc.doctype,
			"reference_name": si_doc.name,
			"allocated_amount": si_doc.by_cash or si_doc.grand_total,
			"due_date": si_doc.due_date
		})

	si_payment.paid_amount = si_payment.references[0].allocated_amount
	si_payment.received_amount = si_payment.paid_amount
	# si_payment.party_balance = si_doc.grand_total
	si_payment.outstanding_amount = 0
	si_payment.flags.ignore_permissions = True
	si_payment.flags.ignore_credit_validation = True
	si_payment.flags.ignore_mandatory = True
	si_payment.submit()
	frappe.msgprint(_("Payment Entry : {0} Created!!!".format("<a href='#Form/Payment Entry/{0}'>{0}</a>".format(si_payment.name))))


@frappe.whitelist()
def get_wrhous():
	warehouse = frappe.db.get_value("Village Level Collection Centre", {"email_id": frappe.session.user}, 'warehouse')
	return warehouse


@frappe.whitelist()
def get_service_note_item(doctype, txt, searchfield, start, page_len, filters):
	print "\n\nfilters",filters
	if filters.service_note:
		query_item = frappe.db.sql(""" select item_code from `tabItem` where item_group in ('Medicines', 'Services')""")
		return query_item
	else:
		query_item = frappe.db.sql("""select item_code from `tabItem`""")
		return query_item

@frappe.whitelist()
def get_servicenote_item():
	query_item = frappe.db.sql(""" select item_code from `tabItem` where item_group in ('Medicines', 'Services')""",as_list=1)
	return query_item

@frappe.whitelist()
def get_account_invoice():
	user = frappe.session.user
	user_data = frappe.db.get_value("User", user, ["operator_type", "branch_office"], as_dict=True)
	if user_data.get('operator_type') == "Camp Office" and user_data.get('branch_office'):
		camp_office_data = frappe.db.get_value("Address", user_data.get('branch_office'),
			["income_account", "expense_account", "stock_account", "warehouse"], as_dict=True)
		return camp_office_data
	return {}

def set_camp_office_accounts(doc, method=None):
	# set income/expense account in item grid & also as remarks to filter it as account in reports.
	accounts = get_account_invoice()
	if accounts:
		for i in doc.items:
			if doc.doctype == "Purchase Invoice" and accounts.get('expense_account'):
				i.expense_account = accounts.get('expense_account')
			elif doc.doctype == "Sales Invoice" and accounts.get('income_account'):
				i.income_account = accounts.get('income_account')
				i.warehouse = accounts.get('warehouse')
		account = accounts.get('expense_account') if doc.doctype == "Purchase Invoice" else accounts.get('income_account')
		if account and doc.remarks.find("[#"+account+"#]") == -1:
			doc.remarks = doc.remarks + " [#"+account+"#]"