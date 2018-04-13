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
				elif day.end_day < day.start_day:
					frappe.throw("End day must be greater than start day for row <b>#{0}</b>".format(day.idx))
				
			else: 
				if self.cycles[day.idx-2].end_day + 1 != day.start_day:
					frappe.throw("Cycle must be start with {0} in row#{1}".format(self.cycles[day.idx-2].end_day + 1,day.idx))
				elif day.end_day < day.start_day and day.idx != self.no_of_cycles:
					frappe.throw("End day must be greater than start day for row <b>#{0}</b>".format(day.idx))
				elif day.idx == self.no_of_cycles and day.end_day != 31:
					frappe.throw("Cycle must be end with <b>31</b> for row <b>#{0}</b>".format(day.idx))


	def on_update(self):

		self.delete_date_computation()
		
		self.make_date_computation()


	def delete_date_computation(self):

		current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)

		if self.fiscal_year == current_fiscal_year.get('name'):

			frappe.delete_doc("Cyclewise Date Computation", frappe.db.sql_list("""select name 
							from `tabCyclewise Date Computation`
							where  {1}""".format(self.fiscal_year,self.get_conditions()),debug=1), 
						for_reload=True,ignore_permissions=True,force=True)


	def get_conditions(self):

		condn = " 1=1"
		month_list = frappe.db.sql_list("select month from `tabCyclewise Date Computation` group by month")
		months = "(" + ",".join([ "'{0}'".format(month) for month in month_list ])  +")"

		current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
		current_month = calendar.month_abbr[getdate(nowdate()).month]

		e_date = frappe.db.get_value("Cyclewise Date Computation",
			{"fiscal_year":current_fiscal_year.get('name'),
			"month":current_month,"cycle":'Cycle 1'},"end_date")

		month_e_date = frappe.db.get_value("Cyclewise Date Computation",
			{"fiscal_year":current_fiscal_year.get('name'),
			"month":self.month,"cycle":'Cycle 1'},"end_date")

		if self.month == 'All':
			if getdate(nowdate()) > getdate(e_date) :
				condn += " and month !='{0}'".format(current_month)
		else:
			if getdate(nowdate()) > getdate(month_e_date):
				condn += " and 1=2"#month != '{0}'".format(self.month)
			else:
				condn += " and month = '{0}'".format(self.month)


		return condn


	def make_date_computation(self):

		fy = self.fiscal_year.split("-")[0]
		
		month_end = {
			    "Apr":"04", 
			    "May":"05", 
			    "Jun":"06", 
			    "Jul":"07", 
			    "Aug":"08", 
			    "Sep":"09", 
			    "Oct":"10", 
			    "Nov":"11", 
			    "Dec":"12", 
			    "Jan":"01", 
			    "Feb":"02", 
			    "Mar":"03" 
		}

		if self.month == 'All':
			for key,val in month_end.items():
				for data in self.cycles:
					self.make_monthwise_computation(key=key,val=val,data=data)
			frappe.msgprint(_("Cycles have been generated"))
		else:
			for data in self.cycles:
				self.make_monthwise_computation(key=self.month,val=month_end.get(self.month),data=data)
			frappe.msgprint(_("Cycles have been generated"))

		

	def make_monthwise_computation(self,key,val,data):

		fy = self.fiscal_year.split("-")[0]
		current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
		start_date = ""
		end_date = ""
		
		s_date = get_month_details(self.fiscal_year,val).month_start_date
		e_date = get_month_details(self.fiscal_year,val).month_end_date

		if data.start_day <= e_date.day:
			start_date = getdate(str(e_date.year) + "-"+str(e_date.month)+ "-"+str(data.start_day))
		

		if data.end_day <= e_date.day:
			end_date = getdate(str(e_date.year) + "-"+str(e_date.month)+ "-"+str(data.end_day))
		else:
			end_date = e_date


		if start_date and end_date:
			if not frappe.db.exists('Cyclewise Date Computation', fy[2]+fy[3]+"-"+key + "-" +data.cycle):
				date_computation = frappe.new_doc("Cyclewise Date Computation")
				date_computation.start_date = start_date
				date_computation.end_date = end_date 
				date_computation.month = key
				date_computation.cycle = data.cycle
				date_computation.fiscal_year = self.fiscal_year
				date_computation.doc_name = fy[2]+fy[3]+"-"+key + "-" +data.cycle
				date_computation.flags.ignore_permissions = True
				date_computation.save()
