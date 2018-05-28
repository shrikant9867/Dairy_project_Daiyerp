# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from dairy_erp.dairy_utils import make_dairy_log
import re
import datetime
from dairy_erp.dairy_utils import make_dairy_log
from frappe.utils import flt, today, getdate
from frappe.model.document import Document

def create_si():
	docs = frappe.db.sql("""
		select name,start_date,emi_amount,farmer_id,farmer_name,
		vlcc,status,farmer_advance
	from 
		`tabRecurring Sales Invoice Log`""",as_dict=1)
	for row in docs:
		make_si(row)


def make_si(data):
	try:	
		if today() == str(data.get('start_date')) and data.get('status') == "Pending":
			si_doc = frappe.new_doc("Sales Invoice")
			si_doc.type = "Advance"
			si_doc.customer = data.get('farmer_name')
			si_doc.company = data.get('vlcc')
			si_doc.farmer_advance = data.get('farmer_advance')
			si_doc.append("items",{
				"item_code":"Milk Incentives",
				"qty": 1,
				"rate": data.get('emi_amount'),
				"cost_center": frappe.db.get_value("Company", data.get('vlcc'), "cost_center")
				})
			si_doc.flags.ignore_permissions = True
			si_doc.save()
			si_doc.submit()
			rec_doc = frappe.get_doc("Recurring Sales Invoice Log",data.get('name'))
			rec_doc.status = "Generated"
			rec_doc.flags.ignore_permissions = True
			rec_doc.submit()
	except Exception,e:
		make_dairy_log(title="Sync failed for Data push",method="get_items", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())