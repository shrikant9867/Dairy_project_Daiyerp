# -*- coding: utf-8 -*-
# Copyright (c) 2017, Indictrans and contributer and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.stock_balance import get_balance_qty_from_sle
import json
import re
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,now_datetime
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
from frappe.utils import money_in_words
from frappe.utils import has_common
from dairy_erp.dairy_utils import make_dairy_log
from dairy_erp.customization.price_list.price_list_customization \
	import get_selling_price_list, get_buying_price_list
from dairy_erp.customization.sales_invoice.sales_invoice import get_taxes_and_charges_template


def validate_dairy_company(doc,method=None):

	if doc.address_type == 'Head Office':
		for link in doc.links:
			if link.link_doctype == 'Company':
				comp_doc = frappe.get_doc("Company",link.link_name)
				comp_doc.is_dairy = 1
				comp_doc.save()

	if doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		doc.append("links",
			{
			"link_doctype": "Company",
			"link_name": frappe.db.get_value("Company",{"is_dairy":1},"name")
			})
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.save()
	if doc.address_type == "Vlcc" and not doc.links:
		frappe.throw(_("Please choose <b>vlcc company</b>"))

	# set address as vlcc if vlcc user
	if has_common(frappe.get_roles(), ["Vlcc Manager", "Vlcc Operator"]) and not doc.vlcc:
		company = frappe.db.get_value("User", frappe.session.user, "company")
		if company:
			frappe.db.set_value("Address", doc.name, "vlcc", company)

def make_account_and_warehouse(doc, method=None):
	try:
		if doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
			if frappe.db.get_value("Address", {"address_type": "Head Office"}, "name"):
				make_accounts(doc)
				make_warehouse(doc)
			elif doc.address_type != "Head Office":
				frappe.throw(_("Please create Head Office first"))
	except Exception as e:
		raise e

def make_accounts(doc):
	company_abbr = frappe.db.get_value("Company",doc.links[0].link_name,"abbr")
	# Income Account
	if not frappe.db.exists("Account", doc.address_title + " Income - " + company_abbr) and doc.links:
		inc_acc = frappe.new_doc("Account")
		inc_acc.account_name = doc.address_title + " Income"
		inc_acc.parent_account = "Direct Income - " + company_abbr
		inc_acc.insert()
		doc.income_account = inc_acc.name

	# Expence Account
	if not frappe.db.exists("Account", doc.address_title + " Expense - " + company_abbr) and doc.links:
		exp_acc = frappe.new_doc("Account")
		exp_acc.account_name = doc.address_title + " Expense"
		exp_acc.parent_account = "Stock Expenses - " + company_abbr
		exp_acc.insert()
		doc.expense_account = exp_acc.name

	# Stock Account
	if not frappe.db.exists("Account", doc.address_title + " Stock - " + company_abbr) and doc.links:
		stock_acc = frappe.new_doc("Account")
		stock_acc.account_name = doc.address_title + " Stock"
		stock_acc.account_type = "Stock"
		stock_acc.parent_account = "Stock Assets - " + company_abbr
		stock_acc.insert()
		doc.stock_account = stock_acc.name
		doc.save()

def make_warehouse(doc):
	"""configure w/h for dairy components"""
	if frappe.db.sql("""select name from `tabAddress` where address_type ='Head Office'"""):

		company_abbr = frappe.db.get_value("Company",doc.links[0].link_name,"abbr")
		if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and \
		   not frappe.db.exists('Warehouse', doc.address_title + " - "+ company_abbr):

				wr_house_doc = frappe.new_doc("Warehouse")
				wr_house_doc.warehouse_name = doc.address_title
				wr_house_doc.company =  doc.links[0].link_name if doc.links else []
				# wr_house_doc.account = doc.address_title + " Stock - " + company_abbr
				wr_house_doc.insert()
				doc.warehouse = wr_house_doc.name
				doc.save()

		if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and \
		   not frappe.db.exists('Warehouse', doc.address_title +"-Rejected"+ " - "+ company_abbr):
				wr_house_doc = frappe.new_doc("Warehouse")
				wr_house_doc.warehouse_name = doc.address_title + "-Rejected"
				wr_house_doc.company =  doc.links[0].link_name if doc.links else []
				# wr_house_doc.account = doc.address_title + " Stock - " + company_abbr
				wr_house_doc.insert()
				doc.rejected_warehouse = wr_house_doc.name
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
					item.customer = mr.company if not item.chilling_centre else ""
					chilling_centre_doc = frappe.get_doc("Address",item.chilling_centre) if item.chilling_centre else ""
					addr1 = chilling_centre_doc.address_line1 if chilling_centre_doc and chilling_centre_doc.address_line1 else ""
					addr2 = chilling_centre_doc.address_line2 if chilling_centre_doc and chilling_centre_doc.address_line2 else ""
					city = chilling_centre_doc.city if chilling_centre_doc and chilling_centre_doc.city else ""
					country = chilling_centre_doc.country if chilling_centre_doc and chilling_centre_doc.country else ""
					state = chilling_centre_doc.state if chilling_centre_doc and chilling_centre_doc.state else ""
					address_ = addr1+","+addr2+","+city+","+country+","+state
					# type_ = frappe.db.get_value("Address", item.chilling_centre, 'address_type')
					# if type_ != "Chilling Centre":
					# 	item.chilling_centre = ""
					item.address = frappe.db.get_value("Village Level Collection Centre",{"name":mr.company},"address_display") if not item.chilling_centre  else address_
	
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

def validate_headoffice(doc, method):

	count = 0
	for row in doc.links:
		count += 1
	if doc.is_new() and frappe.db.sql("select name from `tabAddress` where centre_id = '{0}'".format(doc.centre_id)):
		frappe.throw(_("Centre Id exist Already"))
	if frappe.db.sql("select address_type from tabAddress where address_type = 'Head Office' and not name = '{0}'".format(doc.name)) and doc.address_type == "Head Office":
		frappe.throw(_("Head Office exist already"))
	if doc.address_type in ["Head Office"] and not doc.links:
		frappe.throw(_("Please Choose Company from <b>Reference Section</b>"))
	if doc.address_type in ["Chilling Centre","Head Office","Camp Office","Plant"] and not doc.centre_id:
		frappe.throw(_("Centre id needed"))
	if doc.address_type in ["Head Office"] and count!=1:
		frappe.throw(_("Only one entry allowed row"))
	if doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		for row in doc.links:
			if row.get('link_doctype') != "Company":
				frappe.throw(_("Row entry must be company"))
			elif row.get('link_name') and  frappe.get_value("Company",row.get('link_name'),'is_dairy') != 1:
				frappe.throw(_("Please choose <b>Dairy only</b>"))
	if doc.address_type == "Head Office":
		for row in doc.links:
			if row.get('link_doctype') != "Company":
				frappe.throw(_("Row entry must be company"))



def update_warehouse(doc, method):
	"""update w/h for address for selected type ==>[cc,co,plant]"""
	if doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		make_warehouse(doc)
	

@frappe.whitelist()
def after_install():

	create_supplier_type()
	create_translation()



def create_translation():
	"""
	Made Translation for Material Request and Village Level Collections
	"""
	if not frappe.db.get_value("Translation", {"source_name":"Material Request"}, "name"):
		mr_translation = frappe.new_doc("Translation")
		mr_translation.language = "en"
		mr_translation.source_name = "Material Request"
		mr_translation.target_name = "Material Indent"
		mr_translation.save()

	if not frappe.db.get_value("Translation", {"source_name":"Village Level Collection Centre"}, "name"):
		mr_translation = frappe.new_doc("Translation")
		mr_translation.language = "en"
		mr_translation.source_name = "Village Level Collection Centre"
		mr_translation.target_name = "Dairy Cooperative Society"
		mr_translation.save()

	if not frappe.db.get_value("Translation", {"source_name":"Camp Office"}, "name"):
		mr_translation = frappe.new_doc("Translation")
		mr_translation.language = "en"
		mr_translation.source_name = "Camp Office"
		mr_translation.target_name = "P&I"
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
	if not frappe.db.exists('Supplier Type', "General"):
		supp_doc = frappe.new_doc("Supplier Type")
		supp_doc.supplier_type = "General"
		supp_doc.save()


def item_query(doctype, txt, searchfield, start, page_len, filters):

	item_groups = [str('Cattle feed'), str('Mineral Mixtures'), str('Medicines'), str('Artificial Insemination Services'),
		str('Veterinary Services'), str('Others/Miscellaneous'),str('Milk & Products')]
	return frappe.db.sql("""select name from tabItem where item_group in {0}""".format(tuple(item_groups)))

	
def on_submit_pr(doc,method=None):

	submit_dn(doc)
	# validate_qty_against_mi(doc)
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

			pi = make_pi(doc,is_camp_office=True) 	#Purchase Invoice @VLCC use case 1
			si = make_si(dn_doc,pi) 	#Sales Invoice @CO use case 1
			frappe.db.set_value("Purchase Invoice",pi,"sales_invoice",si)


def make_si(dn,pi):
	"""Make auto sales invoice on submit of DN @Camp (DN gets submit on submit of PR)"""
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
	accounts = frappe.db.get_value("Address",{"name":co},["income_account","expense_account","stock_account"],as_dict=1)

	si = frappe.new_doc("Sales Invoice")
	si.customer = dn.customer
	si.company = dn.company
	si.purchase_invoice = pi
	si.selling_price_list = "LCOS" if frappe.db.get_value("Price List","LCOS") else "GTCOS"
	si.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
	if dn.taxes_and_charges:
		si.taxes_and_charges = get_taxes_and_charges_template(si, dn.taxes_and_charges)
	for item in dn.items:
		si.append("items",
			{
				"qty":item.qty,
				"item_code": item.item_code,
				"rate": item.rate,
				"amount": item.amount,
				"warehouse": item.warehouse,
				"cost_center": item.cost_center,
				"delivery_note": dn.name,
				"income_account": accounts.get('income_account')
			})
	si.selling_price_list = dn.selling_price_list#get_selling_price_list(si, is_camp_office=True)
	si.remarks = "[#"+accounts.get('income_account')+"#]" if accounts.get('income_account') else "" 
	si.flags.ignore_permissions = True
	si.save()
	si.submit()
	return si.name

