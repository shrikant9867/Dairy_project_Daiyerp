
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
from frappe import _
import dairy_utils as utils
from item_api import get_seesion_company_datails
import requests
import json

@frappe.whitelist()
def create_po(data):
	response_dict, response_data = {}, []
	try:
		data_ = json.loads(data)
		if data_:
			if data_.get('client_id') and data_.get('supplier') and data_.get('schedule_date'):
				po_exist = frappe.db.get_value("Purchase Order",{"client_id":data_.get('client_id')}, 'name')
				if not po_exist:
					response_dict.update({"status": "success","name": make_po(data_)})
				else:
					response_dict.update({"status": "success", "name": po_exist})
			else:
				response_dict.update({"status":"error", "response":"client id, camp office , item are required "})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict

def make_po(data):
	po_obj = frappe.new_doc("Purchase Order")
	po_obj.update(data)
	po_obj.flags.ignore_permissions = True
	po_obj.insert()
	po_obj.submit()

	return po_obj.name

@frappe.whitelist()
def get_po_list():
	response_dict = {}

	try:
		po_list = frappe.db.sql("""select name,schedule_date,supplier,tc_name,terms,status from `tabPurchase Order` where company = '{0}' and status in ('To Receive and Bill') order by creation desc limit 10""".format(get_seesion_company_datails().get('company')),as_dict=1)
		for row in po_list:
			row.update({"items": frappe.db.sql("select item_code,item_name,uom,qty,rate from `tabPurchase Order Item` where parent = '{0}'".format(row.get('name')),as_dict=1)})
		response_dict.update({"status":"success","data":po_list})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict	