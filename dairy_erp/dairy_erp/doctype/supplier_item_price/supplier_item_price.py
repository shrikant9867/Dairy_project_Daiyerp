# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class SupplierItemPrice(Document):
	def after_insert(self):
		self.create_price_list()

	def create_price_list(self):
		if self.type_ == "Dairy":
			if self.party_type == "Vlcc" and not frappe.db.exists('Price List', self.party_type+"-"+"Selling"):
				price_doc = frappe.new_doc("Price List")
				price_doc.price_list_name = self.type_+"-"+"Selling"
				price_doc.currency = "INR"
				price_doc.selling = 1
				price_doc.flags.ignore_permissions = True
				price_doc.save()
				self.create_item_price(price_doc.name)

			if self.party_type == "Vlcc" and not frappe.db.exists('Price List', self.party_type+"-"+"Buying"):
				price_doc = frappe.new_doc("Price List")
				price_doc.price_list_name = self.party_type+"-"+"Buying"
				price_doc.currency = "INR"
				price_doc.buying = 1
				price_doc.flags.ignore_permissions = True
				price_doc.save()
				self.create_item_price(price_doc.name)


			if self.party_type == "Local Supplier" and not frappe.db.exists('Price List', self.supplier+"-"+"Buying"):
				price_doc = frappe.new_doc("Price List")
				price_doc.price_list_name = self.supplier+"-"+"Buying"
				price_doc.currency = "INR"
				price_doc.buying = 1
				price_doc.supplier = self.supplier
				price_doc.flags.ignore_permissions = True
				price_doc.save()
				self.create_item_price(price_doc.name)


		if self.type_ == "Vlcc":
			self.price_list_vlcc()

	def price_list_vlcc(self):
		if self.party_type_vlcc == "Local Supplier" and not frappe.db.exists('Price List',self.party_type_vlcc+"-"+self.type_+"-"+"Buying") and not self.vlcc and not self.supplier:
			price_doc = frappe.new_doc("Price List")
			price_doc.price_list_name = self.party_type_vlcc+"-"+self.type_+"-"+"Buying"
			price_doc.currency = "INR"
			price_doc.buying = 1
			price_doc.default = 1
			price_doc.flags.ignore_permissions = True
			price_doc.save()
			self.create_item_price(price_doc.name)


		if self.party_type_vlcc == "Local Supplier" and not frappe.db.exists('Price List',self.party_type_vlcc+"-"+self.supplier+"-"+"Buying") and  self.vlcc and self.supplier:
			price_doc = frappe.new_doc("Price List")
			price_doc.price_list_name = self.party_type_vlcc+"-"+self.supplier+"-"+"Buying"
			price_doc.currency = "INR"
			price_doc.buying = 1
			price_doc.flags.ignore_permissions = True
			price_doc.save()
			self.create_item_price(price_doc.name)

	def create_item_price(self, name):
		for row in self.price_template_tab:
			item_price = frappe.new_doc("Item Price")
			item_price.price_list = name
			item_price.item_code = row.item
			item_price.price_list_rate = row.price
			item_price.flags.ignore_permissions = True
			item_price.save()