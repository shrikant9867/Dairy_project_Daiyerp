# -*- coding: utf-8 -*-
# Copyright (c) 2017, Indictrans and contributer and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json
import re


def set_warehouse(doc, method=None):
	"""configure w/h for dairy components"""
	if frappe.db.sql("""select name from `tabAddress` where address_type ='Head Office'"""):
		if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and \
		   not frappe.db.exists('Warehouse', doc.address_title + " - "+frappe.db.get_value("Company",doc.links[0].link_name,"abbr")):
				wr_house_doc = frappe.new_doc("Warehouse")
				wr_house_doc.warehouse_name = doc.address_title
				wr_house_doc.company =  doc.links[0].link_name if doc.links else []
				wr_house_doc.insert()
				doc.warehouse = wr_house_doc.name
				doc.save()
	else:
		frappe.throw("Please create Head Office first for Dairy")


def validate_dairy_company(doc,method=None):
	if doc.address_type == 'Head Office':
		for link in doc.links:
			if link.link_doctype == 'Company':
				comp_doc = frappe.get_doc("Company",link.link_name)
				comp_doc.is_dairy = 1
				comp_doc.save()
	if doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		make_user_give_perm(doc)

def make_user_give_perm(doc):
	from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to
	if not frappe.db.sql("select name from `tabUser` where name=%s", doc.user):
		user_doc = frappe.new_doc("User")
		user_doc.email = doc.user
		user_doc.first_name = doc.operator_name
		user_doc.operator_type = doc.address_type
		user_doc.branch_office = doc.name
		user_doc.send_welcome_email = 0
		user_doc.flags.ignore_permissions = True
		user_doc.flags.ignore_mandatory = True
		user_doc.save()
		add_all_roles_to(user_doc.name)
		perm_doc = frappe.new_doc("User Permission")
		perm_doc.user = user_doc.email
		perm_doc.allow = "Address"
		perm_doc.for_value = doc.name
		perm_doc.flags.ignore_permissions = True
		perm_doc.flags.ignore_mandatory = True
		perm_doc.save()

	else:
		frappe.throw("User exists already") 

def validate_headoffice(doc, method):
	
	if frappe.db.sql("select address_type from tabAddress where address_type = 'Head Office' and not name = '{0}'".format(doc.name)) and doc.address_type == "Head Office":
		frappe.throw(_("Head Office exist already"))
	if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and not doc.links:
		frappe.throw(_("Please Choose Company"))
	validate_user(doc)

def validate_user(doc):
	if doc.address_type in ["Chilling Centre","Camp Office","Plant"] and not doc.user and not doc.operator_name:
		frappe.throw("Please add Operator Email ID and Name")
	elif doc.address_type in ["Chilling Centre","Camp Office","Plant"] and not doc.user:
		frappe.throw("Please add Operator Email ID")
	elif doc.address_type in ["Chilling Centre","Camp Office","Plant"] and not doc.operator_name:
		frappe.throw("Please add Operator name")



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

@frappe.whitelist()
def get_camp_office(doctype, txt, searchfield, start, page_len, filters):
	branch_office = frappe.db.get_value("User",frappe.session.user,"branch_office")
	return frappe.db.sql("""select name from `tabAddress` where name=%s""",branch_office)

@frappe.whitelist()
def get_pending_mr(data):
	data = json.loads(data)
	return frappe.db.sql("""select name,camp_office,schedule_date,company from `tabMaterial Request` where camp_office = %s and status = 'Pending'""",(data.get('camp_office')),as_dict=1)

@frappe.whitelist()
def get_item_table(data,doc):
	data = json.loads(data)
	doc = json.loads(doc)
	mr_list = []
	for mr in data:
		items = frappe.db.sql("""select distinct mr.name,mr_item.item_code,mr_item.item_name,mr_item.description,mr_item.qty,mr_item.schedule_date
			from `tabMaterial Request` mr, `tabMaterial Request Item` mr_item
			where mr.name = mr_item.parent and mr.name = %s""",(mr.get('name')),as_dict=1)
		mr_list.append(items)
	return mr_list