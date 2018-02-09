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
		# add_all_roles_to(user_doc.name)
		if doc.address_type == 'Camp Office':
			user_doc.add_roles("Camp Operator")
		elif doc.address_type == "Chilling Centre":
			user_doc.add_roles("Chilling Center Operator")
		else:
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

@frappe.whitelist()
def after_install():
	create_supplier_type()
	create_translation()
	# create_local_customer()

def create_translation():

	if not frappe.db.sql("select name from `tabTranslation` where source_name='Material Request'"):
		mr_translation = frappe.new_doc("Translation")
		mr_translation.language = "en"
		mr_translation.source_name = "Material Request"
		mr_translation.target_name = "Material Indent"
		mr_translation.save()

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
		supp_doc.supplier_type = "Dairy Type"
		supp_doc.save()
	if not frappe.db.exists('Supplier Type', "Vlcc Type"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "Vlcc Type"
		supp_doc.save()
	if not frappe.db.exists('Supplier Type', "Farmer"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "Farmer"
		supp_doc.save()

def create_local_customer():

	if not frappe.db.exists('Customer', "Vlcc Local Cust"):
		loc_cust_doc = frappe.new_doc("Customer")
		loc_cust_doc.name = "Vlcc Local Cust"
		loc_cust_doc.customer_name = "Vlcc Local Cust"
		loc_cust_doc.customer_group = "Vlcc Local Customer"
		loc_cust_doc.territory = "All Territories"
		loc_cust_doc.flags.ignore_permissions = True
		loc_cust_doc.flags.ignore_mandatory = True
		loc_cust_doc.save()

def item_query(doctype, txt, searchfield, start, page_len, filters):
	item_groups = [str('Cattle feed'), str('Mineral Mixtures'), str('Medicines'), str('Artificial Insemination Services'),
		str('Veterinary Services'), str('Others/Miscellaneous'),str('Milk & Products')]
	return frappe.db.sql("""select name from tabItem where item_group in {0}""".format(tuple(item_groups)))

	
def on_submit_pr(doc,method=None):
	submit_dn(doc)
	validate_qty_against_mi(doc)
	check_if_dropship(doc) 
	
def submit_dn(doc):
	"""on submit of PR @VLCC DN gets auto submitted"""

	
	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC' and not doc.is_new():
		#check dn association with pr(1-1 mapping)
		dn_value = frappe.db.sql("""select parent from `tabDelivery Note Item` where purchase_receipt = '{0}' """.format(doc.name),as_dict=1)
		if dn_value:
			dn_doc = frappe.get_doc("Delivery Note",dn_value[0].get('parent'))
			for row , row_ in zip(doc.items, dn_doc.items):
				if row.delivery_note and row.qty < row_.qty:
					row_.rejected_qty = row_.qty - row.qty
					row_.qty = row.qty
			dn_doc.base_in_words = money_in_words(doc.base_grand_total,doc.currency)
			dn_doc.flags.ignore_permissions = True
			dn_doc.submit()

			make_si(dn_doc) 	#Sales Invoice @CO use case 1

			make_pi(doc) 	#Purchase Invoice @VLCC use case 1

def make_si(dn):
	"""Make auto sales invoice on submit of DN @Camp (DN gets submit on submit of PR)"""
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)

	si = frappe.new_doc("Sales Invoice")
	si.customer = dn.customer
	si.company = dn.company
	si.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	for item in dn.items:
		si.append("items",
			{
				"qty":item.qty,
				"item_code": item.item_code,
				"rate": item.rate,
				"amount": item.amount,
				"warehouse": item.warehouse,
				"cost_center": item.cost_center,
				"delivery_note": dn.name
			})
	si.flags.ignore_permissions = True
	si.save()
	si.submit()

def make_pi(doc):
	"""Make auto PI on submit of PR @VLCC"""

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	if user_doc.get('operator_type') == 'VLCC':
		pi = frappe.new_doc("Purchase Invoice")
		pi.supplier = doc.supplier
		pi.company = doc.company
		pi.camp_office = co
		for item in doc.items:
			pi.append("items",
				{
					"qty":item.qty,
					"item_code": item.item_code,
					"rate": item.rate,
					"amount": item.amount,
					"warehouse": item.warehouse,
					"cost_center": item.cost_center,
					"purchase_receipt": doc.name
				})

		pi.flags.ignore_permissions = True
		pi.save()
		pi.submit()


def make_pi_against_localsupp(po_doc,pr_doc):
	"""Make PI for CO(dairy) local supplier @CO Use case 2"""

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)

	pi = frappe.new_doc("Purchase Invoice")
	pi.supplier = po_doc.supplier
	pi.company = po_doc.company
	pi.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	for row_ in pr_doc.items:
		pi.append("items",
			{
				"qty":row_.qty,
				"item_code": row_.item_code,
				"rate": frappe.db.get('Item Price',{'name':row_.item_code,'buying':'1','company':po_doc.company,'price_list':po_doc.buying_price_list},'rate'),
				"purchase_order": po_doc.name
			})

	return pi

def validate_qty_against_mi(doc):
	"""update Material Request Status mapped with delivery Note"""

	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC' and not doc.is_new():
		dn_value = frappe.db.sql("""select parent from `tabDelivery Note Item` where purchase_receipt = '{0}' """.format(doc.name),as_dict=1)

		if dn_value:
			material_req_list = frappe.db.sql("""select sum(qty) as qty_sum, material_request from `tabDelivery Note Item` 
				where parent = '{0}' group by material_request""".format(dn_value[0].get('parent')),as_dict=1)
			
			for row in material_req_list:
				material_request_updater = frappe.get_doc("Material Request",row.get('material_request'))
				mr_qty = get_material_req_qty(material_request_updater)
				
				if mr_qty > row.get('qty_sum'):
					material_request_updater.per_delivered = 99.99
					material_request_updater.set_status("Partially Delivered")
					material_request_updater.save()

				elif mr_qty == row.get('qty_sum'):
					material_request_updater.per_delivered = 100
					material_request_updater.set_status("Delivered")
					material_request_updater.save()


def get_material_req_qty(doc):
	"""count total quantity for specific MI"""
	
	total_qty =0 
	for row in doc.items:
		total_qty += row.qty
	return total_qty

def check_if_dropship(doc):
	"""If dropship is checked on PO at Camp level of respective MR"""

	mr_list = []
	conditions = ""
	dairy = frappe.db.get_value("Company",{"is_dairy":1},"name")
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)

	if user_doc.get("operator_type") == 'VLCC':
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

					pi = make_pi_against_localsupp(po_doc,doc)		#Purchase Invoice @CO in use case 2

					if po_doc.is_dropship == 1:
						si = frappe.new_doc("Sales Invoice")
						si.customer = doc.company
						si.company = frappe.db.get_value("Company",{"is_dairy":1},"name")
						si.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

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

				si.flags.ignore_permissions = True  		#Sales Invoice @CO in use case 2
				si.save()
				si.submit()
				
				if pi:
					pi.flags.ignore_permissions = True  		#Purchase Invoice @CO in use case 2
					pi.save()
					pi.submit()

				make_pi(doc)			#Purchase Invoice @VLCC in use case 2
				mi_status_update(doc)


def mi_status_update(doc):

	material_req_list = frappe.db.sql("""select sum(qty) as qty_sum, material_request from `tabPurchase Receipt Item` 
				where parent = '{0}' group by material_request""".format(doc.name),as_dict=1)

	for row in material_req_list:
		material_request_updater = frappe.get_doc("Material Request",row.get('material_request'))
		mr_qty = get_material_req_qty(material_request_updater)
		
		if mr_qty > row.get('qty_sum'):
			material_request_updater.per_delivered = 99.99
			material_request_updater.set_status("Partially Delivered")
			material_request_updater.save()

		elif mr_qty == row.get('qty_sum'):
			material_request_updater.per_delivered = 100
			material_request_updater.set_status("Delivered")
			material_request_updater.save()
	


def validate_qty(doc, method):
	"""validate PR qty, must be equal to DN or less"""

	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC' and not doc.is_new():
		#check dn association with pr(1-1 mapping)
		dn_value = frappe.db.sql("""select parent from `tabDelivery Note Item` where purchase_receipt = '{0}' """.format(doc.name),as_dict=1)
		if dn_value:
			dn_doc = frappe.get_doc("Delivery Note",dn_value[0].get('parent'))
			for row , row_ in zip(doc.items, dn_doc.items):
				if row.qty > row_.qty:
					frappe.throw("Quantity should not be greater than {0} in row#{1}".format(row_.qty,row.idx))


def make_so_against_vlcc(doc,method=None):

	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC' and \
		frappe.db.get_value("Customer",doc.customer,"customer_group") == 'Farmer':

		vlcc = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"camp_office")
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

def validate_pr(doc,method=None):
	
	operator_type = frappe.db.get_value("User",frappe.session.user,"operator_type")
	if operator_type == 'Camp Office':
		for item in doc.items:		
			if item.purchase_receipt:
				pr = frappe.get_doc("Purchase Receipt",item.purchase_receipt)
				if pr.docstatus == 0:
					frappe.throw("Delivery note gets submit on acceptance of goods at Company <b>{0}</b>".format(doc.customer))


