from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json


@frappe.whitelist()
def validate_item_qty(doc,method):
	pass

def validate_price_list(doc, method):
	user_doc = frappe.db.get_value("User",frappe.session.user,\
			['company','operator_type','branch_office'],as_dict=1)
	supplier_type = frappe.db.get_value("Supplier", doc.supplier , 'supplier_type')
	vlcc_attr = frappe.db.get_value("Village Level Collection Centre",user_doc.get('company'),\
				['camp_office', 'chilling_centre'],as_dict=1)
	
	if user_doc.get('operator_type') == "VLCC":
		if doc.buying_price_list not in ["GTVLCCB","LVLCCB-"+doc.get('company')]\
			and supplier_type == "VLCC Local":
				frappe.throw(_("Please Create Material Price List First Vlcc Buying"))
		elif supplier_type == "Dairy Type" and doc.buying_price_list not in \
			['LCOVLCCB-'+vlcc_attr.get('camp_office'), 'GTCOVLCCB']:
				pass
				# frappe.throw(_("Please Create Material Price List for Co to Vlcc"))
	
	if user_doc.get('operator_type') == "Camp Office" and not check_pr_flag(doc):
		if doc.buying_price_list not in ["GTCOB", "LCOB-"+ user_doc.get('branch_office')]:
			frappe.throw(_("Please Create Material Price List First"))


def check_pr_flag(doc):
	#identify pr at which level
	flag = False
	for row in doc.items:
		if row.delivery_note:
			flag = True
	return flag