def make_pi(doc,is_camp_office):
	"""Make auto PI on submit of PR @VLCC"""

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	if user_doc.get('operator_type') == 'VLCC':
		pi = frappe.new_doc("Purchase Invoice")
		pi.supplier = doc.supplier
		pi.company = doc.company
		pi.camp_office = co if is_camp_office == True else ""
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
		if doc.taxes_and_charges:
			pi.taxes_and_charges = get_taxes_and_charges_template(pi, doc.taxes_and_charges)
		pi.buying_price_list = doc.buying_price_list
		pi.flags.ignore_permissions = True
		pi.save()
		pi.submit()
		return pi.name


def make_pi_against_localsupp(po_doc,pr_doc):
	"""Make PI for CO(dairy) local supplier @CO Use case 2"""

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
	accounts = frappe.db.get_value("Address",{"name":co},["income_account","expense_account","stock_account"],as_dict=1)

	pi = frappe.new_doc("Purchase Invoice")
	pi.supplier = po_doc.supplier
	pi.company = po_doc.company
	pi.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
	if po_doc.taxes_and_charges:
			pi.taxes_and_charges = get_taxes_and_charges_template(pi, po_doc.taxes_and_charges)
	for row_ in pr_doc.items:
		pi.append("items",
			{
				"qty":row_.qty,
				"item_code": row_.item_code,
				"rate": frappe.db.get('Item Price',{'name':row_.item_code,'buying':'1','company':po_doc.company,'price_list':po_doc.buying_price_list},'rate'),
				"purchase_order": po_doc.name,
				"expense_account":accounts.get('expense_account')
			})
	pi.buying_price_list = "LCOB"+"-"+co if frappe.db.get_value("Price List","LCOB"+"-"+co ,"name") else "GTCOB"#get_buying_price_list(pi, is_camp_office=True) #"LCOB" if frappe.db.get_value("Price List","LCOB") else "GTCOB"#get_buying_price_list(pi, is_camp_office=True)
	pi.remarks = "[#"+accounts.get('expense_account')+"#]" if accounts.get('expense_account') else ""
	return pi

def validate_qty_against_mi(doc):
	"""update Material Request Status mapped with delivery Note"""

	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC' and not doc.is_new():
		delivered_qty = 0

		dn_value = frappe.db.sql("""select parent from `tabDelivery Note Item` where purchase_receipt = '{0}' """.format(doc.name),as_dict=1)

		if dn_value:
			material_req_list = frappe.db.sql("""select sum(qty) as qty_sum, material_request from `tabDelivery Note Item` 
				where parent = '{0}' group by material_request""".format(dn_value[0].get('parent')),as_dict=1)
			
			for row in material_req_list:
				material_request_updater = frappe.get_doc("Material Request",row.get('material_request'))
				mr_qty = get_material_req_qty(material_request_updater)
				
				delivery_note = frappe.get_doc("Delivery Note",dn_value[0].get('parent'))
				for data in material_request_updater.items:
					for row in delivery_note.items:
						if data.item_code == row.item_code:
							data.completed_dn += row.qty
							data.new_dn_qty = data.qty - data.completed_dn
							delivered_qty += data.completed_dn

				if mr_qty > delivered_qty:
					material_request_updater.per_delivered = 99.99
					material_request_updater.set_status("Partially Delivered")
					material_request_updater.save()
				elif mr_qty == delivered_qty:
					material_request_updater.per_delivered = 100
					material_request_updater.set_status("Delivered")
					material_request_updater.save()


def get_material_req_qty(doc):
	"""count total quantity for specific MI"""
	
	total_qty =0.0
	for row in doc.items:
		total_qty += row.qty
	return total_qty

def check_if_dropship(doc):
	"""If dropship is checked on PO at Camp level of respective MR"""

	mr_list = []
	conditions = ""
	dairy = frappe.db.get_value("Company",{"is_dairy":1},"name")
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
	accounts = frappe.db.get_value("Address",{"name":co},["income_account","expense_account","stock_account"],as_dict=1)

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

				pi_name = make_pi(doc,is_camp_office=False)			#Purchase Invoice @VLCC in use case 2

				for data in set(po_data):
					po_doc = frappe.get_doc("Purchase Order",data)

					pi = make_pi_against_localsupp(po_doc,doc)		#Purchase Invoice @CO in use case 2

					if po_doc.is_dropship == 1:
						si = frappe.new_doc("Sales Invoice")
						si.customer = doc.company
						si.purchase_invoice = pi_name
						si.company = frappe.db.get_value("Company",{"is_dairy":1},"name")
						si.camp_office = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")
						if doc.taxes_and_charges:
							si.taxes_and_charges = get_taxes_and_charges_template(si, doc.taxes_and_charges)
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
									"warehouse": frappe.db.get_value("Address",{"name":po_doc.camp_office},"warehouse"),
									"income_account": accounts.get('income_account')
								})
				si.selling_price_list = "LCOS" +"-"+co if frappe.db.get_value("Price List","LCOS"+"-"+co ,"name") else "GTCOS"#get_selling_price_list(si, is_vlcc=True)
				si.remarks = "[#"+accounts.get('income_account')+"#]" if accounts.get('income_account') else ""
				si.flags.ignore_permissions = True  		#Sales Invoice @CO in use case 2
				si.save()
				si.submit()
				frappe.db.set_value("Purchase Invoice",pi_name,"sales_invoice",si)
				
				if pi:
					pi.flags.ignore_permissions = True  		#Purchase Invoice @CO in use case 2
					pi.save()
					pi.submit()

				mi_status_update(doc)


