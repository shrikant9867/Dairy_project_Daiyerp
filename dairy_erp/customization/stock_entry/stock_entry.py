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
from frappe.utils import money_in_words, has_common
from erpnext.stock.stock_balance import get_balance_qty_from_sle



def set_target_warehouse(doc,method):
	if not doc.flags.is_api:
		chilling_centre = ""
		doc.purpose = "Material Transfer"
		target_warhouse = ""
		user_ = frappe.db.get_value("User", frappe.session.user, ['branch_office','operator_type'],as_dict=1)
		if user_.get('operator_type') == "Camp Office":
			for row in doc.items:
				row.camp_qty = row.qty
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
	if frappe.db.get_value("User",frappe.session.user,'operator_type') == "Camp Office" and not doc.flags.is_api:
		frappe.throw(_("Stock Entry gets submit on acceptance of goods at <b>{0}</b>".format(doc.items[0].chilling_centre)))


def drop_ship_opeartion(doc, method):
	pass


def check_if_dropship(doc,method):
	"""If dropship is checked on PO at Camp level of respective MR"""

	mr_list = []
	conditions = ""
	dairy = frappe.db.get_value("Company",{"is_dairy":1},"name")
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	if user_doc.get("operator_type") == 'Chilling Centre' and not doc.flags.is_api:
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


	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company', 'branch_office'], as_dict =1)
	#co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('branch_office')},"camp_office")
	expense_account = frappe.db.get_value("Address",po_doc.camp_office, "expense_account")
	pi = frappe.new_doc("Purchase Invoice")
	pi.supplier = po_doc.supplier
	pi.company = po_doc.company
	# pi.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
	pi.camp_office = po_doc.camp_office
	pi.buying_price_list = get_price_list()
	if expense_account:
		pi.remarks = "[#"+expense_account+"#]"
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
	# pr_doc.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
	pr_doc.camp_office = po_doc.camp_office
	pr_doc.buying_price_list = get_price_list()
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
	if not doc.flags.is_api:
		update_received_stock_qty(doc)
		mi_list = frappe.db.get_all("Stock Entry Detail", {"parent": doc.name}, "material_request as mi")
		for mi in mi_list:
			mi = frappe.get_doc("Material Request", mi.get('mi'))
			all_received = True
			for i in mi.items:
				if i.qty != i.received_stock_qty:
					all_received = False
			mi_status = "Delivered" if all_received else "Partially Delivered"
			per_delivered = 100 if all_received else 99.99
			mi.per_delivered = per_delivered
			mi.set_status(status=mi_status)
			mi.flags.ignore_permissions = True
			mi.flags.ignore_validate_update_after_submit = True
			mi.save()

def update_received_stock_qty(doc):
	for st_i in doc.items:
		if st_i.get('material_request'):
			mi = frappe.get_doc("Material Request", st_i.get('material_request'))
			for i in mi.items:
				if st_i.item_code == i.item_code and st_i.material_request == i.parent:
					i.received_stock_qty =  i.received_stock_qty + st_i.qty
			mi.flags.ignore_permissions = True
			mi.save()

def se_permission_query(user):
	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	if has_common(["Chilling Center Operator", "Chilling Center Manager"], roles) and user != 'Administrator':
		query = """`tabStock Entry`.owner = '{0}'""".format(user)
		branch_office = frappe.db.get_value("User", user, "branch_office")
		if branch_office:
			st_entries = frappe.db.sql("select distinct parent from `tabStock Entry Detail` \
					where chilling_centre = '{0}'".format(branch_office))
			if st_entries:
				st = "(" + ",".join([ "'{0}'".format(s[0]) for s in st_entries ]) + ")"
				query += " or `tabStock Entry`.name in {0}".format(st)
		return query
	elif has_common(['Vlcc Manager',"Vlcc Operator"],roles) and user != 'Administrator':
		return """`tabStock Entry`.company = '{0}'""".format(user_doc.get('company'))

	elif has_common(["Camp Manager", "Camp Operator"], roles) and user != 'Administrator':
		return """`tabStock Entry`.camp_office = '{0}'""".format(user_doc.get('branch_office'))



def get_price_list():
	user_attr = frappe.db.get_value("User",frappe.session.user,\
				['operator_type', 'company', 'branch_office'],as_dict=1)
	
	if user_attr.get('operator_type') == "VLCC":
		camp = frappe.db.get_value("Village Level Collection Center", \
			user_attr.get('company'),'camp_office')
		if frappe.db.exists("Price List", "LCOB-"+camp.get('camp_office')):
			return "LCOB-"+camp
		elif frappe.db.exists("Price List", "GTCOB"):
			return "GTCOB"

	if user_attr.get('operator_type') == "Chilling Centre":
		camp = frappe.db.get_value("Address", user_attr.get('branch_office'), 'associated_camp_office')
		if frappe.db.exists("Price List", "LCOB-"+camp):
			return "LCOB-"+camp
		elif frappe.db.exists("Price List","GTCOB"):
			return "GTCOB"

	if user_attr.get('operator_type') == "Camp Office":
		if frappe.db.exists("Price List","LCOB-"+user_attr.get('branch_office')):
			return "LCOB-"+camp
		elif frappe.db.exists("Price List","GTCOB"):
			return "GTCOB"