# -*- coding: utf-8 -*-
# Copyright (c) 2017, Indictrans and contributer and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json
import re
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
from frappe.utils import money_in_words


def set_target_warehouse(doc,method):
	chilling_centre = ""
	doc.purpose = "Material Transfer"
	target_warhouse = ""
	user_ = frappe.db.get_value("User", frappe.session.user, ['branch_office','operator_type'],as_dict=1)
	if user_.get('operator_type') == "Camp Office":
		for row in doc.items:
			chilling_centre = row.chilling_centre
			row.s_warehouse = frappe.db.get_value("Address",user_.get('branch_office'),'warehouse')
			row.t_warehouse = frappe.db.get_value("Address",chilling_centre,'warehouse')
		target_warhouse = frappe.db.get_value("Address",chilling_centre,'warehouse')
	
	if target_warhouse and user_.get('operator_type') == "Camp Office":
		doc.to_warehouse = target_warhouse
	
	if user_.get('operator_type') == "Chilling Centre":
		for row in doc.items:
			chilling_centre = row.chilling_centre
			row.s_warehouse = frappe.db.get_value("Address",doc.camp_office,'warehouse')
			row.t_warehouse = frappe.db.get_value("Address",user_.get('branch_office'),'warehouse')
			if row.accepted_qty:
				row.qty = row.accepted_qty
				row.rejected_qty = row.original_qty - row.accepted_qty
	


def validate_camp_submission(doc, method):
	if frappe.db.get_value("User",frappe.session.user,'operator_type') == "Camp Office":
		frappe.throw(_("Not allowed to Submit"))


def drop_ship_opeartion(doc, method):
	if doc.is_dropship:
		is_dairy = frappe.db.get_value("Company",{"is_dairy":1},'name')
		pi_doc = frappe.new_doc("Purchase Invoice")
		pi_doc.company = is_dairy
		pi_doc.supplier = doc.dropship_supplier
		pi_doc.buying_price_list = "Standard Buying"
		for row in doc.items:
			pi_doc.append("items",{
				"item_code": row.item_code,
				"item_name": row.item_name
				})
		pi_doc.credit_to = "Creditors - "+frappe.db.get_value("Company",is_dairy,'abbr')
		pi_doc.flags.ignore_permissions = True
		pi_doc.flags.ignore_mandatory = True
		pi_doc.save()
		pi_doc.submit()