def mi_status_update(doc):
	
	item_doc = "Purchase Receipt Item" if doc.doctype == "Purchase Receipt" else "Delivery Note Item"
	delivered_qty = 0.0

	material_req_list = frappe.db.sql("""select sum(qty) as qty_sum, material_request from `tab{0}` 
				where parent = '{1}' group by material_request""".format(item_doc, doc.name),as_dict=1)

	for row in material_req_list:
		if row.get('material_request'):
			mi = frappe.get_doc("Material Request",row.get('material_request'))
			for data in mi.items:
				for i in doc.items:
					if data.item_code == i.item_code and data.parent == i.material_request:
						data.completed_dn += i.qty
			
			mi.flags.ignore_permissions = True
			mi.save()

			all_delivered = True
			for i in mi.items:
				if i.qty != i.completed_dn:
					all_delivered = False
			mi_status = "Delivered" if all_delivered else "Partially Delivered"
			per_delivered = 100 if all_delivered else 99.99
			mi.per_delivered = per_delivered
			mi.set_status(status=mi_status)
			mi.flags.ignore_permissions = True
			mi.flags.ignore_validate_update_after_submit = True
			mi.save()

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

	elif frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC':
		pr_qty = 0.0
		mr_qty = 0.0
		for item in doc.items:
			if item.material_request:
				material_request = frappe.get_doc("Material Request",item.material_request)
				for i in material_request.items:
					if i.item_code == item.item_code:
						qty = i.qty - i.completed_dn
						mr_qty += qty
				pr_qty += item.qty 

		if mr_qty and pr_qty > mr_qty:
			frappe.throw("Quantity should not be greater than Requested Qty")

# def qty_computation(mr):
	
# 	total_qty =0.0
# 	for row in mr.items:
# 		total_qty += row.new_dn_qty
# 	return total_qty


def make_so_against_vlcc(doc,method=None):

	if frappe.db.get_value("User",frappe.session.user,"operator_type") == 'VLCC' and \
		frappe.db.get_value("Customer",doc.customer,"customer_group") == 'Farmer':

		vlcc = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"camp_office")
		so = frappe.new_doc("Sales Order")
		so.company = frappe.db.get_value("Company",{"is_dairy":1},"name")
		so.customer = doc.company
		if doc.taxes_and_charges:
				so.taxes_and_charges = get_taxes_and_charges_template(so, doc.taxes_and_charges)
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

	mi_status_update(doc)

def set_co_warehouse_pr(doc,method=None):

	doc.posting_time = now_datetime().strftime('%H:%M:%S')

	branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type"],as_dict=1)
	if branch_office.get('operator_type') == 'Camp Office':
		if doc.items:
			for item in doc.items:
				if not item.delivery_note:
					item.warehouse = frappe.db.get_value("Address",branch_office.get('branch_office'),"warehouse")
					if item.rejected_qty:
						warehouse = frappe.db.get_value("Address",branch_office.get('branch_office'),["warehouse","rejected_warehouse"],as_dict=1)
						item.rejected_warehouse = warehouse.get('rejected_warehouse') if warehouse.get('rejected_warehouse') else warehouse.get('warehouse')
	if branch_office.get('operator_type') == 'VLCC':
		if doc.items:
			vlcc_wr = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},["warehouse","rejected_warehouse"],as_dict=1)
			co = frappe.db.get_value("Village Level Collection Centre",{"name":doc.company},"camp_office")

			for item in doc.items:
				item.warehouse = vlcc_wr.get('warehouse')
				if item.rejected_qty:
					item.rejected_warehouse = vlcc_wr.get('rejected_warehouse')
				if not doc.flags.ignore_material_price:
					if item.material_request:
						doc.buying_price_list = "LCOVLCCB"+"-"+co if frappe.db.get_value("Price List","LCOVLCCB"+"-"+co) else "GTCOVLCCB"
					elif item.delivery_note:
						doc.buying_price_list = "LCOVLCCB"+"-"+co if frappe.db.get_value("Price List","LCOVLCCB"+"-"+co) else "GTCOVLCCB"
					else:
						doc.buying_price_list = "LVLCCB-"+doc.company if frappe.db.get_value("Price List","LVLCCB"+"-"+doc.company) else "GTVLCCB"



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

def add_config_settings(args=None):
	try:
		add_values(args)
		add_dairy_language(args)
		create_item_group()
	except Exception,e:
		make_dairy_log(title="Config settings Failed",method="add_config_settings", status="Error",
		data = args, message=e, traceback=frappe.get_traceback())	

def add_values(args=None):
	dairy_configuration = frappe.get_doc("Dairy Configuration")
	dairy_configuration.company = args.get('company_name')
	dairy_configuration.first_name = args.get('full_name')
	dairy_configuration.email_id = args.get('email')
	dairy_configuration.is_dropship = args.get('is_dropship')
	dairy_configuration.save(ignore_permissions=True)

def add_dairy_language(args):
	language = frappe.new_doc("Language")
	language.language_code = "dcl"
	language.language_name = "Dairy"
	language.based_on = "en"
	language.save(ignore_permissions=True)
	set_dairy_language(language.language_code,args.get('email'))

def set_dairy_language(language,email_id):
	frappe.db.sql("""update `tabUser` SET language= '{0}' WHERE email = '{1}' """.format(language,email_id))
	# system_setting = frappe.get_doc("System Settings","System Settings")
	# system_setting.language = language
	# system_setting.save(ignore_permissions=True)

