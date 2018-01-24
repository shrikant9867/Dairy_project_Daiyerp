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
def get_mr_list(data):
	
	response_dict = {}
	try:
		mr_list = frappe.db.sql("""select name,schedule_date,camp_office from `tabMaterial Request` where company= '{0}' and status ='Pending' order by creation  desc limit 10""".format(get_seesion_company_datails().get('company')),as_dict=1)
		for row in mr_list:
			row.update({"items": frappe.db.sql("select item_code,item_name, qty from `tabMaterial Request Item` where parent = '{0}'".format(row.get('name')),as_dict=1)})
		response_dict.update({"status":"success","data":mr_list})
	except Exception,e:
			utils.make_mobile_log(title="Sync failed for Data push",method="get_items", status="Error",
			data = row.get('name'), message=e, traceback=frappe.get_traceback())
			response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict

@frappe.whitelist()
def create_mr(data):

	response_dict, response_data = {}, []
	try:
		data_ = json.loads(data)
		if data_:
			if data_.get('client_id') and data_.get('camp_office') and data_.get('schedule_date'):
				mr_exist = frappe.db.get_value("Material Request",{"client_id":data_.get('client_id')}, 'name')
				if not mr_exist:
					response_dict.update({"status": "success","name": make_mr(data_)})
				else:
					response_dict.update({"status": "success", "name": mr_exist})
			else:
				response_dict.update({"status":"error", "response":"client id, camp office , item are required "})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict


def make_mr(row):
	"""
	Material Request API same (DOM) w/h and company Indenting flow
	"""
	mr_doc = frappe.new_doc("Material Request")
	mr_doc.update(row)
	mr_doc.flags.ignore_permissions = True
	mr_doc.insert()
	mr_doc.submit()

	return mr_doc.name
