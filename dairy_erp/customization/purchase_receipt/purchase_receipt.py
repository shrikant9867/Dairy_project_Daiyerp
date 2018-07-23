from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
import json
import copy

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

# make purchase invoice when vlcc do PR for local PO.
def make_pi_against_vlcc(doc,method=None):
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC' and \
		doc.supplier_type == "VLCC Local":
		pr = frappe.get_doc("Purchase Receipt",doc.name)
		pr_items = frappe.db.get_all("Purchase Receipt Item", "*", {"parent": pr.name})
		pi = frappe.new_doc("Purchase Invoice")
		pi.supplier = pr.supplier
		pi.supplier_type = pr.supplier_type
		pi.vlcc_milk_collection_record = pr.vlcc_milk_collection_record
		pi.company = pr.company
		pi.taxes_and_charges = pr.taxes_and_charges
		for item in pr_items:
			pi.append("items",
				{
					"item_code": item.item_code,
					"item_name": item.item_name,
					"description": item.description,
					"uom": item.uom,
					"qty": item.qty,
					"rate": item.rate,
					"amount": item.amount,
					"warehouse": item.warehouse,
					"purchase_receipt": doc.name
				}
			)
		pi.flags.ignore_permissions = True
		pi.flags.for_cc = True
		pi.submit()

@frappe.whitelist()
def toggle_supplier_invoice_no(doc_name):
	purchase_order_reference = ""
	material_request = frappe.db.get_value("Purchase Receipt Item",{"parent":doc_name},'material_request')
	if material_request:
		purchase_order_reference = frappe.db.sql("""select DISTINCT(po.name),pi.material_request 
												from `tabPurchase Order` po,
												`tabPurchase Order Item` pi 
												where pi.parent = po.name 
												and pi.material_request = "{0}" 
												and is_dropship = 1""".format(material_request),as_list=1)[0][0]
	if purchase_order_reference:
		purchase_receipt = frappe.get_doc("Purchase Receipt",doc_name)
		purchase_receipt.purchase_order_reference = purchase_order_reference if purchase_order_reference else ""
		purchase_receipt.save()
	return purchase_order_reference


def check_pr_flag(doc):
	#identify pr at which level
	flag = False
	for row in doc.items:
		if row.delivery_note:
			flag = True
	return flag