def create_item_group():

	item_groups = ['Cattle feed', 'Mineral Mixtures', 'Medicines', 'Artificial Insemination Services',
		'Veterinary Services', 'Others/Miscellaneous','Milk & Products', 'Stationary']
	for i in item_groups:
		if not frappe.db.exists('Item Group',i):
			item_grp = frappe.new_doc("Item Group")
			item_grp.parent_item_group = "All Item Groups"
			item_grp.item_group_name = i
			item_grp.insert()
	create_customer_group()
	create_item()


def create_item():
	for i in ['Milk Incentives', 'Loan Emi', 'Advance Emi', 'COW Milk', 'BUFFALO Milk']:
		if not frappe.db.exists("Item",i):
			item_doc = frappe.new_doc("Item")
			item_doc.item_code = i
			item_doc.item_group = "Others/Miscellaneous" if i in ['Milk Incentives', 'Loan Emi', 'Advance Emi'] else 'Milk & Products'
			item_doc.flags.ignore_permissions = True
			item_doc.flags.ignore_mandatory = True
			item_doc.save()

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
			purchase_rec.is_delivery = 1
			purchase_rec.supplier =  branch_office.get('branch_office')
			purchase_rec.company = doc.customer
			purchase_rec.base_in_words = money_in_words(doc.base_rounded_total,doc.currency)
			purchase_rec.buying_price_list = get_buying_price_list(purchase_rec, is_camp_office=True) #"LCOVLCCB" if frappe.db.get_value("Price List","LVLCCB") else "GTCOVLCCB"
			for item in doc.items:
				purchase_rec.append("items",
					{
						"item_code": item.item_code,
						"item_name": item.item_code,
						"description": item.item_code,
						"uom": item.uom,
						"qty": item.qty,
						"received_qty":item.qty,
						"rate":item.rate,
						"amount": item.amount,
						"delivery_note":doc.name,
						"warehouse": frappe.db.get_value("Village Level Collection Centre",{"name":doc.customer},"warehouse")
					}
				)
			if doc.taxes_and_charges:
				purchase_rec.taxes_and_charges = get_taxes_and_charges_template(purchase_rec, doc.taxes_and_charges)
			purchase_rec.flags.ignore_permissions = True
			purchase_rec.save()
			for item in doc.items:
				item.purchase_receipt = purchase_rec.name
			doc.save()

def set_company(doc, method):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	if user_doc.get('operator_type') == "VLCC" and doc.supplier_type in ["VLCC Local"]:
		doc.company = user_doc.get('company')

def mr_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	vlcc = frappe.db.get_values("Village Level Collection Centre",{"camp_office":user_doc.get('branch_office')},"name",as_dict=1)
	vlcc.append({'name':frappe.db.get_value("Company",{'is_dairy':1},'name')}) # added by khushal please correct it
	if user_doc.get('operator_type') == "VLCC":
		return """(`tabMaterial Request`.company = '{0}')""".format(user_doc.get('company'))

	elif user_doc.get('operator_type') == "Camp Office":
		company = ['"%s"'%comp.get('name') for comp in vlcc]
		if company:
			return """`tabMaterial Request`.company in  ({company})""".format(company=','.join(company))
		else:
			return """`tabMaterial Request`.company = 'Guest' """

	elif user_doc.get('operator_type') == "Chilling Centre":
		return """`tabMaterial Request`.owner = '{0}' """.format(frappe.session.user)


def pr_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	if user_doc.get('operator_type') == "VLCC":
		return """(`tabPurchase Receipt`.company = '{0}')""".format(user_doc.get('company'))

	elif user_doc.get('operator_type') == "Camp Office":
		pr_nos = get_pr_from_warehouse_ref(user_doc.get('branch_office'))
		if pr_nos:
			query = """`tabPurchase Receipt`.name in {0}""".format(pr_nos)
		else:
			query = "1=2"
		return query

	elif user_doc.get('operator_type') == "Chilling Centre":
		#query = "`tabPurchase Receipt`.owner = '{0}'".format(frappe.session.user)
		pr_nos = get_pr_from_warehouse_ref(user_doc.get('branch_office'))
		if pr_nos:
			query = """`tabPurchase Receipt`.name in {0}""".format(pr_nos)
		else:
			query = "1=2"
		return query

def get_pr_from_warehouse_ref(branch_office):
	# check warehouse in PR Item table & return distinct PR
	warehouse = frappe.db.get_value("Address",branch_office , "warehouse")
	pr_list = frappe.db.get_all("Purchase Receipt Item", {"warehouse": warehouse}, "distinct parent")
	pr_nos = ''
	if pr_list:
		pr_nos = "(" + ",".join([ "'{0}'".format(pr.get('parent')) for pr in pr_list ])  +")"
	return pr_nos

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

	elif user_doc.get('operator_type') == "Camp Office":
		query = """`tabPurchase Invoice`.camp_office = '{0}'""".format(user_doc.get('branch_office'))
		pi_nos = get_pi_from_exp_head_ref(user_doc.get('branch_office'))
		if pi_nos:
			query += """ or `tabPurchase Invoice`.name in {0} """.format(pi_nos)
		return query

	elif user_doc.get('operator_type') == "Chilling Centre":
		#query = """`tabPurchase Invoice`.owner = '{0}'""".format(frappe.session.user) 
		pi_nos = get_pi_from_exp_head_ref(user_doc.get('branch_office'))
		if pi_nos:
			query = """`tabPurchase Invoice`.name in {0}""".format(pi_nos)
		else:
			query = "1=2"
		return query