def set_co_warehouse_pr(doc,method=None):

	branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type"],as_dict=1)
	if branch_office.get('operator_type') == 'Camp Office':
		if doc.items:
			for item in doc.items:
				if not item.delivery_note:
					item.warehouse = frappe.db.get_value("Address",branch_office.get('branch_office'),"warehouse")
					if item.rejected_qty:
						item.rejected_warehouse = frappe.db.get_value("Address",branch_office.get('branch_office'),"warehouse")
	if branch_office.get('operator_type') == 'VLCC':
		if doc.items:
			vlcc = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"warehouse")
			for item in doc.items:
				item.warehouse = vlcc
				if item.rejected_qty:
					item.rejected_warehouse = vlcc



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
	create_local_customer()

def create_customer_group():
	customer_groups = ['Farmer', 'Vlcc', 'Dairy','Vlcc Local Customer']
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
	"""if MR reference on Delivery Note then only make PR"""
	
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
			purchase_rec.base_in_words = money_in_words(doc.base_rounded_total,doc.currency)
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

def mr_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	vlcc = frappe.db.get_values("Village Level Collection Centre",{"camp_office":user_doc.get('branch_office')},"name",as_dict=1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabMaterial Request`.company = '{0}')""".format(user_doc.get('company'))

	if user_doc.get('operator_type') == "Camp Office":
		company = ['"%s"'%comp.get('name') for comp in vlcc]
		return """`tabMaterial Request`.company in  ({company})""".format(company=','.join(company))

def pr_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	if user_doc.get('operator_type') == "VLCC":
		return """(`tabPurchase Receipt`.company = '{0}')""".format(user_doc.get('company'))

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabPurchase Receipt`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

def po_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabPurchase Order`.company = '{0}')""".format(user_doc.get('company'))

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabPurchase Order`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

def pi_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabPurchase Invoice`.company = '{0}')""".format(user_doc.get('company'))

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabPurchase Invoice`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

def dn_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabDelivery Note`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabDelivery Note`.company = '{0}')""".format(user_doc.get('company'))

def si_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabSales Invoice`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabSales Invoice`.company = '{0}')""".format(user_doc.get('company'))

def farmer_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabFarmer`.vlcc_name = '{0}')""".format(user_doc.get('company'))

def vlcc_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabVillage Level Collection Centre`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabVillage Level Collection Centre`.name = '{0}')""".format(user_doc.get('company'))

def fmrc_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabFarmer Milk Collection Record`.associated_vlcc = '{0}')""".format(user_doc.get('company'))

def vmcr_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	vlcc = frappe.db.get_values("Village Level Collection Centre",{"camp_office":user_doc.get('branch_office')},"name",as_dict=1)

	if user_doc.get('operator_type') == "Camp Office":
		company = ['"%s"'%comp.get('name') for comp in vlcc]
		return """`tabVlcc Milk Collection Record`.associated_vlcc in  ({company})""".format(company=','.join(company))

def pe_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	vlcc = frappe.db.get_values("Village Level Collection Centre",{"camp_office":user_doc.get('branch_office')},"name",as_dict=1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabPayment Entry`.company = '{0}')""".format(user_doc.get('company'))

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabPayment Entry`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

def supplier_permission(user):

	pass

	# user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	# if user_doc.get('operator_type') == "Camp Office":
	# 	return """(`tabSupplier`.camp_office = '{0}' and `tabSupplier`.supplier_type in ('Vlcc Type','Dairy Local'))""".format(user_doc.get('branch_office'))

	# if user_doc.get('operator_type') == "VLCC":
	# 	supplier_list = frappe.db.sql("""select s.name as supp,p.company from `tabSupplier` s, `tabParty Account` 
	# 					p where p.parent = s.name and p.company = '{0}' group by s.name""".format(user_doc.get('company')),as_dict=1)

	# 	supp = [ '"%s"'%sup.get("supp") for sup in supplier_list ]
	# 	return """tabSupplier.name in ({supp})"""\
	# 		.format(supp=','.join(supp))

def customer_permission(user):

	pass

	# user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	# if user_doc.get('operator_type') == "Camp Office":
	# 	return """(`tabCustomer`.camp_office = '{0}' and `tabCustomer`.customer_group = 'Vlcc')""".format(user_doc.get('branch_office'))

	# if user_doc.get('operator_type') == "VLCC":
	# 	customer_list = frappe.db.sql("""select c.name as cust from `tabCustomer` c, `tabParty Account` p where p.parent = c.name and 
	# 					p.company = '{0}' and customer_group in ('Farmer','Dairy') group by c.name""".format(user_doc.get('company')),as_dict=1)

	# 	customer = [ '"%s"'%cust.get("cust") for cust in customer_list ]
	# 	return """tabCustomer.name in ({customer})"""\
	# 		.format(customer=','.join(customer))


def set_camp(doc, method):
	camp = frappe.db.get_value("Sales Invoice",doc.voucher_no,'camp_office')
	doc.camp_office = camp
	doc.flags.ignore_permissions = True
