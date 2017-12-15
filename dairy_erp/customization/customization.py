# -*- coding: utf-8 -*-
# Copyright (c) 2017, Indictrans and contributer and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json

def set_warehouse(doc, method):
	"""configure w/h for dairy components"""

	if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"]:
		wr_house_doc = frappe.new_doc("Warehouse")
		wr_house_doc.warehouse_name = doc.address_title
		wr_house_doc.company =  doc.links[0].link_name if doc.links else []
		wr_house_doc.insert()
		doc.warehouse = wr_house_doc.name
		doc.save()

def create_supplier_type():
	if not frappe.db.exists('Supplier Type', "Dairy Local"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "Dairy Local"
		supp_doc.save()
	if not frappe.db.exists('Supplier Type', "VLCC Local"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "VLCC Local"
		supp_doc.save()