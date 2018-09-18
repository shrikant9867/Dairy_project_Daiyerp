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


def auto_vpcr():
	try:
		vlcc_list = frappe.get_all("Village Level Collection Centre", 'name')
		for vlcc in vlcc_list:
			current_pc = get_current_cycle()
			if len(current_pc):
				is_vpcr = frappe.db.get_value("VLCC Payment Cycle Report", {'cycle': current_pc[0].get('name'), 'vlcc_name': vlcc.get('name')})
				if not is_vpcr:
					generate_vpcr(current_pc[0].get('name'), vlcc.get('name'))
	except Exception,e:
		make_dairy_log(title="Sync failed for Data push",method="get_items", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())

def generate_vpcr(cur_cycle, vlcc):
	vmcr = get_vmcr_data(cur_cycle, vlcc)
	

def get_vmcr_data(cur_cycle, vlcc):
	vmcr =  frappe.db.sql("""
			select rcvdtime,shift,milkquantity,fat,snf,rate,amount
		from 
			`tabVlcc Milk Collection Record`
		where 
			associated_vlcc = '{0}' and date(rcvdtime) between '{1}' and '{2}'
			""".format(vlcc, frappe.db.get_value('Cyclewise Date Computation',cur_cycle,'start_date'), \
			frappe.db.get_value('Cyclewise Date Computation',cur_cycle,'start_date')),as_dict=1,debug=0)
