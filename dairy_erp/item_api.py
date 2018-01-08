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
	
	response_dict = frappe.db.sql("""select name,item_name,description from `tabItem` where 
		item_group in ('Cattle feed', 'Mineral Mixtures', 'Medicines', 
		'Artificial Insemination Services') and is_stock_item=1 and disabled =0""",as_dict = 1)
	for row in response_dict:
		try:
			row.update({"qty": get_item_qty(row.get('name'))})

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
		vlcc_details = get_camp_office()
		response_dict.update({"items":get_items(),"uom": get_uom(),"camp_office": vlcc_details.get('camp_office'), "vlcc": vlcc_details.get('name')})
	except Exception,e:
			utils.make_mobile_log(title="Sync failed for Data push",method="get_items", status="Error",
			data = row.get('name'), message=e, traceback=frappe.get_traceback())
			response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict	

def get_uom():
	return frappe.db.sql("select name from `tabUOM`",as_dict=1)

def get_camp_office():
	user_doc = frappe.get_doc("User",frappe.session.user)
	camp_office = frappe.db.get_value("Village Level Collection Centre",user_doc.company,['camp_office','name'],as_dict=1)
	return camp_office