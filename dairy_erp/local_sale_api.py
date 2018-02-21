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
		if data.get('items'):
			local_exist = frappe.db.get_value("Sales Invoice",{"client_id": data.get('client_id')}, 'name')
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
	ls_obj = frappe.new_doc("Sales Invoice")
	ls_obj.local_sale = 1
	ls_obj.update_stock = 1
	ls_obj.debit_to = frappe.db.get_value("Company",ls_obj.company, 'default_receivable_account')
	ls_obj.update(data)
	ls_obj.flags.ignore_permissions = True
	ls_obj.flags.ignore_mandatory = True
	ls_obj.save()
	ls_obj.submit()
	return ls_obj.name


@frappe.whitelist()
def local_sale_list():
	response_dict = {}
	try:
		la_list = frappe.db.sql("""select name,customer_or_farmer,posting_date,additional_discount_percentage,grand_total from `tabSales Invoice` where local_sale =1 order by creation desc limit 10 """,as_dict=1)
		for row in la_list:
			if row.get('customer_or_farmer') == "Farmer":
				row.update(
					{
						"farmer_name": frappe.db.get_value("Sales Invoice",row.get('name'),'customer'),
						"effective_credit": frappe.db.get_value("Sales Invoice",row.get('name'),'effective_credit'),
						"total_milk_cow": frappe.db.get_value("Sales Invoice",row.get('name'),'total_cow_milk_qty'),
						"total_milk_buffalo": frappe.db.get_value("Sales Invoice",row.get('name'),'total_buffalo_milk_qty'),
						"items": frappe.db.sql("select item_code,item_name,qty,rate,uom from `tabSales Invoice Item` where parent = '{0}' order by idx".format(row.get('name')),as_dict=1)
					}
				)
				if frappe.db.get_value("Sales Invoice",row.get('name'),'cash_payment'):
					row.update({"cash_payment":1})
		
			if row.get('customer_or_farmer') == "Vlcc Local Customer":
				row.update(
					{
						"total_milk_cow": frappe.db.get_value("Sales Invoice",row.get('name'),'total_cow_milk_qty'),
						"total_milk_buffalo": frappe.db.get_value("Sales Invoice",row.get('name'),'total_buffalo_milk_qty'),
						"items": frappe.db.sql("select item_code,item_name,qty,rate,uom from `tabSales Invoice Item` where parent = '{0}' order by idx".format(row.get('name')),as_dict=1)
					}
				)

		response_dict.update({"status":"success","data":la_list})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict


