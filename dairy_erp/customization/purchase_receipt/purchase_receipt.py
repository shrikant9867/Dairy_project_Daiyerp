from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json


@frappe.whitelist()
def validate_item_qty(doc,method):
	print"\n\n\n\n\n\n###############validate_item_qty##################"
	# print"########doc##########",doc
	# for item in doc.items:
	# 	if item.purchase_order:
	# 		po_doc=frappe.get_doc("Purchase Order",item.purchase_order)

	# 		for po_items in po_doc.items:
	# 			if item.item_code == po_items.item_code:
	# 				if item.qty > po_items.qty:
	# 					frappe.throw(_("Accepted Qty cannot be greater than Requested Qty"))
					
