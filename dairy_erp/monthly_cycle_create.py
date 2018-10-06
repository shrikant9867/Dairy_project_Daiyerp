# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,get_first_day,get_last_day,add_days
from erpnext.hr.doctype.process_payroll.process_payroll import get_month_details
from erpnext.accounts.utils import get_fiscal_year
from collections import OrderedDict
import dairy_utils as utils
import calendar
import datetime
import time
from frappe import _



def monthly_cycle_creation():
	try:
		farmer_date_computation()
		vlcc_date_computation()
	except Exception,e:
		utils.make_dairy_log(title="Monthly Cycle Create Error",method="monthly_cycle_creation", 
		status="Error",data="message" ,message="e", traceback=frappe.get_traceback())
	
def vlcc_date_computation():

	dairy_setting = frappe.get_doc("Dairy Setting")
	current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
	current_month = getdate(nowdate()).month
	current_month_abbr = calendar.month_abbr[current_month]
	month_details = get_month_details(current_fiscal_year.get('name'),cint(current_month))
	cycle_data = OrderedDict()
	s_date,e_date = "",""

	cycle_exist = frappe.get_all('Cyclewise Date Computation',
			filters = { 'month': current_month_abbr,
			'fiscal_year':current_fiscal_year.get('name')})

	if not len(cycle_exist) and dairy_setting.no_of_cycles and dairy_setting.no_of_interval:
		for cycle_index in range(1,cint(dairy_setting.no_of_cycles)+cint(1)):
			cycle_name = "Cycle "+str(cycle_index)
			cycle_data.setdefault(cycle_name, {})

			if cycle_index == 1:
				s_date = month_details.month_start_date
				e_date = datetime.date(month_details.year, cint(current_month), cint(dairy_setting.no_of_interval))
			elif cycle_index == cint(dairy_setting.no_of_cycles):
				s_date = add_days(getdate(s_date),cint(dairy_setting.no_of_interval))
				e_date = month_details.month_end_date
			else:
				s_date = add_days(getdate(s_date),cint(dairy_setting.no_of_interval))
				e_date = add_days(getdate(e_date),cint(dairy_setting.no_of_interval))

			args = {
				"start_date": s_date,
				"end_date": e_date,
				"month":current_month_abbr,
				"fiscal_year":current_fiscal_year.get('name')
			}
			cycle_data[cycle_name].update(args)

		vlcc_cycle_date_computation(cycle_data)

def farmer_date_computation():

	vlcc_setting = frappe.get_all("VLCC Settings",fields=['no_of_cycles','no_of_interval','name'])
	current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
	current_month = getdate(nowdate()).month
	current_month_abbr = calendar.month_abbr[current_month]
	month_details = get_month_details(current_fiscal_year.get('name'),cint(current_month))
	cycle_data = OrderedDict()
	s_date,e_date = "",""

	vlcc_settings = vlcc_setting[0].get('name') if vlcc_setting and vlcc_setting[0].get('name') else []
	if vlcc_settings:
		for vlcc in vlcc_setting:
			cycle_exist = frappe.get_all('Farmer Date Computation',
					filters = {'vlcc': vlcc.get('name'), 
					'month': current_month_abbr,
					'fiscal_year':current_fiscal_year.get('name')})

			if not len(cycle_exist) and vlcc.get('no_of_cycles') and vlcc.get('no_of_interval'):
				for cycle_index in range(1,cint(vlcc.get('no_of_cycles'))+cint(1)):
					cycle_name = "Cycle "+str(cycle_index)
					cycle_data.setdefault(cycle_name, {})

					if cycle_index == 1:
						s_date = month_details.month_start_date
						e_date = datetime.date(month_details.year, cint(current_month), cint(vlcc.get('no_of_interval')))
					elif cycle_index == cint(vlcc.get('no_of_cycles')):
						s_date = add_days(getdate(s_date),cint(vlcc.get('no_of_interval')))
						e_date = month_details.month_end_date
					else:
						s_date = add_days(getdate(s_date),cint(vlcc.get('no_of_interval')))
						e_date = add_days(getdate(e_date),cint(vlcc.get('no_of_interval')))

					args = {
						"start_date": s_date,
						"end_date": e_date,
						"month":current_month_abbr,
						"fiscal_year":current_fiscal_year.get('name'),
						"vlcc":vlcc.get('name')
					}
					cycle_data[cycle_name].update(args)
			farmer_cycle_date_computation(cycle_data)

def farmer_cycle_date_computation(cycle_data):

	for cycle,args in cycle_data.items():
		fy = args.get('fiscal_year').split("-")[0]
		company_abbr = frappe.db.get_value("Village Level Collection Centre",args.get('vlcc'),"abbr")
		
		date_computation = frappe.new_doc("Farmer Date Computation")
		date_computation.start_date = args.get('start_date')
		date_computation.end_date = args.get('end_date')
		date_computation.month = args.get('month')
		date_computation.cycle = cycle
		date_computation.vlcc = args.get('vlcc')
		date_computation.fiscal_year = args.get('fiscal_year')
		date_computation.doc_name = fy[2]+fy[3]+"-"+args.get('month') + "-" +cycle+"-"+company_abbr
		date_computation.flags.ignore_permissions = True
		date_computation.save()

def vlcc_cycle_date_computation(cycle_data):

	for cycle,args in cycle_data.items():
		fy = args.get('fiscal_year').split("-")[0]		
		date_computation = frappe.new_doc("Cyclewise Date Computation")
		date_computation.start_date = args.get('start_date')
		date_computation.end_date = args.get('end_date')
		date_computation.month = args.get('month')
		date_computation.cycle = cycle
		date_computation.fiscal_year = args.get('fiscal_year')
		date_computation.doc_name = fy[2]+fy[3]+"-"+args.get('month') + "-" +cycle
		date_computation.flags.ignore_permissions = True
		date_computation.save()
