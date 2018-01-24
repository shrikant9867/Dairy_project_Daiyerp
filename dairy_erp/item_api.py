# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt
# Author Khushal Trivedi

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
from frappe import _
import api_utils as utils
import requests
import json
from erpnext.stock.stock_balance import get_balance_qty_from_sle

@frappe.whitelist()
def get_items():
	"""Mobile API's common to sell and purchase 
	"""
	
	response_dict = frappe.db.sql("""select name as item_code,item_name,description,weight_uom from `tabItem` where 
		item_group in ('Cattle feed', 'Mineral Mixtures', 'Medicines', 
		'Artificial Insemination Services') and is_stock_item=1 and disabled =0""",as_dict = 1)
	for row in response_dict:
		try:
			row.update({"qty": get_item_qty(row.get('name')),"uom":frappe.db.sql("select uom,conversion_factor from `tabUOM Conversion Detail` where parent = '{0}'".format(row.get('item_code')),as_dict=1)})

		except Exception,e:
			utils.make_mobile_log(title="Sync failed for Data push",method="get_items", status="Error",
			data = row.get('name'), message=e, traceback=frappe.get_traceback())
			response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict


def get_item_qty(item):
	
	user_doc = frappe.get_doc("User",frappe.session.user)
	warehouse = frappe.db.get_value("Village Level Collection Centre",user_doc.company,'warehouse')
	return get_balance_qty_from_sle(item, warehouse)


@frappe.whitelist()
def get_masters():
	response_dict = {}
	try:
		if frappe.session.user != "Administrator":
			vlcc_details = get_camp_office()
			response_dict.update({
				"items":get_items(),
				# "uom": get_uom(),
				"camp_office": vlcc_details.get('camp_office'),
				"vlcc": vlcc_details.get('name'),
				"farmer": get_farmer(),
				"suppliers": get_supplier(),
				"terms_and_condition": terms_condition(),
				"sales_taxes": taxes_templates(),
				"purchase_taxes":pr_taxes_templates()
			})
		else:
			frappe.throw(_("User cannot be administrator"))
	except Exception,e:
			utils.make_mobile_log(title="Sync failed for Data push",method="get_items", status="Error",
			data = "", message=e, traceback=frappe.get_traceback())
			response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict	

def get_uom():
	return frappe.db.sql("select name from `tabUOM`",as_dict=1)

def get_camp_office():
	user_doc = frappe.get_doc("User",frappe.session.user)
	camp_office = frappe.db.get_value("Village Level Collection Centre",user_doc.company,['camp_office','name'],as_dict=1)
	return camp_office

def get_farmer():
	company = get_seesion_company_datails()
	return frappe.db.sql("""select name as id,full_name ,vlcc_name from `tabFarmer` where vlcc_name ='{0}'""".format(company.get('company')),as_dict =1)

def terms_condition():
	return frappe.db.sql("""select name,terms from `tabTerms and Conditions` where vlcc ='{0}'""".format(get_seesion_company_datails().get('company')),as_dict=1)

def get_supplier():
	supplier = frappe.db.sql("""select name from `tabSupplier` where supplier_type in ('VLCC Local','Dairy Type')""",as_dict=1)
	print supplier
	for row in supplier:
		update_supplier_value(row)
	return supplier

def taxes_templates():
	taxes_ =  frappe.db.sql(""" select name from `tabSales Taxes and Charges Template` where disabled =0 and company = '{0}'""".format(get_seesion_company_datails().get('company')),as_dict=1)
	for row in taxes_:
		row.update({"template":frappe.db.sql("""select charge_type,description,rate from `tabSales Taxes and Charges` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
	return taxes_

def get_seesion_company_datails():

	user_doc = frappe.get_doc("User",frappe.session.user)
	return {"company" : user_doc.company}

def pr_taxes_templates():
	taxes_ =  frappe.db.sql(""" select name from `tabPurchase Taxes and Charges Template` where disabled =0 and company = '{0}'""".format(get_seesion_company_datails().get('company')),as_dict=1)
	for row in taxes_:
		row.update({"template":frappe.db.sql("""select charge_type,description,rate from `tabPurchase Taxes and Charges` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
	return taxes_

def update_supplier_value(row):
	supplier_item_price = frappe.db.sql("select name from `tabSupplier Item Price` where branch_office = '{0}' and customer = '{1}'".format(row.get('name'),get_seesion_company_datails().get('company')),as_dict=1)
	print "_____________",supplier_item_price
	if supplier_item_price:
		row.update({"item_prices": frappe.db.sql("select item,price from `tabSupplier Item Price Child` where parent = '{0}'".format(supplier_item_price[0].get('name')),as_dict=1)})