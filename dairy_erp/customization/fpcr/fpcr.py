# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from dairy_erp.dairy_utils import make_dairy_log
from frappe.utils import flt, today, getdate, nowdate
from dairy_erp.customization.vlcc_loan.vlcc_loan import get_current_cycle


def auto_fpcr():
	try:
		farmer_list = frappe.get_all("Farmer",['farmer_id','vlcc_name','full_name'])
		for farmer in farmer_list:
			cur_cycle = get_current_cycle(farmer)
			if len(cur_cycle):
				generate_fpcr(cur_cycle[0].get('name'))
	except Exception,e:
		make_dairy_log(title="Auto Fpcr Failed",method="auto_fpcr", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())

def get_current_cycle(data):
	return frappe.db.sql("""
			select name 
		from
			`tabFarmer Date Computation`
		where
			vlcc = %s and now() between start_date and end_date
		""",(data.get('vlcc_name')),as_dict=1)

def generate_fpcr(cur_cycle, farmer):
	fpcr_doc = frappe.new_doc("Farmer Payment Cycle Report")
	fpcr_doc.vlcc_name = farmer.get('vlcc_name')
	fpcr_doc.date = nowdate
	fpcr_doc.cycle = cur_cycle
	fpcr_doc.farmer_id = farmer.get('farmer_id')
	fpcr_doc.append('fmcr_details',{

		})
