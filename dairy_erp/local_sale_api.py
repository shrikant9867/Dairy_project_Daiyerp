# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt
# Author Khushal Trivedi

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
from item_api import get_seesion_company_datails
from frappe import _
import api_utils as utils
import json


@frappe.whitelist()
def create_local_sale(data):
	response_dict = {}
	print data
	data = json.loads(data)
	try:
		if data.get('local_customer_or_farmer') and data.get('farmer') and data.get('items'):
			local_exist = frappe.db.get_value("Local Sale",{"client_id": data.get('client_id')}, 'name')
			print local_exist
			if not local_exist:
				response_dict.update({"status": "success", "name": create_ls(data)})
			else:
				response_dict.update({"status": "success", "name": local_exist})
		
	except Exception,e:
		utils.make_mobile_log(title="Sync failed for Data push",method="create_local_sale", status="Error",
			data = data, message=e, traceback=frappe.get_traceback())

		response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict

def create_ls(data):
	ls_obj = frappe.new_doc("Local Sale")
	ls_obj.local_customer_or_farmer = data.get('local_customer_or_farmer')
	ls_obj.farmer = data.get('farmer')
	ls_obj.client_id = data.get('client_id')
	for row in data.get('items'):
		ls_obj.append("items",
			{
				"item_code": row.get('item_code'),
				"uom": row.get('uom'),
				"qty": row.get('qty'),
				"rate": row.get('rate'),
				"conversion_factor":4.000
			}
		)
	ls_obj.flags.ignore_permissions = True
	ls_obj.flags.ignore_mandatory = True
	ls_obj.save()
	ls_obj.submit()
	return ls_obj.name


@frappe.whitelist()
def local_sale_list():
	response_dict = {}
	try:
		la_list = frappe.db.sql("""select status,local_customer_or_farmer,name,posting_date,farmer,effective_credit,cow_milk_quantity_farmer,buffalo_milk_qty_farmer,discount,taxes_and_charges from `tabLocal Sale` order by creation desc limit 10 """,as_dict=1)
		for row in la_list:
			row.update({"items": frappe.db.sql("select item_code,item_name,delivery_date, qty, rate,uom from `tabLocal Sales Item` where parent = '{0}'".format(row.get('name')),as_dict=1)})
			if row.get('taxes_and_charges'):
				row.update({row.get('taxes_and_charges'): frappe.db.sql("""select charge_type,description,rate from `tabPurchase Taxes and Charges` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
		response_dict.update({"status":"success","data":la_list})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict