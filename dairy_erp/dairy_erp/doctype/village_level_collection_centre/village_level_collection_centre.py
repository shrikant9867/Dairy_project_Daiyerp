# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class VillageLevelCollectionCentre(Document):
	def after_insert(self):
		"""create company and w/h configure associated company"""
		abbr = ""
		comp_doc = frappe.new_doc("Company")
		comp_doc.company_name = self.vlcc_name
		for i in self.vlcc_name.upper().split():
			abbr += i[0]
		comp_doc.abbr = abbr
		comp_doc.default_currency = "INR"
		comp_doc.insert() 

		wr_hs_doc = frappe.new_doc("Warehouse")
		wr_hs_doc.warehouse_name = self.vlcc_name
		wr_hs_doc.company = self.vlcc_name
		wr_hs_doc.insert()
		self.warehouse = wr_hs_doc.name
		self.save()
