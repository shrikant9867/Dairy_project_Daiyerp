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
	pass
	# if doc.is_dropship:
		# check_if_dropship(doc)
		# is_dairy = frappe.db.get_value("Company",{"is_dairy":1},'name')
		# pi_doc = frappe.new_doc("Purchase Invoice")
		# pi_doc.company = is_dairy
		# pi_doc.supplier = doc.dropship_supplier
		# pi_doc.buying_price_list = "Standard Buying"
		# for row in doc.items:
		# 	pi_doc.append("items",{
		# 		"item_code": row.item_code,
		# 		"item_name": row.item_name
		# 		})
		# pi_doc.credit_to = "Creditors - "+frappe.db.get_value("Company",is_dairy,'abbr')
		# pi_doc.flags.ignore_permissions = True
		# pi_doc.flags.ignore_mandatory = True
		# pi_doc.save()
		# pi_doc.submit()


def check_if_dropship(doc,method):
	"""If dropship is checked on PO at Camp level of respective MR"""

	mr_list = []
	conditions = ""
	dairy = frappe.db.get_value("Company",{"is_dairy":1},"name")
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	if user_doc.get("operator_type") == 'Chilling Centre':
		print "inside check if dropship+++++++++++++++++\n\n"
		for item in doc.items:
			if item.material_request:
				mr_list.append(str(item.material_request))

		if mr_list:
			conditions = "and pi.material_request = '{0}'".format(mr_list[0]) if len(mr_list) == 1 else "and pi.material_request in {0}".format(tuple(mr_list))

		#check PO with dropship
		if conditions:
			po = frappe.db.sql("""select p.name,pi.material_request from `tabPurchase Order` p,`tabPurchase Order Item` pi where p.company = '{0}' 
							{1} and p.docstatus = 1 and p.name = pi.parent and p.is_dropship = 1 group by pi.material_request""".format(dairy,conditions),as_dict=1)
			if po:
				po_data = [data.get('name') for data in po]

				for data in set(po_data):
					po_doc = frappe.get_doc("Purchase Order",data)

					pi = make_pi_against_localsupp(po_doc,doc)
					pr = make_pr_against_localsupp(po_doc,doc)		
				
				if pi:
					pi.flags.ignore_permissions = True  		
					pi.save()
					pi.submit()

				# mi_status_update(doc)


def make_pi_against_localsupp(po_doc,stock_doc):
	"""Make PI for CO(dairy) local supplier @CO Use case 2"""


	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	pi = frappe.new_doc("Purchase Invoice")
	pi.supplier = po_doc.supplier
	pi.company = po_doc.company
	pi.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	for row_ in stock_doc.items:
		pi.append("items",
			{
				"qty":row_.qty,
				"item_code": row_.item_code,
				# "rate": row_.rate, #frappe.db.get('Item Price',{'name':row_.item_code,'buying':'1','company':po_doc.company,'price_list':po_doc.buying_price_list},'rate'),
				"purchase_order": po_doc.name
			})
	return pi

	
def make_pr_against_localsupp(po_doc,stock_doc):
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
	
	pr_doc = frappe.new_doc("Purchase Receipt")
	pr_doc.supplier = po_doc.supplier
	pr_doc.company = po_doc.company
	pr_doc.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	for row_ in stock_doc.items:
		print row_.__dict__
		pr_doc.append("items",
			{
				"qty":row_.qty,
				"item_code": row_.item_code,
				# "rate": row_.rate, #frappe.db.get('Item Price',{'name':row_.item_code,'buying':'1','company':po_doc.company,'price_list':po_doc.buying_price_list},'rate'),
				"purchase_order": po_doc.name,
				"warehouse": row_.s_warehouse
			})
	pr_doc.flags.ignore_permissions = True  		
	pr_doc.save()
	pr_doc.submit()

def update_mi_status(doc, method=None):
# update MI delivery status
	stock_entry_against_mi = frappe.db.get_value("Stock Entry Detail", {
	"parent": doc.name}, "material_request")
	if stock_entry_against_mi:
		stock_in_qty = frappe.db.sql("""select sum(qty) as qty, material_request as mi 
		from `tabStock Entry Detail` where parent = '{0}' 
		group by material_request""".format(doc.name),as_dict=True)
		if stock_in_qty:
			for st in stock_in_qty:
				if st.get('mi'):
					mi_qty = frappe.db.get_value("Material Request Item", {
					"parent": st.get('mi')}, "sum(qty) as mi_qty")
					mi = frappe.get_doc("Material Request", st.get('mi'))
					if st.get('qty') < mi_qty:
						mi.per_delivered = 99.99
						mi.set_status(status="Partially Delivered", update=True)
						mi.flags.ignore_permissions = True
						mi.save()
					elif st.get('qty') == mi_qty:
						mi.per_delivered = 100
						mi.set_status(status="Delivered", update=True)
						mi.flags.ignore_permissions = True
						mi.save()




