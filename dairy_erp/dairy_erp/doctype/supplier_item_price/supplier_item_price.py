# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class SupplierItemPrice(Document):
	def validate(self):
		if self.is_new() and frappe.db.sql("select name from `tabSupplier Item Price` where supplier = '{0}' and vlcc = '{1}'".format(self.supplier,self.vlcc)):
			# frappe.throw(_("Only one Item price allowed"))
			pass
	

	def after_insert(self):
		"""table manipulation price list and item price"""
		self.create_price_list_()

	def create_price_list_(self):
		if self.party_type == "Supplier":
			self.create_price_list_supplier()
		if self.type_ == "Branch Office" and self.party_type == "Customer":
			dairy_comp = frappe.db.get_value("Company",{'is_dairy':1}, 'name')
			price_list = frappe.new_doc("Price List")
			price_list.price_list_name = self.customer+"-"+"selling"+"-"+self.branch_office
			price_list.company = dairy_comp
			price_list.currency = "INR"
			price_list.selling = 1
			price_list.flags.ignore_permissions = True
			price_list.save()
			self.create_item_price(price_list)

			price_list_ = frappe.new_doc("Price List")
			price_list_.price_list_name = self.branch_office+"-"+"buying"+"-"+self.customer
			price_list_.company = self.customer
			price_list_.currency = "INR"
			price_list_.buying = 1
			price_list_.flags.ignore_permissions = True
			price_list_.save()
			self.create_item_price(price_list_)


	def create_item_price(self, pr_obj):
		for row in self.price_template_tab:
			item_price = frappe.new_doc("Item Price")
			item_price.price_list = pr_obj.name
			item_price.item_code = row.item
			item_price.price_list_rate = row.price
			item_price.flags.ignore_permissions = True
			item_price.save()


	def create_price_list_supplier(self):
		dairy_comp = frappe.db.get_value("Company",{'is_dairy':1}, 'name')
		if self.type_ == "Vlcc" and self.party_type == "Supplier":
			price_list = frappe.new_doc("Price List")
			price_list.price_list_name = self.supplier+"-"+"buying"
			price_list.company = self.vlcc
			price_list.currency = "INR"
			price_list.buying = 1
			price_list.flags.ignore_permissions = True
			price_list.save()
			self.create_item_price(price_list)

		if self.type_ == "Branch Office" and self.party_type == "Supplier":
			price_list = frappe.new_doc("Price List")
			price_list.price_list_name = self.supplier+"-"+"buying"
			price_list.company = dairy_comp
			price_list.currency = "INR"
			price_list.buying = 1
			price_list.flags.ignore_permissions = True
			price_list.save()
			self.create_item_price(price_list)