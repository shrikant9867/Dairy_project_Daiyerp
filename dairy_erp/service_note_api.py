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
def create_service_note(data):
	response_dict = {}
	data = json.loads(data)
	try:
		if data.get('items'):
			local_exist = frappe.db.get_value("Sales Invoice",{"client_id": data.get('client_id')}, 'name')
			if not local_exist:
				response_dict.update({"status": "success", "name": create_sn(data)})
			else:
				response_dict.update({"status": "success", "name": local_exist})
		
	except Exception,e:
		utils.make_mobile_log(title="Sync failed for Data push",method="create_service_note", status="Error",
			data = data, message=e, traceback=frappe.get_traceback())

		response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict


def create_sn(data):
	company = frappe.get_value("User",frappe.session.user,"company")
	sn_obj = frappe.new_doc("Sales Invoice")
	sn_obj.service_note = 1
	sn_obj.company = company
	sn_obj.debit_to = frappe.db.get_value("Company",sn_obj.company, 'default_receivable_account')
	customer = frappe.db.get_value("Farmer",data.get('farmer_id'), 'full_name')
	if frappe.db.exists("Customer", customer):
		sn_obj.customer = customer
		sn_obj.update(data)
		for row in sn_obj.items:
			row.cost_center = frappe.db.get_value("Company",company, 'cost_center')
		sn_obj.flags.ignore_permissions = True
		sn_obj.flags.ignore_mandatory = True
		sn_obj.save()
		sn_obj.submit()
		return sn_obj.name


@frappe.whitelist()
def sn_list():
	response_dict = {}
	try:
		pr_list = frappe.db.sql("""select status,company as vlcc,name,posting_date,additional_discount_percentage,customer as farmer,effective_credit,case_details taxes_and_charges,grand_total from `tabSales Invoice` where company = '{0}' and service_note = 1 order by creation desc limit 10 """.format(get_seesion_company_datails().get('company')),as_dict=1)
		if pr_list:
			print "#############",pr_list
			for row in pr_list:
				row.update({"items": frappe.db.sql("select item_code,item_name,qty,rate,uom from `tabSales Invoice Item` where parent = '{0}' order by idx".format(row.get('name')),as_dict=1)})
				row.update({"diagnosis": frappe.db.sql("""select disease,description from `tabDisease Child` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
				if row.get('taxes_and_charges'):
					row.update({row.get('taxes_and_charges'): frappe.db.sql("""select charge_type,description,rate from `tabSales Taxes and Charges` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
				else:
					del row['taxes_and_charges']
			response_dict.update({"status":"success","data":pr_list})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict