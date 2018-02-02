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
def create_sv_nt(data):
	
	response_dict = {}
	data = json.loads(data)
	try:
		if data.get('diseases') and data.get('items') and data.get('client_id'):
			sn_exist = frappe.db.get_value("Service Note", {"client_id": data.get('client_id')}, 'name')
			if not sn_exist:
				response_dict.update({"status": "success", "name": create_sn(data)})
			else:
				response_dict.update({"status": "success", "name": sn_exist})
		else:
			frappe.throw(__("Invalid Data, Please check data !"))

	
	except Exception,e:
		utils.make_mobile_log(title="Sync failed for Data push",method="create_local_sale", status="Error",
			data = data, message=e, traceback=frappe.get_traceback())

		response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict


def create_sn(data):
	sn_obj = frappe.new_doc("Service Note")
	sn_obj.update(data)
	sn_obj.flags.ignore_permissions = True
	sn_obj.flags.ignore_mandatory = True
	sn_obj.insert()
	sn_obj.submit()
	
	return sn_obj.name