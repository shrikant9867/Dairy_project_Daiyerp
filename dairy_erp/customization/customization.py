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
				if item.material_request:
					mr = frappe.get_doc("Material Request",item.material_request)
					item.customer = mr.company
					item.address = frappe.db.get_value("Village Level Collection Centre",{"name":mr.company},"address_display")
	if branch_office.get('operator_type') == 'VLCC':
		vlcc = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"camp_office")
		for item in doc.items:
			item.warehouse = frappe.db.get_value("Address",{"name":vlcc},"warehouse")



def set_page_break(doc,method=None):
	branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type"],as_dict=1)
	if branch_office.get('operator_type') == 'Camp Office' and doc.is_dropship == 1:
		for item in doc.items:
			item.page_break = 1
		doc.items[-1].page_break = 0
def validate_dairy_company(doc,method=None):
	if doc.address_type == 'Head Office':
		for link in doc.links:
			if link.link_doctype == 'Company':
				comp_doc = frappe.get_doc("Company",link.link_name)
				comp_doc.is_dairy = 1
				comp_doc.save()
	if doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		make_user(doc)

def make_user(doc):
	from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to
	dairy = frappe.db.get_value("Company",{"is_dairy":1},"name")
	if not frappe.db.sql("select name from `tabUser` where name=%s", doc.user):
		user_doc = frappe.new_doc("User")
		user_doc.email = doc.user
		user_doc.first_name = doc.operator_name
		user_doc.operator_type = doc.address_type
		user_doc.branch_office = doc.name
		user_doc.company = dairy
		user_doc.send_welcome_email = 0
		user_doc.new_password = "admin"
		user_doc.flags.ignore_permissions = True
		user_doc.flags.ignore_mandatory = True
		user_doc.save()
		add_all_roles_to(user_doc.name)
		give_permission(user_doc,"Address",doc.name)
		if doc.address_type == 'Camp Office':
			if dairy:
				give_permission(user_doc,"Company",dairy)
	else:
		frappe.throw("User exists already") 

