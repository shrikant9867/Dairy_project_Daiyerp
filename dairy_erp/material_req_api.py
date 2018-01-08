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
import json


@frappe.whitelist()
def get_mr_list(data):
	
	response_dict = {}
	try:
		company = frappe.db.get_value("User", frappe.session.user, "company")
		if data == "Material Indent":
			response_dict = frappe.db.sql("""select itm.namectm.item_code , itm.schedule_date,itm.camp_office
				 			from `tabMaterial Request` itm,`tabMaterial Request Item` ctm where  
				 		ctm.parent=itm.name and itm.company='{0}'""".format(company),as_dict=1)
		else:
			response_dict.update({"status":"error","message":"data can be one of Material Indent, Delivery Note,Purchase Order"})
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
			for row in data_:
				try:
					mr_exist = frappe.db.get_value("Material Request",{"client_id":row.get('client_id')}, 'name')
					if not mr_exist:
						response_data.append({"status": "success","name": make_mr(row)})
					else:
						response_data.append({"status": "success", "name": mr_exist})

				except Exception,e:
					utils.make_mobile_log(title="Sync failed for Data push",method="create_mr", status="Error",
					data = data, message=e, traceback=frappe.get_traceback())
					response_data.append({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
		response_dict.update({"status":"success","data":response_data})
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
	mr_doc.submit()

	return mr_doc.name
