# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

class Farmer(Document):
	def on_submit(self):
		"""create customer & supplier for A/C head"""
		
		self.create_supplier()
		self.create_customer()
	
	def create_supplier(self):
		supl_doc = frappe.new_doc("Supplier")
		supl_doc.supplier_name = self.full_name
		supl_doc.supplier_type = "Farmer"
		supl_doc.company = self.vlcc_name
		supl_doc.farmer = self.name
		supl_doc.append("accounts",
			{
			"company": self.vlcc_name,
			"account": frappe.db.get_value("Company",self.vlcc_name, "default_payable_account")
			})
		supl_doc.farmer = self.name
		supl_doc.insert()

	def create_customer(self):
		custmer_doc = frappe.new_doc("Customer")
		custmer_doc.customer_name = self.full_name
		custmer_doc.customer_group = "Farmer"
		custmer_doc.company = self.vlcc_name
		custmer_doc.farmer = self.name
		custmer_doc.append("accounts",
			{
			"company": self.vlcc_name,
			"account": frappe.db.get_value("Company",self.vlcc_name, "default_receivable_account")
			})
		custmer_doc.farmer = self.name
		custmer_doc.insert()

	def validate(self):
		self.validate_eff_credit_percent()
		if len(self.farmer_id) != 4:
			frappe.throw(_("Only <b>4</b> Digits Farmer ID Allowed"))

	def validate_eff_credit_percent(self):
		# eff-credit % must be between 0-99
		eff_credit_percent = flt(self.percent_effective_credit)
		if not self.ignore_effective_credit_percent and (eff_credit_percent < 0 or eff_credit_percent > 99):
			frappe.throw(_("Percent Of Effective Credit must be between 0 to 99"))
