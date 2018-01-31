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
			if not local_exist:
				print local_exist
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
	#ls_obj.local_customer_or_farmer = data.get('local_customer_or_farmer')
	ls_obj.update(data)
	ls_obj.flags.ignore_permissions = True
	ls_obj.flags.ignore_mandatory = True
	ls_obj.insert()
	ls_obj.submit()
	
	return ls_obj.name