def give_permission(user_doc,allowed_doctype,for_value):
	perm_doc = frappe.new_doc("User Permission")
	perm_doc.user = user_doc.email
	perm_doc.allow = allowed_doctype
	perm_doc.for_value = for_value
	perm_doc.apply_for_all_roles = 0
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
	if not frappe.db.exists('Supplier Type', "Dairy Type"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "Dairy Local"
		supp_doc.save()
	if not frappe.db.exists('Supplier Type', "Vlcc Type"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "Dairy Local"
		supp_doc.save()



def item_query(doctype, txt, searchfield, start, page_len, filters):
	item_groups = [str('Cattle feed'), str('Mineral Mixtures'), str('Medicines'), str('Artificial Insemination Services'),
		str('Veterinary Services'), str('Others/Miscellaneous'),str('Milk & Products')]
	return frappe.db.sql("""select name from tabItem where item_group in {0}""".format(tuple(item_groups)))

# def make_pi(doc,method=None):
	# operator_type = frappe.db.get_value("User",frappe.session.user,"operator_type")
	# if operator_type == 'Camp Office' or operator_type == 'VLCC':
	# 	pi = frappe.get_doc(make_purchase_invoice(doc.name))
	# 	pi.insert()
	# 	pi.submit()
	
def submit_dn(doc,method=None):
	po_list = []
	dn_flag = 0
	local_supplier = ""
	dairy = frappe.db.get_value("Company",{"is_dairy":1},"name")
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC':
		for item in doc.items:
			if item.delivery_note:
				dn_flag = 1
				dn = frappe.get_doc("Delivery Note",item.delivery_note)
				for data in dn.items:
					dn_flag = 2
					if item.qty < data.qty:
						print "iside if..\n\n"
						rejected = data.qty - item.qty
						data.qty = item.qty
						data.rejected_qty = rejected
					# elif item.qty > data.qty:
					# 	print item.qty,"item.qty....\n\n"
					# 	print data.qty,"data.qty...\n\n"
					# 	frappe.throw("Quantity should not be greater than {0}".format(data.qty))

					if data.material_request:		
						mr = frappe.get_doc("Material Request",data.material_request)
						# mr.per_closed = 100
						# mr.set_status("Closed")
						# mr.save()
						for i in mr.items:
							if i.qty == data.qty:
								mr.per_delivered = 100
								mr.set_status("Delivered")
								mr.flags.ignore_permissions = True
								mr.save()
							elif i.qty > data.qty:
								qty = i.qty - data.qty
								mr.per_delivered = 99.99
								mr.set_status("Partially Delivered")
								mr.flags.ignore_permissions = True
								mr.save()
				if dn_flag == 2:
					dn.flags.ignore_permissions = True		
					dn.submit()
				si_obj = frappe.new_doc("Sales Invoice")
		 		si_obj.customer = dn.customer
		 		si_obj.company = dn.company
		 		for item in dn.items:
			 		si_obj.append("items",
			 		{
			 			"item_code": item.item_code,
			 			"rate": item.rate,
			 			"amount": item.amount,
			 			"warehouse": item.warehouse,
						"cost_center": item.cost_center,
						"delivery_note": dn.name
			 		})
		 		si_obj.flags.ignore_permissions = True
		 		si_obj.insert()
				si_obj.submit()

		
			po = frappe.db.sql("""select p.name,pi.material_request from `tabPurchase Order` p,`tabPurchase Order Item` pi where p.company = 'Dairy' 
							and pi.material_request = %s and p.docstatus = 1 and p.name = pi.parent""",(item.material_request),as_dict=1)
			for i in po:
				po_list.append(i.get('name'))
				mr = frappe.get_doc("Material Request",i.get('material_request'))
				mr.per_closed = 100
				mr.set_status("Closed")
				mr.save()
		if dn_flag:
			pi = frappe.get_doc(make_purchase_invoice(doc.name))
			pi.flags.ignore_permissions = True
			pi.submit()
		dropship = 0
		for po in po_list:
			po_doc = frappe.get_doc("Purchase Order",po)
			if po_doc.is_dropship == 1:
				dropship = 1
				local_supplier = po_doc.supplier
				si = frappe.new_doc("Sales Invoice")
				si.customer = doc.company
				si.company = dairy
				for item in doc.items:
					si.append("items",
					{
						"item_code": item.item_code,
						"item_name": item.item_code,
						"description": item.item_code,
						"uom": item.uom,
						"qty": item.qty,
						"rate": item.rate,
						"amount": item.amount,
						"warehouse": frappe.db.get_value("Address",{"name":po_doc.camp_office},"warehouse")
					})
					if item.material_request:
						mr = frappe.get_doc("Material Request",item.material_request)
						for i in mr.items:
							if item.qty > i.qty:
								frappe.throw("Quantity should not be greater than {0}".format(i.qty))
		if dropship:
			si.flags.ignore_permissions = True
			si.submit()
			pi = frappe.get_doc(make_purchase_invoice(doc.name))
			pi.flags.ignore_permissions = True
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
	# operator_type = frappe.db.get_value("User",frappe.session.user,"operator_type")
	# if operator_type == 'Camp Office' or operator_type == 'VLCC':
	# 	si = make_sales_invoice(doc.name)
	# 	si.submit()
	operator_type = frappe.db.get_value("User",frappe.session.user,"operator_type")
	if operator_type == 'Camp Office':
		for item in doc.items:
			if item.material_request:
				mr = frappe.get_doc("Material Request",item.material_request)
				for data in mr.items:
					if data.qty == item.qty:
						# if mr.per_ordered == 100:
						mr.per_delivered = 100
						mr.set_status("Delivered")
						mr.flags.ignore_permissions = True
						mr.save()
					elif data.qty > item.qty:
						qty = data.qty - item.qty
						mr.per_delivered = 99.99
						mr.set_status("Partially Delivered")
						mr.flags.ignore_permissions = True
						mr.save()
						# frappe.db.sql("""update `tabMaterial Request Item` set qty = {0} where parent = '{1}'""".format(qty,mr.name))
			if item.purchase_receipt:
				pr = frappe.get_doc("Purchase Receipt",item.purchase_receipt)
				if pr.docstatus == 0:
					frappe.throw("You are not allow to submit")


def set_co_warehouse_pr(doc,method=None):
	branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type"],as_dict=1)
	if branch_office.get('operator_type') == 'Camp Office':
		if doc.items:
			for item in doc.items:
				if not item.delivery_note:
					item.warehouse = frappe.db.get_value("Address",branch_office.get('branch_office'),"warehouse")
	if branch_office.get('operator_type') == 'VLCC':
		if doc.items:
			vlcc = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"warehouse")
			for item in doc.items:
				item.warehouse = vlcc

def set_vlcc_warehouse(doc,method=None):
	branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type","company"],as_dict=1)
	if branch_office.get('operator_type') == 'Camp Office':
		company_abbr = frappe.db.get_value("Company", branch_office.get('company'), "abbr")
		doc.company = branch_office.get('company')
		if doc.items:
			for item in doc.items:
				item.warehouse = frappe.db.get_value("Address",branch_office.get('branch_office'),"warehouse")
				item.expense_account = 'Cost of Goods Sold - '+ company_abbr
				item.cost_center = 'Main - '+ company_abbr

	if branch_office.get('operator_type') == 'VLCC':
		if doc.customer:
			if frappe.db.get_value("Customer",{"name":doc.customer},"customer_group") == "Farmer":
				if doc.items:
					for item in doc.items:
						item.warehouse = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"warehouse")

