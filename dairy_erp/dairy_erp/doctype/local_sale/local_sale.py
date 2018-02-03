# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
from frappe import _
from dairy_erp.api_utils import make_mobile_log
import requests
import json
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
from erpnext.stock.stock_balance import get_balance_qty_from_sle
import re, urllib, datetime, math, time
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
from frappe import _

# Sid Customization

class LocalSale(Document):
	def validate(self):
		self.total_weight()
		self.check_effective_credit()
		# self.additional_discount()
		# self.rounded_total()

	def additional_discount(self):
		print "________________ {0} ______________", self.additional_discount_percentage
		if self.additional_discount_percentage:
			additional_discount = 0
			for i in self.items:
				additional_discount += (i.get('amount')* self.additional_discount_percentage)/100
				self.discount_amount = additional_discount

	def check_effective_credit(self):
		print "________________ {0} and {1} and {2}______________".format(self.effective_credit,self.customer,self.farmer)
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
		pass
		# total = 0
		# for i in self.items:
		# 	print "##############",type(i.get('amount'))
		# 	total += i.get('amount')
		# self.total = total

	def on_submit(self):
		self.create_delivery_note_for_vlcc()

	def create_delivery_note_for_vlcc(self):
		if self.local_customer_or_farmer == "Vlcc Local Customer":
			customer = self.customer
		elif self.local_customer_or_farmer == "Farmer":
			customer = self.farmer_name

		delivry_obj = frappe.new_doc("Delivery Note")
		delivry_obj.customer = customer
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
		frappe.msgprint(_("Delivery Note: {0} Created!!! \n Sales Invoice: {1} Created!!!".format(delivry_obj.name,si_obj.name)))

	# def create_sale_invoice_ls(self):
	# 	print "____________",self.name
	# 	try:
	# 		si_obj = frappe.new_doc("Sales Invoice")
	# 		si_obj.customer = self.customer
	# 		si_obj.company = frappe.db.get_value("User",frappe.session.user,'company')
	# 		si_obj_cost_center = frappe.db.get_value("Company",si_obj.company,'cost_center')
	# 		si_obj.due_date = self.posting_time
	# 		for row in self.items:
	# 			si_obj.append("items",
	# 			{
	# 				"item_code": row.get('item_code'),
	# 				"item_name": row.get('item_code'),
	# 				"description": row.get('item_code'),
	# 				"uom": "Litre",
	# 				"qty": row.get('qty'),
	# 				"rate": row.get('rate'),
	# 				"amount": row.get('amount'),
	# 				"warehouse": row.get("warehouse"),
	# 				"cost_center": si_obj_cost_center
	# 			})
	# 		si_obj.flags.ignore_permissions = True
	# 		# si_obj.service_note = self.name
	# 		si_obj.submit()
	# 		frappe.msgprint(_("Sales Invoice: {0} Created!!!".format(self.name))
		# except Exception,e:
		# 	make_mobile_log(title="Sync failed for Data push",method="get_items", status="Error",
		# 	data = "", message=e, traceback=frappe.get_traceback())

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
