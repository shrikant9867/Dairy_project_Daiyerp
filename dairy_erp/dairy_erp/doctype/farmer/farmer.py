# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Farmer(Document):
	def after_insert(self):
		"""create customer & supplier for A/C head"""
		
		supl_doc = frappe.new_doc("Supplier")
		supl_doc.supplier_name = self.full_name
		supl_doc.supplier_type = "Distributor"
		supl_doc.company = self.vlcc_name
		supl_doc.append("accounts",
			{
			"company": self.vlcc_name,
			"account": frappe.db.get_value("Company",self.vlcc_name, "default_payable_account")
			})
		supl_doc.insert()

		custmer_doc = frappe.new_doc("Customer")
		custmer_doc.customer_name = self.full_name
		custmer_doc.company = self.vlcc_name
		custmer_doc.append("accounts",
			{
			"company": self.vlcc_name,
			"account": frappe.db.get_value("Company",self.vlcc_name, "default_receivable_account")
			})
		custmer_doc.insert()

		
