# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
from frappe.utils import money_in_words
from dairy_erp.api_utils import make_mobile_log
import requests
import json
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
from erpnext.stock.stock_balance import get_balance_qty_from_sle
import re, urllib, datetime, math, time
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
from frappe import _
from erpnext.accounts.doctype.payment_request.payment_request import make_payment_entry

# Sid Customization

class LocalSale(Document):
	def validate(self):
		# self.total_weight()
		self.check_effective_credit()
		# self.get_in_words()

	def get_in_words(self):
		self.base_in_words = money_in_words(self.grand_total,self.currency)
		self.in_words = money_in_words(self.grand_total,self.currency)

	def additional_discount(self):
		if self.additional_discount_percentage:
			additional_discount = 0
			for i in self.items:
				additional_discount += (i.get('amount')* self.additional_discount_percentage)/100
				self.discount_amount = additional_discount

	def check_effective_credit(self):
		effective_credit = self.effective_credit
		if self.local_customer_or_farmer == 'Vlcc Local Customer':
			if self.customer == None:
				frappe.throw(_("Please select Customer"))
		if self.local_customer_or_farmer == 'Farmer':
			if self.farmer and effective_credit == 0:
				frappe.throw(_("Cannot create <b>'Local Sale'</b> if <b>'Effective Credit'</b> is 0.0"))
			elif self.farmer == None:
				frappe.throw(_("Please select Farmer"))
			elif self.farmer and effective_credit < self.total:
				frappe.throw(_("Cannot make <b>'Local Sale'</b> if <b>'Effective Credit'</b> is less than <b>Total</b>"))

	def total_weight(self):
		total_ = 0
		for i in self.items:
			print type(i.get('amount')),i.get('amount')
			total_ += i.get('amount')
		self.total = total

	def on_submit(self):
		self.create_delivery_note_for_vlcc()

	def create_delivery_note_for_vlcc(self):
		if self.local_customer_or_farmer == "Vlcc Local Customer":
			customer = self.customer

			# print "\n Delivery Note Object {0} \n".format(self.__dict__)
			# print "\n**********  Grand Total:{0} \n Total Taxes:{1}  ************\n".format(self.grand_total,self.total_taxes_and_charges)

			delivry_obj = frappe.new_doc("Delivery Note")
			delivry_obj.customer = customer
			delivry_obj.grand_total = self.grand_total + self.total_taxes_and_charges
			delivry_obj.total_taxes_and_charges = self.total_taxes_and_charges
			delivry_obj.company = frappe.db.get_value("User",frappe.session.user,'company')
			cost_center = frappe.db.get_value("Company",delivry_obj.company,'cost_center')
			for row in self.items:
				delivry_obj.append("items",
					{
						"item_code": row.item_code,
						"item_name": row.item_name,
						"description": row.description,
						"uom": "Litre",
						"qty": row.get('qty'),
						"rate": row.get('rate'),
						"amount": row.get('amount'),
						"warehouse": row.get("warehouse"),
						"cost_center": cost_center
					})
			delivry_obj.flags.ignore_permissions = True
			delivry_obj.submit()
			si_obj = make_sales_invoice(delivry_obj.name)
			si_obj.flags.ignore_permissions = True
			si_obj.submit()
			si_obj.grand_total = delivry_obj.grand_total + delivry_obj.total_taxes_and_charges
			si_obj.total_taxes_and_charges = delivry_obj.total_taxes_and_charges
			make_payment_on_si(si_obj)
			frappe.msgprint(_("Delivery Note :'{0}' Created".format("<a href='#Form/Delivery Note/{0}'>{0}</a>".format(delivry_obj.name))))
			frappe.msgprint(_("Sales Invoice :'{0}' Created".format("<a href='#Form/Sales Invoice/{0}'>{0}</a>".format(si_obj.name))))
		
		elif self.local_customer_or_farmer == "Farmer":
			customer = self.farmer_name
			
			delivry_obj = frappe.new_doc("Delivery Note")
			delivry_obj.customer = customer
			# delivry_obj.grand_total = self.grand_total
			# delivry_obj.total_taxes_and_charges = self.total_taxes_and_charges
			delivry_obj.company = frappe.db.get_value("User",frappe.session.user,'company')
			cost_center = frappe.db.get_value("Company",delivry_obj.company,'cost_center')
			for row in self.items:
				delivry_obj.append("items",
					{
						"item_code": row.item_code,
						"item_name": row.item_name,
						"description": row.description,
						"uom": "Litre",
						"qty": row.get('qty'),
						"rate": row.get('rate'),
						"amount": row.get('amount'),
						"warehouse": row.get("warehouse"),
						"cost_center": cost_center
					})
			delivry_obj.flags.ignore_permissions = True
			delivry_obj.submit()
			si_obj = make_sales_invoice(delivry_obj.name)
			si_obj.flags.ignore_permissions = True
			si_obj.submit()
			if self.cash:
				make_payment_on_si(si_obj)
			si_obj.grand_total = delivry_obj.grand_total + delivry_obj.total_taxes_and_charges
			si_obj.total_taxes_and_charges = delivry_obj.total_taxes_and_charges
			frappe.msgprint(_("Delivery Note :'{0}' Created".format("<a href='#Form/Delivery Note/{0}'>{0}</a>".format(delivry_obj.name))))
			frappe.msgprint(_("Sales Invoice :'{0}' Created".format("<a href='#Form/Sales Invoice/{0}'>{0}</a>".format(si_obj.name))))


