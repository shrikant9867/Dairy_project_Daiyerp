# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,get_first_day,get_last_day,add_days
from erpnext.hr.doctype.process_payroll.process_payroll import get_month_details
from erpnext.accounts.utils import get_fiscal_year
import calendar
import datetime
import time
from frappe import _



def auto_cycle_create():
	
	vlcc_setting = frappe.get_all("VLCC Settings",fields=['no_of_cycles','no_of_interval','name'])
	current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
	current_month = getdate(nowdate()).month
	month_details = get_month_details(current_fiscal_year.get('name'),cint(current_month))
	cycle_data = {}
	s_date,e_date = "",""

	vlcc_settings = vlcc_setting[0].get('name') if vlcc_setting and vlcc_setting[0].get('name') else []
	if vlcc_settings:
		for vlcc in vlcc_setting:
			if vlcc.get('no_of_cycles') and vlcc.get('no_of_interval'):
				for cycle_index in range(1,cint(vlcc.get('no_of_cycles'))+cint(1)):
					if cycle_index == 1:
						s_date = month_details.month_start_date
						e_date = datetime.date(month_details.year, cint(current_month), cint(vlcc.get('no_of_interval')))
						cycle_data.update({"Cycle "+str(cycle_index):[s_date,e_date]})
					elif cycle_index == cint(vlcc.get('no_of_cycles')):
						s_date = add_days(getdate(s_date),cint(vlcc.get('no_of_interval')))
						e_date = month_details.month_end_date
						cycle_data.update({"Cycle "+str(cycle_index):[s_date,e_date]})
					else:
						s_date = add_days(getdate(s_date),cint(vlcc.get('no_of_interval')))
						e_date = add_days(getdate(e_date),cint(vlcc.get('no_of_interval')))
						cycle_data.update({"Cycle "+str(cycle_index):[s_date,e_date]})

def cycle_date_computation():
	date_computation = frappe.new_doc("Farmer Date Computation")
	date_computation.start_date = start_date
	date_computation.end_date = end_date 
	date_computation.month = key
	date_computation.cycle = data.cycle
	date_computation.vlcc = self.vlcc
	date_computation.fiscal_year = self.fiscal_year
	date_computation.doc_name = fy[2]+fy[3]+"-"+key + "-" +data.cycle+"-"+company_abbr
	date_computation.flags.ignore_permissions = True
	date_computation.save()