def get_pi_from_exp_head_ref(branch_office):
	# check expense_head in PI Item and return distinct PI
	exp_head = frappe.db.get_value("Address", branch_office, "expense_account")
	print "$$$$$$$$$$$$$$",exp_head,branch_office
	pi_list = frappe.db.get_all("Purchase Invoice Item", {"expense_account": exp_head}, "distinct parent")
	print pi_list
	pi_nos = ''
	if pi_list:
		pi_nos = "(" + ",".join([ "'{0}'".format(pi.get('parent')) for pi in pi_list ])  +")"
	return pi_nos

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

	if user_doc.get('operator_type') == "Vet AI Technician":
		return """(`tabSales Invoice`.owner = '{0}')""".format(frappe.session.user)

''' 
	Farmer Permission query condition 
'''
def farmer_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabFarmer`.vlcc_name = '{0}')""".format(user_doc.get('company'))
	elif user_doc.get('operator_type') == "Vet AI Technician":
		return """(`tabFarmer`.vlcc_name = '{0}')""".format(user_doc.get('company'))


def vlcc_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabVillage Level Collection Centre`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabVillage Level Collection Centre`.name = '{0}')""".format(user_doc.get('company'))

	if user_doc.get('operator_type') == "Vet AI Technician":
		return """(`tabVillage Level Collection Centre`.name = '{0}')""".format(user_doc.get('company'))

	if user_doc.get('operator_type') == 'Chilling Centre':
		return """(`tabVillage Level Collection Centre`.chilling_centre = '{0}')""".format(user_doc.get('branch_office'))

def fmrc_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabFarmer Milk Collection Record`.associated_vlcc = '{0}')""".format(user_doc.get('company'))

def vmcr_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	vlcc = frappe.db.get_values("Village Level Collection Centre",{"camp_office":user_doc.get('branch_office')},"name",as_dict=1)

	if user_doc.get('operator_type') == "Camp Office":
		company = ['"%s"'%comp.get('name') for comp in vlcc]
		if company:
			return """`tabVlcc Milk Collection Record`.associated_vlcc in  ({company})""".format(company=','.join(company))
		else:
			return """`tabVlcc Milk Collection Record`.associated_vlcc = 'Guest' """

	if user_doc.get('operator_type') == "Chilling Centre":
		cc_centre_id = frappe.db.get_value("Address", user_doc.get('branch_office'), "centre_id")
		return """`tabVlcc Milk Collection Record`.societyid = '{0}'""".format(cc_centre_id)

def pe_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	vlcc = frappe.db.get_values("Village Level Collection Centre",{"camp_office":user_doc.get('branch_office')},"name",as_dict=1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabPayment Entry`.company = '{0}')""".format(user_doc.get('company'))

	if user_doc.get('operator_type') == "Camp Office":
		return """(`tabPayment Entry`.camp_office = '{0}')""".format(user_doc.get('branch_office'))

	if user_doc.get('operator_type') == "Vet AI Technician":
		return """(`tabPayment Entry`.owner = '{0}')""".format(frappe.session.user)

def supplier_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	dairy_mgr = frappe.db.sql("select distinct u.name from `tabUser` u left join `tabHas Role` r on r.parent = u.name where r.role = 'Dairy Manager'")
	dairy_mgr = "(" + ",".join([ "'{0}'".format(d[0]) for d in dairy_mgr ]) + ")"
	if user_doc.get('operator_type') == "Camp Office":

		supplier_list = frappe.db.sql("""select s.name as supp,p.company from `tabSupplier` s, `tabParty Account` 
						p where (p.parent = s.name and s.supplier_type in ('Dairy Local','Vlcc Type') and
						p.company = '{0}' and s.camp_office = '{1}') or (s.supplier_type = 'Dairy Local' and s.owner in {2})
						group by s.name""".format(user_doc.get('company'),user_doc.get('branch_office'), dairy_mgr),as_dict=1)

		supp = [ '"%s"'%sup.get("supp") for sup in supplier_list ]
		if supp:
			return """tabSupplier.name in ({supp})"""\
				.format(supp=','.join(supp))
		else:
			return """tabSupplier.supplier_type = 'Guest' """
		

	elif user_doc.get('operator_type') == "VLCC":
		supplier_list = frappe.db.sql(
					"""
							select s.name as supp,p.company
						from 
							`tabSupplier` s, 
							`tabParty Account` p 
						where 
						p.parent = s.name and s.supplier_type in 
						('Dairy Type','Farmer','VLCC Local','General') and 
						p.company = '{0}' group by s.name
					""".format(user_doc.get('company')),as_dict=1)

		supp = [ '"%s"'%sup.get("supp") for sup in supplier_list ]
		if supp:
			return """tabSupplier.name in ({supp})"""\
				.format(supp=','.join(supp))
		else:
			return """tabSupplier.supplier_type = 'Guest' """


