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

def set_co_warehouse_po(doc,method=None):
	branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type"],as_dict=1)
	if branch_office.get('operator_type') == 'Camp Office':	
		dairy = frappe.db.get_value("Company",{"is_dairy":1},"name")
		doc.company = dairy
		if doc.items:
			for item in doc.items:
				item.warehouse = frappe.db.get_value("Address",branch_office.get('branch_office'),"warehouse")


def validate_dairy_company(doc,method=None):
	if doc.address_type == 'Head Office':
		for link in doc.links:
			if link.link_doctype == 'Company':
				comp_doc = frappe.get_doc("Company",link.link_name)
				comp_doc.is_dairy = 1
				comp_doc.save()
	if doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		make_user(doc)


def set_vlcc_warehouse_mr(doc,method=None):
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC':
		if doc.items:
			for item in doc.items:
				item.warehouse = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"warehouse")


def make_user(doc):
	from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to
	if not frappe.db.sql("select name from `tabUser` where name=%s", doc.user):
		user_doc = frappe.new_doc("User")
		user_doc.email = doc.user
		user_doc.first_name = doc.operator_name
		user_doc.operator_type = doc.address_type
		user_doc.branch_office = doc.name
		user_doc.send_welcome_email = 0
		user_doc.new_password = "admin"
		user_doc.flags.ignore_permissions = True
		user_doc.flags.ignore_mandatory = True
		user_doc.save()
		add_all_roles_to(user_doc.name)
		give_permission(user_doc,"Address",doc.name)
		if doc.address_type == 'Camp Office':
			dairy = frappe.db.get_value("Company",{"is_dairy":1},"name")
			if dairy:
				give_permission(user_doc,"Company",dairy)
	else:
		frappe.throw("User exists already") 

def give_permission(user_doc,allowed_doctype,for_value):
	perm_doc = frappe.new_doc("User Permission")
	perm_doc.user = user_doc.email
	perm_doc.allow = allowed_doctype
	perm_doc.for_value = for_value
	perm_doc.flags.ignore_permissions = True
	perm_doc.flags.ignore_mandatory = True
	perm_doc.save()

def validate_headoffice(doc, method):
	count = 0
	for row in doc.links:
		count += 1
	if doc.is_new() and frappe.db.sql("select name from `tabAddress` where centre_id = '{0}'".format(doc.centre_id)):
		frappe.throw(_("Id exist Already"))
	if frappe.db.sql("select address_type from tabAddress where address_type = 'Head Office' and not name = '{0}'".format(doc.name)) and doc.address_type == "Head Office":
		frappe.throw(_("Head Office exist already"))
	if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and not doc.links:
		frappe.throw(_("Please Choose Company"))
	if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and not doc.centre_id:
		frappe.throw(_("Centre id needed"))
	if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and count!=1:
		frappe.throw(_("Only one entry allowed row"))
	if doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		for row in doc.links:
			if row.get('link_doctype') != "Company":
				frappe.throw(_("Row entry must be company"))
			elif row.get('link_name') and  frappe.get_value("Company",row.get('link_name'),'is_dairy') != 1:
				frappe.throw(_("Please choose <b>Dairy only</b>"))

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


def after_install():
	create_supplier_type()

def create_supplier_type():

	if not frappe.db.exists('Supplier Type', "Dairy Local"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "Dairy Local"
		supp_doc.save()
	if not frappe.db.exists('Supplier Type', "VLCC Local"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "VLCC Local"
		supp_doc.save()


def user_query(doctype, txt, searchfield, start, page_len, filters):
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC':
		return frappe.db.sql("""select name from tabCustomer where customer_group = 'Farmer'""")

def item_query(doctype, txt, searchfield, start, page_len, filters):
	item_groups = [str('Cattle feed'), str('Mineral Mixtures'), str('Medicines'), str('Artificial Insemination Services'),
		str('Veterinary Services'), str('Others/Miscellaneous'),str('Milk & Products')]
	return frappe.db.sql("""select name from tabItem where item_group in {0}""".format(tuple(item_groups)))

def make_pi(doc,method=None):
	operator_type = frappe.db.get_value("User",frappe.session.user,"operator_type")
	if operator_type == 'Camp Office' or operator_type == 'VLCC':
		pi = frappe.get_doc(make_purchase_invoice(doc.name))
		pi.insert()
		pi.submit()

def make_so_against_vlcc(doc,method=None):
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC' and \
		frappe.db.get_value("Customer",doc.customer,"customer_group") == 'Farmer':
		vlcc = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"camp_office")
		a = frappe.db.get_value("Address",{"name":vlcc},"warehouse")
		so = frappe.new_doc("Sales Order")
		so.company = frappe.db.get_value("Company",{"is_dairy":1},"name")
		so.customer = doc.company
		for item in doc.items:
			so.append("items", {
				"item_code": item.item_code,
				"item_name": item.item_name,
				"description":item.description,
				"qty": item.qty,
				"delivery_date":item.delivery_date,
				"warehouse": frappe.db.get_value("Address",{"name":vlcc},"warehouse"),
				"price_list_rate": item.price_list_rate,
				"rate": item.rate
			})
		so.flags.ignore_permissions = True
		so.flags.ignore_mandatory = True
		so.save()
		so.submit()

def make_si_against_vlcc(doc,method=None):
	operator_type = frappe.db.get_value("User",frappe.session.user,"operator_type")
	if operator_type == 'Camp Office' or operator_type == 'VLCC':
		si = make_sales_invoice(doc.name)
		si.submit()


def set_co_warehouse_pr(doc,method=None):
	branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type"],as_dict=1)
	if branch_office.get('operator_type') == 'Camp Office':
		if doc.items:
			for item in doc.items:
				item.warehouse = frappe.db.get_value("Address",branch_office.get('branch_office'),"warehouse")

def set_vlcc_warehouse(doc,method=None):
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC':
		if doc.items:
			for item in doc.items:
				item.warehouse = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"warehouse")
	

def create_item_group(args=None):
	item_groups = ['Cattle feed', 'Mineral Mixtures', 'Medicines', 'Artificial Insemination Services',
		'Veterinary Services', 'Others/Miscellaneous','Milk & Products']
	for i in item_groups:
		if not frappe.db.exists('Item Group',i):
			item_grp = frappe.new_doc("Item Group")
			item_grp.parent_item_group = "All Item Groups"
			item_grp.item_group_name = i
			item_grp.insert()
	create_customer_group()

def create_customer_group():
	customer_groups = ['Farmer', 'Vlcc', 'Dairy']
	for i in customer_groups:
		if not frappe.db.exists('Customer Group',i):
			cust_grp = frappe.new_doc("Customer Group")
			cust_grp.parent_customer_group = "All Customer Groups"
			cust_grp.customer_group_name = i
			cust_grp.insert()

def user_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("select name from tabCustomer where customer_group = 'Farmer'")


def user_query_dn(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("select name from tabCustomer where customer_group = 'Vlcc'")

def user_query_po(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("select name from tabSupplier where supplier_type = 'Dairy Local'")