def set_mr_warehouse(doc,method=None):
	branch_office = frappe.db.get_value("User",frappe.session.user,["operator_type","company"],as_dict=1)
	if branch_office.get('operator_type') == 'VLCC':
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

def user_query_dn(doctype, txt, searchfield, start, page_len, filters):
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'Camp Office':
		return frappe.db.sql("select name from tabCustomer where customer_group = 'Vlcc'")
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC':
		return frappe.db.sql("select name from tabCustomer where customer_group = 'Farmer'")

def user_query_po(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("select name from tabSupplier where supplier_type = 'Dairy Local'")

def user_query(doctype, txt, searchfield, start, page_len, filters):
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC':
		return frappe.db.sql("""select name from tabCustomer where customer_group = 'Farmer'""")

def make_purchase_receipt(doc,method=None):
	branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type","company"],as_dict=1)
	mr_flag = 0
	if branch_office.get('operator_type') == 'Camp Office':
		for item in doc.items:
			if item.material_request:
				mr_flag = 1
		if mr_flag:		
			purchase_rec = frappe.new_doc("Purchase Receipt")
			purchase_rec.supplier =  branch_office.get('branch_office')
			purchase_rec.company = doc.customer
			for item in doc.items:
				purchase_rec.append("items",
					{
						"item_code": item.item_code,
						"item_name": item.item_code,
						"description": item.item_code,
						"uom": item.uom,
						"qty": item.qty,
						"rate":item.rate,
						"amount": item.amount,
						"delivery_note":doc.name,
						"warehouse": frappe.db.get_value("Village Level Collection Centre",{"name":doc.customer},"warehouse")
					}
				)
			purchase_rec.flags.ignore_permissions = True
			purchase_rec.save()
			for item in doc.items:
				item.purchase_receipt = purchase_rec.name
			doc.save()
			
def set_company(doc, method):
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	if user_doc.get('operator_type') == "VLCC" and doc.supplier_type == "VLCC Local":
		doc.company = user_doc.get('company')