def customer_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "Camp Office":

		customer_list = frappe.db.sql("""select c.name as cust,c.customer_group from `tabCustomer` c, `tabParty Account` p where p.parent = c.name and 
					p.company = %s and c.customer_group in ('Vlcc') and c.camp_office = %s group by c.name""",(user_doc.get('company'),user_doc.get('branch_office')),as_dict=1)

		customer = [ '"%s"'%cust.get("cust") for cust in customer_list ]

		if customer:
			return """tabCustomer.name in ({customer})"""\
			.format(customer=','.join(customer))
		else:
			return """tabCustomer.customer_group = 'Guest' """

	if user_doc.get('operator_type') == "VLCC":
		customer_list = frappe.db.sql("""select c.name as cust from `tabCustomer` c, `tabParty Account` p where p.parent = c.name and 
					p.company = '{0}' and c.customer_group in ('Farmer','Dairy','Vlcc Local Customer') group by c.name""".format(user_doc.get('company')),as_dict=1)

		customer = [ '"%s"'%cust.get("cust") for cust in customer_list ]

		if customer:
			return """tabCustomer.name in ({customer})"""\
			.format(customer=','.join(customer))
		else:
			return """tabCustomer.customer_group = 'Guest' """

def user_permissions(user):

	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user=="Administrator":
		return ""
	elif "Dairy Manager" in roles:

		user_ = frappe.db.sql("""select user.name from tabUser user, `tabHas Role` user_role where 
			user_role.role = "Dairy Operator" and 
			user_role.parent = user.name and 
			user.enabled and user.name not in ('Guest', 'Administrator')""",as_dict=True)

		user_list = ['"%s"'%data.name for data in user_]

		if user_list:
			return """tabUser.name = '%(user)s' or  tabUser.name in ({user_list})"""\
				.format(user_list=','.join(user_list))
		else:
			return """tabUser.name = '%(user)s'"""

	elif "Dairy Operator" in roles:

		return """tabUser.name = '%(user)s'"""

	elif "Camp Manager" in roles:
	
		user_ = frappe.db.sql("""select user.name from tabUser user, `tabHas Role` user_role where 
			user_role.role = "Camp Operator" and 
			user.branch_office = %s and user_role.parent = user.name and 
			user.enabled and user.name not in ('Guest', 'Administrator')""",(user_doc.get('branch_office')),as_dict=True)

		user_list = ['"%s"'%data.name for data in user_]
		
		if user_list:
			return """tabUser.name = '%(user)s' or  tabUser.name in ({user_list})"""\
				.format(user_list=','.join(user_list))
		else:
			return """tabUser.name = '%(user)s'"""

	elif "Camp Operator" in roles:
		return """tabUser.name = '%(user)s'"""

	elif "Vlcc Manager" in roles:

		user_ = frappe.db.sql("""select user.name as name from tabUser user,  `tabHas Role` user_role 
				where user_role.role in ("Vlcc Operator") and  user_role.parent = user.name and user.company = %s and  
				user.enabled and user.name not in ("Guest", "Administrator");""",(user_doc.get('company')),as_dict=1)

		vet = frappe.db.sql("""select email from `tabVeterinary AI Technician` where
			 vlcc = %s""",(user_doc.get('company')),as_dict=True)

		user_list = ['"%s"'%data.name for data in user_]

		vet_list = ['"%s"'%data.email for data in vet]
		
		if user_list and vet_list:
			return """tabUser.name = '%(user)s' or  tabUser.name in ({user_list}) or tabUser.name in ({vet_list})"""\
				.format(user_list=','.join(user_list),vet_list=','.join(vet_list))
		elif user_list and not vet_list:
			return """tabUser.name = '%(user)s' or  tabUser.name in ({user_list}) """\
				.format(user_list=','.join(user_list))
		elif vet_list and not user_list:
			return """tabUser.name = '%(user)s' or  tabUser.name in ({vet_list}) """\
				.format(vet_list=','.join(vet_list))
		else:
			return """tabUser.name = '%(user)s'"""

	elif "Vlcc Operator" in roles:
		return """tabUser.name = '%(user)s'"""

	elif "Vet/AI Technician" in roles:
		return """tabUser.name = '%(user)s'"""

	elif has_common(["Chilling Center Operator", "Chilling Center Manager", "Vet/AI Technician"], roles):
		return """tabUser.name = '%(user)s'"""

def item_price_permission(user):

	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	lcob = "LCOB"+"-"+user_doc.get('branch_office') if user_doc.get('branch_office') else ""
	lcos = "LCOS" +"-"+user_doc.get('branch_office') if user_doc.get('branch_office') else ""

	lvlccb = "LVLCCB" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lfs = "LFS" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lcs = "LCS" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lcovlccb = "LCOVLCCB" +"-"+co if co else ""


	if user != 'Administrator' and ('Camp Manager' in roles or 'Camp Operator' in roles):
		return """`tabItem Price`.price_list in ('GTCOB','GTCOS','{0}','{1}') """.format(lcob,lcos)
	elif user != 'Administrator' and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
		return """`tabItem Price`.price_list in ('GTVLCCB','GTFS','GTCS','GTCOVLCCB','{0}','{1}','{2}','{3}') """.format(lvlccb,lfs,lcs,lcovlccb)
	elif user != 'Administrator' and 'Vet/AI Technician' in roles:
		return """`tabItem Price`.price_list in ('GTFS','{0}') """.format(lfs)
	elif user != 'Administrator' and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
		return """`tabItem Price`.price_list in ('GTVLCCB','GTFS','GTCS','GTCOVLCCB','GTCOB','GTCOS') """

