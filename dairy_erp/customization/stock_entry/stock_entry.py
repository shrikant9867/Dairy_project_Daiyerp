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
	user_ = frappe.db.get_value("User", frappe.session.user, ['branch_office','operator_type'],as_dict=1)
	if user_.get('operator_type') == "Camp Office":
		for row in doc.items:
			chilling_centre = row.chilling_centre
			row.s_warehouse = frappe.db.get_value("Address",user_,'warehouse')
			row.t_warehouse = frappe.db.get_value("Address",chilling_centre,'warehouse')
		target_warhouse = frappe.db.get_value("Address",chilling_centre,'warehouse')
	
	if target_warhouse:
		doc.to_warehouse = target_warhouse  


def validate_camp_submission(doc, method):
	if frappe.db.get_value("User",frappe.session.user,'operator_type') == "Camp Office":
		frappe.throw(_("Not allowed to Submit"))
