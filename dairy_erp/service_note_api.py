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
		if data.get('diagnosis') and data.get('items') and data.get('client_id'):
			sn_exist = frappe.db.get_value("Service Note", {"client_id": data.get('client_id')}, 'name')
			if not sn_exist:
				response_dict.update({"status": "success", "name": create_sn(data)})
			else:
				response_dict.update({"status": "success", "name": sn_exist})
		else:
			frappe.throw(_("Invalid Data, Please check data !"))

	
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


@frappe.whitelist()
def service_note_list():
	response_dict = {}
	try:
		sn_list = frappe.db.sql("""select name,status,posting_date,vlcc_name,farmer_id,case_details,discount_amount,grand_total,taxes_and_charges from `tabService Note` order by creation desc limit 10 """,as_dict=1)
		for row in sn_list:
			row.update({"items": frappe.db.sql("select item_code,item_name,qty,uom from `tabService Note Item` where parent = '{0}'".format(row.get('name')),as_dict=1)})
			if row.get('taxes_and_charges'):
				row.update({row.get('taxes_and_charges'): frappe.db.sql("""select charge_type,description,rate from `tabService Note Taxes` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
			row.update({"diagnosis": frappe.db.sql("""select disease,description from `tabDisease Child` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
		response_dict.update({"status":"success","data":sn_list})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict