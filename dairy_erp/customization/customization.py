# -*- coding: utf-8 -*-
# Copyright (c) 2017, Indictrans and contributer and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json

def set_warehouse(doc, method=None):
	"""configure w/h for dairy components"""

	if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and \
	   not frappe.db.exists('Warehouse', doc.address_title + " - "+frappe.db.get_value("Company",doc.links[0].link_name,"abbr")):
			wr_house_doc = frappe.new_doc("Warehouse")
			wr_house_doc.warehouse_name = doc.address_title
			wr_house_doc.company =  doc.links[0].link_name if doc.links else []
			wr_house_doc.insert()
			doc.warehouse = wr_house_doc.name
			doc.save()

def validate_headoffice(doc, method):
	
	if frappe.db.sql("select address_type from tabAddress where address_type = 'Head Office' and not name = '{0}'".format(doc.name)) and doc.address_type == "Head Office":
		frappe.throw(_("Head Office exist already"))
	if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and not doc.links:
		frappe.throw(_("Please Choose Company"))

def update_warehouse(doc, method):
	"""update w/h for address for selected type ==>[cc,co,plant]"""
	set_warehouse(doc)

def create_supplier_type():
	if not frappe.db.exists('Supplier Type', "Dairy Local"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "Dairy Local"
		supp_doc.save()
	if not frappe.db.exists('Supplier Type', "VLCC Local"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "VLCC Local"
		supp_doc.save()