def price_list_permission(user):

	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	lcob = "LCOB"+"-"+user_doc.get('branch_office') if user_doc.get('branch_office') else ""
	lcos = "LCOS" +"-"+user_doc.get('branch_office') if user_doc.get('branch_office') else ""

	lvlccb = "LVLCCB" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lfs = "LFS" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lcs = "LCS" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lcovlccb = "LCOVLCCB" +"-"+co if co else ""


	if user != 'Administrator' and ('Camp Manager' in roles or 'Camp Operator' in roles):
		return """`tabPrice List`.name in ('GTCOB','GTCOS','{0}','{1}','Standard Buying','Standard Selling')""".format(lcob,lcos)
	elif user != 'Administrator' and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
		return """`tabPrice List`.name in ('GTVLCCB','GTFS','GTCS','GTCOVLCCB','{0}','{1}','{2}','{3}','Standard Buying','Standard Selling') """.format(lvlccb,lfs,lcs,lcovlccb)
	elif user != 'Administrator' and 'Vet/AI Technician' in roles:
		return """`tabPrice List`.name in ('GTFS','{0}','Standard Buying','Standard Selling') """.format(lfs)
	elif user != 'Administrator' and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
		return """`tabPrice List`.name in ('GTVLCCB','GTFS','GTCS','GTCOVLCCB','GTCOB','GTCOS','Standard Buying','Standard Selling') """
	


def set_camp(doc, method):

	camp = frappe.db.get_value("Sales Invoice",doc.voucher_no,'camp_office')
	doc.camp_office = camp
	doc.flags.ignore_permissions = True


def set_supp_company(doc,method):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
	if (user_doc.get('operator_type') == "Camp Office" and doc.supplier_type == "Dairy Local") or (user_doc.get('operator_type') == "VLCC" and doc.supplier_type in ["VLCC Local", "General"]):
		doc.append("accounts",
			{
			"company": user_doc.get('company'),
			"account": frappe.db.get_value("Company",user_doc.get('company'), "default_payable_account")
			})
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.save()


def company_permission(user):
	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabCompany`.name = '{0}')""".format(user_doc.get('company'))
	elif user_doc.get('operator_type') == "Vet AI Technician":
		return """(`tabCompany`.name = '{0}')""".format(user_doc.get('company'))
	elif user != 'Administrator' and ('Camp Manager' in roles or 'Camp Operator' in roles):
		vlcc_list = frappe.get_all("Village Level Collection Centre", {"camp_office":user_doc.get('branch_office')}, 'name')
		vlcc_list = [ '"%s"'%vlcc.get("name") for vlcc in vlcc_list ]
		if vlcc_list:
			return """tabCompany.name in ({vlcc_list})"""\
				.format(vlcc_list=','.join(vlcc_list))
		else:
			return """tabCompany.name = 'Guest' """

def warehouse_permission(user):

	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)

	if user_doc.get('operator_type') == "VLCC":
		return """(`tabWarehouse`.company = '{0}')""".format(user_doc.get('company'))
	elif user_doc.get('operator_type') == "Vet AI Technician":
		return """(`tabWarehouse`.company = '{0}')""".format(user_doc.get('company'))

def set_chilling_wrhouse(doc, method):
	branch_office = frappe.db.get_value("User",frappe.session.user,["operator_type","company","branch_office"],as_dict=1)
	if branch_office.get('operator_type') == 'Chilling Centre':
		if doc.items:
			for item in doc.items:
				item.original_qty = item.qty
				item.warehouse = frappe.db.get_value("Address",{"name":branch_office.get('branch_office')},"warehouse")


def validate_dn(doc,method):
	for item in doc.items:
		warehouse_qty = get_balance_qty_from_sle(item.item_code,item.warehouse)
		if item.material_request:
			mi=frappe.get_doc("Material Request",item.material_request)
			if item.qty > warehouse_qty:
				frappe.throw(_("<b>Warehouse Insufficent Stock </b>"))
			else:
				for mi_items in mi.items:
					if item.item_code == mi_items.item_code:
						if item.qty > (mi_items.qty - mi_items.completed_dn):
							frappe.throw(_("<b>Dispatch Quantity</b> should not be greater than <b>Requested Quantity</b>"))


def item_permissions(user):
	
	roles = frappe.get_roles()
	operator_type = frappe.db.get_value("User",user,'operator_type')
	if operator_type == "Vet AI Technician":
		return """tabItem.item_group in ('Veterinary Services','Medicines')and tabItem.name not 
				in ('Advance Emi', 'Loan Emi', 'Milk Incentives') """
	elif operator_type == "Chilling Centre":
		return """tabItem.item_group = 'Stationary' and tabItem.name not 
				in ('Advance Emi', 'Loan Emi', 'Milk Incentives')"""
	elif operator_type == "VLCC":
		return """tabItem.item_group != 'Stationary' and tabItem.name not 
				in ('Advance Emi', 'Loan Emi', 'Milk Incentives')"""
	elif operator_type == "Camp Office":
		return """tabItem.name not in
		 ('Advance Emi', 'Loan Emi', 'Milk Incentives')"""

	elif user != 'Administrator' and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
		return """tabItem.name not in
		 ('Advance Emi', 'Loan Emi', 'Milk Incentives')"""