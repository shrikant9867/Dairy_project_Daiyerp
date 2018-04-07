# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,get_first_day,get_last_day
from erpnext.hr.doctype.process_payroll.process_payroll import get_month_details
from erpnext.accounts.utils import get_fiscal_year
import calendar
import datetime
from frappe import _

class VLCCPaymentCycle(Document):

	def validate(self):

		last_day = get_last_day(nowdate()).day

		for day in self.cycles:

			if day.idx == 1:
				if day.start_day != 1:
					frappe.throw("Cycle must be start with <b>1</b> for row <b>#{0}</b>".format(day.idx))
				elif day.end_day <= day.start_day:
					frappe.throw("End day must be greater than start day for row <b>#{0}</b>".format(day.idx))
				
			else: 
				if self.cycles[day.idx-2].end_day + 1 != day.start_day:
					frappe.throw("Cycle must be start with {0} in row#{1}".format(self.cycles[day.idx-2].end_day + 1,day.idx))
				# elif day.end_day <= day.start_day and day.idx != self.no_of_cycles:
				# 	frappe.throw("End day must be greater than start day for row <b>#{0}</b>".format(day.idx))
				elif day.idx == self.no_of_cycles and day.end_day != 31:
					frappe.throw("Cycle must be end with <b>31</b> for row <b>#{0}</b>".format(day.idx))


	def on_update(self):

		self.delete_date_computation()
		
		self.make_date_computation()

		frappe.msgprint(_("Cycles have been generated for fiscal year <b>{0}</b>".format(self.fiscal_year)))

	def delete_date_computation(self):

		frappe.delete_doc("Cyclewise Date Computation", frappe.db.sql_list("""select name from `tabCyclewise Date Computation`
		where fiscal_year = '{0}' {1}""".format(self.fiscal_year,self.get_conditions())), for_reload=True,ignore_permissions=True,force=True)

	def get_conditions(self):
		condn = " and 1=1"
		month = getdate(nowdate()).month
		current_month = calendar.month_abbr[month]
		if getdate(nowdate()).day > 10:
			condn += " and month !='{0}'".format(current_month)
		return condn

	def make_date_computation(self):

		month_dict = {}
		current_month = calendar.month_abbr[getdate(nowdate()).month]
		fy = self.fiscal_year.split("-")[0]
		
		month_end = {
			    "04": "Apr",
			    "05": "May",
			    "06": "Jun",
			    "07": "Jul",
			    "08": "Aug",
			    "09": "Sep",
			    "10": "Oct",
			    "11": "Nov",
			    "12": "Dec",
			    "01": "Jan",
			    "02": 'Feb',
			    "03": "Mar"
		}
		
		for i,val in month_end.items():
			for data in self.cycles:
				s_date = get_month_details(self.fiscal_year,i).month_start_date
				e_date = get_month_details(self.fiscal_year,i).month_end_date

				if data.start_day <= e_date.day:
					start_date = getdate(str(e_date.year) + "-"+str(e_date.month)+ "-"+str(data.start_day))
				else:
					continue

				if data.end_day <= e_date.day:
					end_date = getdate(str(e_date.year) + "-"+str(e_date.month)+ "-"+str(data.end_day))
				else:
					end_date = e_date

				date_computation = frappe.new_doc("Cyclewise Date Computation")
				date_computation.start_date = start_date
				date_computation.end_date = end_date 
				date_computation.month = val
				date_computation.cycle = data.cycle
				date_computation.fiscal_year = self.fiscal_year
				date_computation.doc_name = fy[2]+fy[3]+"-"+val + "-" +data.cycle
				date_computation.flags.ignore_permissions = True
				date_computation.save()