@frappe.whitelist()
def make_payment_on_si(si_doc):
	si_payment = frappe.new_doc("Payment Entry")
	si_payment.paid_to = frappe.db.get_value("Account",{"company":si_doc.company,"account_type":'Cash'},"name")
	si_payment.posting_date = si_doc.posting_date
	si_payment.company = si_doc.company
	si_payment.mode_of_payment = "Cash"
	si_payment.payment_type = "Receive"
	si_payment.party_type = "Customer"
	si_payment.party_name = si_doc.customer
	si_payment.party = si_doc.customer

	for row in si_doc.items:
		si_payment.append("references",
			{
				"reference_doctype": si_doc.doctype,
				"total_amount": si_doc.grand_total + si_doc.total_taxes_and_charges,
				"reference_name": si_doc.name,
				"outstanding_amount": si_doc.outstanding_amount,
				"allocated_amount": si_doc.grand_total,
				"due_date": si_doc.due_date
			})

	si_payment.paid_amount = si_doc.grand_total + si_doc.total_taxes_and_charges
	si_payment.received_amount = si_doc.grand_total
	si_payment.party_balance = si_doc.grand_total
	si_payment.outstanding_amount = 0
	si_payment.flags.ignore_permissions = True
	si_payment.flags.ignore_mandatory = True
	si_payment.submit()
	frappe.msgprint(_("Payment Entry : {0} Created!!!".format("<a href='#Form/Payment Entry/{0}'>{0}</a>".format(si_payment.name))))


@frappe.whitelist()
def get_price_list_rate(item):
	if item:
		rate = frappe.db.sql("""select price_list_rate from `tabItem Price`
						 		where item_name = '{0}' and 
						 		price_list ='Standard Selling'""".format(item),as_list=1)
		if rate:
			return rate[0][0]
		else:
			return 0

@frappe.whitelist()
def fetch_taxes(tax):
	# return frappe.db.sql("""select """)
	taxes = frappe.get_doc("Sales Taxes and Charges Template",tax)
	return taxes

@frappe.whitelist()
def get_milk_qty_local():
	company = frappe.db.get_value("User",frappe.session.user,'company')
	if item:
		rate = frappe.db.sql("""select price_list_rate from `tabItem Price`
						 		where item_name = '{0}' and 
						 		price_list ='Standard Selling'""".format(item),as_list=1)
		if rate:
			return rate[0][0]
		else:
			return 0

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
def get_vlcc_warehouse():
	warehouse = frappe.db.get_value("Village Level Collection Centre", {"email_id": frappe.session.user}, 'warehouse')
	return warehouse

@frappe.whitelist()
def get_effective_credit(customer):
	# print "---------------customer----------------",customer
	company = frappe.db.get_value("User", frappe.session.user, "company")
	purchase = frappe.db.get_value("Purchase Invoice", {"title":customer,"company":company}, "sum(grand_total)")
	sales = frappe.db.get_value("Sales Invoice", {"title":customer,"company":company}, "sum(grand_total)")
	# print "----------------------sales",sales
	# print "======================purchase",purchase
	# purchase_total = frappe.db.sql("""select name,sum(grand_total) as purchase_total from `tabPurchase Invoice` where title = '{0}' and company = '{1}'""".format(customer,company),as_dict=True) 
	# sales_total = frappe.db.sql("""select name,sum(grand_total) as sales_total from `tabSales Invoice` where title = '{0}' and company = '{1}'""".format(customer,company),as_dict=True)
	
	if purchase == None:
		eff_amt = 0.0
		return eff_amt

	if purchase and sales:
		eff_amt = purchase - sales
		return eff_amt

	elif purchase == None and sales:
		# print "____________________ {0} _______________".format(sales)
		eff_amt = 0.0
		return eff_amt
	elif purchase and sales == None:
		# print "____________________ {0} _______________".format(purchase)
		eff_amt = purchase
		return eff_amt
	else:
		eff_amt = 0.0
		return eff_amt
