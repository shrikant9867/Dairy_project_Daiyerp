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

# Sid Customization

class LocalSale(Document):
	def validate(self):
		self.total_weight()

	def total_weight(self):
		total = 0
		for i in self.items:
			total += i.get('amount')
		self.total = total

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
		# self.create_sale_invoice_ls()
		print "========================="

	def create_sale_invoice_ls(self):
		print "____________",self.name
		try:
			si_obj = frappe.new_doc("Sales Invoice")
			si_obj.customer = self.customer
			si_obj.company = frappe.db.get_value("User",frappe.session.user,'company')
			si_obj_cost_center = frappe.db.get_value("Company",si_obj.company,'cost_center')
			si_obj.due_date = self.posting_time
			for row in self.items:
				si_obj.append("items",
				{
					"item_code": row.get('item_code'),
					"item_name": row.get('item_code'),
					"description": row.get('item_code'),
					"uom": "Litre",
					"qty": row.get('qty'),
					"rate": row.get('rate'),
					"amount": row.get('amount'),
					"warehouse": row.get("warehouse"),
					"cost_center": si_obj_cost_center
				})
			si_obj.flags.ignore_permissions = True
			# si_obj.service_note = self.name
			si_obj.submit()
		except Exception,e:
			make_mobile_log(title="Sync failed for Data push",method="get_items", status="Error",
			data = "", message=e, traceback=frappe.get_traceback())

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
