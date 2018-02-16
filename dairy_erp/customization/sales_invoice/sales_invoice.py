# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.stock_balance import get_balance_qty_from_sle
from frappe.utils import flt, now_datetime, cstr



@frappe.whitelist()
def get_local_customer(company):
	data = fetch_balance_qty()
	data.update({'customer':frappe.db.get_value("Customer",company+"-"+"Local",'name')})
	return data


@frappe.whitelist()
def get_farmer_config(farmer= None):
	data = fetch_balance_qty()
	eff_credit = get_effective_credit(frappe.db.get_value("Farmer",farmer,'full_name'))
	data.update({'eff_credit': eff_credit, 'customer': frappe.db.get_value("Farmer",farmer,'full_name')})
	return data


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

def get_effective_credit(customer):
	# SIdhant code for effective credit
	company = frappe.db.get_value("User", frappe.session.user, "company")
	purchase = frappe.db.sql("""select sum(grand_total) as pur_amnt from `tabPurchase Invoice` where company = '{0}' and supplier = '{1}' and status not in ('Paid')""".format(company, customer),as_dict=1)
	sales = frappe.db.sql("""select sum(grand_total) as si_amnt from `tabSales Invoice` where company = '{0}' and customer = '{1}' and status not in ('Paid')""".format(company, customer),as_dict=1)
	
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



def validate_local_sale(doc, method):
	if doc.local_sale:
		doc.customer = frappe.db.get_value('Farmer',doc.farmer,'full_name')
		warehouse = frappe.db.get_value('Village Level Collection Centre',doc.company,'warehouse')
		doc.debit_to = frappe.db.get_value("Company",doc.company, 'default_receivable_account')
		print "@@@@@@@@@@@@@@@",doc.debit_to
		for row in doc.items:
			row.warehouse = warehouse
			row.cost_center = frappe.db.get_value('Company',doc.company,'cost_center')
	# 	frappe.throw(_("Not Permitted Effective Credit"))
	# if doc.local_sale and not doc.update_stock:
	# 	frappe.throw(_("update the stock"))

def payment_entry(doc, method):
	if doc.local_sale and doc.customer_or_farmer == "Farmer" and doc.effective_credit <= 0 :
		frappe.throw(_("Not Permitted"))
	if doc.local_sale and not doc.update_stock:
		frappe.throw(_("update the stock"))
	if doc.local_sale and doc.customer_or_farmer == "Vlcc Local Customer":
		make_payment_entry(doc)
	if doc.local_sale and doc.customer_or_farmer == "Farmer" and doc.cash_payment:
		make_payment_entry(doc)



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
			"allocated_amount": si_doc.grand_total,
			"due_date": si_doc.due_date
		})

	si_payment.paid_amount = si_payment.references[0].allocated_amount
	si_payment.received_amount = si_payment.paid_amount
	# si_payment.party_balance = si_doc.grand_total
	si_payment.outstanding_amount = 0
	si_payment.flags.ignore_permissions = True
	si_payment.flags.ignore_mandatory = True
	si_payment.submit()
	frappe.msgprint(_("Payment Entry : {0} Created!!!".format("<a href='#Form/Payment Entry/{0}'>{0}</a>".format(si_payment.name))))


@frappe.whitelist()
def get_wrhous():
	warehouse = frappe.db.get_value("Village Level Collection Centre", {"email_id": frappe.session.user}, 'warehouse')
	return warehouse