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
#from dairy_erp.customization.sales_invoice.sales_invoice import get_effective_credit

@frappe.whitelist()
def get_items():
	"""Mobile API's common to sell and purchase 
	"""
	
	response_dict = frappe.db.sql("""select name as item_code,item_name,description,standard_rate,stock_uom from `tabItem` where 
		item_group in ('Cattle feed', 'Mineral Mixtures', 'Medicines', 
		'Artificial Insemination Services','Milk & Products') and is_stock_item=1 and disabled =0""",as_dict = 1)
	for row in response_dict:
		try:
			row.update({"qty": get_item_qty(row.get('item_code')),"uom":frappe.db.sql("select um.uom,um.conversion_factor * i.standard_rate as rate from `tabUOM Conversion Detail` as um join `tabItem` as i on  um.parent = i.name where um.parent = '{0}'".format(row.get('item_code')),as_dict=1)})
			# row.get('uom').append({"uom": frappe.db.get_value('Item',row.get('item_code'),'stock_uom'),"rate": frappe.db.get_value('Item',row.get('item_code'), "standard_rate")})
		
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
				"purchase_taxes":pr_taxes_templates(),
				"diseases": get_diseases(),
				"total_cow_milk": get_milk_attr('COW Milk'),
				"total_buffalo_milk": get_milk_attr('BUFFALO Milk')
			})
		else:
			frappe.throw(_("User cannot be administrator"))
	except Exception,e:
			utils.make_mobile_log(title="Sync failed for Data push",method="get_items", status="Error",
			data = "", message=e, traceback=frappe.get_traceback())
			response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict	


def get_uom():
	#deprecated current requirement may be future aspect handy
	return frappe.db.sql("select name from `tabUOM`",as_dict=1)


def get_camp_office():
	user_doc = frappe.get_doc("User",frappe.session.user)
	camp_office = frappe.db.get_value("Village Level Collection Centre",user_doc.company,['camp_office','name'],as_dict=1)
	return camp_office


def get_farmer():
	company = get_seesion_company_datails()
	farmer = frappe.db.sql("""select name as id,full_name ,vlcc_name from `tabFarmer` where vlcc_name ='{0}'""".format(company.get('company')),as_dict =1)
	for row in farmer:
		row.update({"effective_credit": calculate_effective_credit(row.get('id'))})
	return farmer


def terms_condition():
	return frappe.db.sql("""select name,terms from `tabTerms and Conditions` where vlcc ='{0}'""".format(get_seesion_company_datails().get('company')),as_dict=1)


def get_supplier():
	supplier = frappe.db.sql("""select su.name,su.contact_no from `tabSupplier` as su join `tabParty Account` as pa on  pa.parent = su.name where supplier_type in ('VLCC Local','Dairy Type') and pa.company = '{0}'""".format(get_seesion_company_datails().get('company')),as_dict=1)
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
	return {"company" : user_doc.company,"branch_office":user_doc.branch_office,"operator_type":user_doc.operator_type}


def pr_taxes_templates():
	taxes_ =  frappe.db.sql(""" select name from `tabPurchase Taxes and Charges Template` where disabled =0 and company = '{0}'""".format(get_seesion_company_datails().get('company')),as_dict=1)
	for row in taxes_:
		row.update({"template":frappe.db.sql("""select charge_type,description,rate from `tabPurchase Taxes and Charges` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
	return taxes_


def update_supplier_value(row):
	"""supplier item price for different UOM per object """
	
	row.update({"items": frappe.db.sql("select  item_code,item_name,standard_rate,stock_uom from `tabItem`",as_dict=1)})
	for row in row.get('items'):
		#needful UOM respective supplier
		item_ = frappe.db.get_value("Item",row.get('item_code'),['stock_uom','standard_rate','description'],as_dict=1)
		row.update(
			{
				"uom": frappe.db.sql("select um.uom,um.conversion_factor * {0} as rate from `tabUOM Conversion Detail` as um join `tabItem` as i on  um.parent = i.name where um.parent = '{1}'".format(row.get('standard_rate'),row.get('item_code')),as_dict=1),
				
			}
		)
	


def get_diseases():
	return frappe.db.sql("""select name, description from `tabDisease`""",as_dict=1)


@frappe.whitelist()
def log_out():
	try:
		response_dict = {}
		frappe.local.login_manager.logout()
		frappe.db.commit()
		response_dict.update({"status":"Success", "message":"Successfully Logged Out"})
	except Exception, e:
		response_dict.update({"status":"Error", "error":e, "traceback":frappe.get_traceback()})

	return response_dict

@frappe.whitelist(allow_guest=True)
def forgot_password(user_id):
	try:
		response_dict = {}
		user = frappe.get_doc("User", user_id)
		user.validate_reset_password()
		user.reset_password(send_email=True)
		response_dict.update({"status":"Success", \
			"message":_("Password reset instructions have been sent to your email")})
	except frappe.DoesNotExistError:
		response_dict.update({"status":"Error", "message":_("User {0} does not exist").format(user_id)})
	except Exception, e:
		response_dict.update({"status":"Error", "message":e, "traceback":frappe.get_traceback()})

	return response_dict


def calculate_effective_credit(id_):
	from customization.sales_invoice.sales_invoice import get_effective_credit
	farmer_name = frappe.db.get_value("Farmer",id_,'full_name')
	return get_effective_credit(farmer_name)

def get_milk_attr(item):
	if item:
		user_doc = frappe.get_doc("User",frappe.session.user)
		warehouse = frappe.db.get_value("Village Level Collection Centre",user_doc.company,'warehouse')
		return get_balance_qty_from_sle(item, warehouse)
	else:
		frappe.throw(_("Item Does Not Exist"))