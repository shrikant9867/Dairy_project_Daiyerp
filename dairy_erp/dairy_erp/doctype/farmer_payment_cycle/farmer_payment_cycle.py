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
import time
from frappe import _

class FarmerPaymentCycle(Document):

	def validate(self):

		self.validate_def()
		self.validate_data()
		self.validate_cycle()
	

	def validate_def(self):
		user_doc = frappe.db.get_value("User",{"name":frappe.session.user},'company')

		if self.is_new():
			if frappe.db.sql_list("""select name from `tabFarmer Payment Cycle` 
							where vlcc = %s""",(user_doc)):
				frappe.throw("Please add cycles in the existing defination of cycle")

	def validate_cycle(self):

		for day in self.cycles:
			if self.no_of_cycles == 1:
				if not day.start_day and not day.end_day:
					frappe.throw("Please add start/end day")
				elif day.start_day != 1:
					frappe.throw("Cycle must be start with <b>1</b> for row <b>#{0}</b>".format(day.idx))
				elif day.end_day < day.start_day and day.end_day:
					frappe.throw("End day must be greater than start day for row <b>#{0}</b>".format(day.idx))
				else:
					if self.month == 'All':
						if day.end_day != 31:
							frappe.throw("Cycle must be end with <b>31</b> for row <b>#{0}</b>".format(day.idx))
					else:
						month_num = "%02d" % time.strptime(self.month, "%b").tm_mon
						end_date = get_month_details(self.fiscal_year,month_num).month_end_date
						if day.end_day != end_date.day:
							frappe.throw("Cycle must be end with <b>{0}</b> for row <b>#{1}</b>".format(end_date.day,day.idx))
			else:
				if day.idx == 1:
					if not day.start_day and not day.end_day:
						frappe.throw("Please add start/end day")
					elif day.start_day != 1:
						frappe.throw("Cycle must be start with <b>1</b> for row <b>#{0}</b>".format(day.idx))
					elif day.end_day and day.end_day < day.start_day:
						frappe.throw("End day must be greater than start day for row <b>#{0}</b>".format(day.idx))
					else:
						if self.month == 'All':
							if day.end_day >= 31:
								frappe.throw("End day must be less than <b>31</b> for row <b>#{0}</b>".format(day.idx))
						else:
							month_num = "%02d" % time.strptime(self.month, "%b").tm_mon
							end_date = get_month_details(self.fiscal_year,month_num).month_end_date
							if day.end_day >= end_date.day:
								frappe.throw("End day must be less than <b>{0}</b> for row <b>#{1}</b>".format(end_date.day,day.idx))
					
				else:
					if not day.start_day and not day.end_day:
						frappe.throw("Please add start/end day") 
					elif self.cycles[day.idx-2].end_day + 1 != day.start_day:
						frappe.throw("Cycle must be start with <b>{0}</b> in row#{1}".format(self.cycles[day.idx-2].end_day + 1,day.idx))
					elif day.end_day < day.start_day and day.idx != self.no_of_cycles:
						frappe.throw("End day must be greater than start day for row <b>#{0}</b>".format(day.idx))
					elif day.idx != self.no_of_cycles:
						if self.month == 'All':
							if day.end_day >= 31:
								frappe.throw("End day must be less than <b>31</b> for row <b>#{0}</b>".format(day.idx))
						else:
							month_num = "%02d" % time.strptime(self.month, "%b").tm_mon
							end_date = get_month_details(self.fiscal_year,month_num).month_end_date
							if day.end_day >= end_date.day:
								frappe.throw("End day must be less than <b>{0}</b> for row <b>#{1}</b>".format(end_date.day,day.idx))
					elif day.idx == self.no_of_cycles:
						if self.month == 'All': 
							if day.end_day != 31:
								frappe.throw("Cycle must be end with <b>31</b> for row <b>#{0}</b>".format(day.idx))
						else:
							month_num = "%02d" % time.strptime(self.month, "%b").tm_mon
							end_date = get_month_details(self.fiscal_year,month_num).month_end_date
							if day.end_day != end_date.day:
								frappe.throw("Cycle must be end with <b>{0}</b> for row <b>#{1}</b>".format(end_date.day,day.idx))

	def validate_data(self):

		if self.no_of_cycles == 0:
			frappe.throw("Number of cycles must be between 1-31")


	def on_update(self):

		self.delete_date_computation()
		
		self.make_date_computation()


	def delete_date_computation(self):

		current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)

		if self.fiscal_year == current_fiscal_year.get('name'):

			frappe.delete_doc("Farmer Date Computation", frappe.db.sql_list("""select name from 
			`tabFarmer Date Computation` where {0}""".format(self.get_conditions())), 
			for_reload=True,ignore_permissions=True,force=True)

	def get_conditions(self):

		condn = " 1=1"

		current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
		current_month = calendar.month_abbr[getdate(nowdate()).month]

		e_date = frappe.db.get_value("Farmer Date Computation",
			{"fiscal_year":current_fiscal_year.get('name'),
			"month":current_month,"cycle":'Cycle 1'},"end_date")

		month_e_date = frappe.db.get_value("Farmer Date Computation",
			{"fiscal_year":current_fiscal_year.get('name'),
			"month":self.month,"cycle":'Cycle 1'},"end_date")

		if self.month == 'All':
			if getdate(nowdate()) > getdate(e_date) :
				condn += " and month !='{0}'".format(current_month)
		else:
			if getdate(nowdate()) > getdate(month_e_date):
				condn += " and 1=2"
			else:
				condn += " and month = '{0}'".format(self.month)

		return condn

	def make_date_computation(self):

		fy = self.fiscal_year.split("-")[0]
		current_month = calendar.month_abbr[getdate(nowdate()).month]
		
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

		cycle_exist_all = frappe.db.sql("""select end_date from `tabFarmer Date Computation` 
					where month=%s and fiscal_year = %s and cycle = 'Cycle 1'""",(current_month,self.fiscal_year),as_dict=True)

		cycle_exist_month = frappe.db.sql("""select end_date from `tabFarmer Date Computation` 
					where month=%s and fiscal_year = %s and cycle = 'Cycle 1' """,(self.month,self.fiscal_year),as_dict=True)

		if self.month == 'All':
			if len(cycle_exist_all):
				if getdate(nowdate()) < getdate(cycle_exist_all[0].get('end_date')):
					for key,val in month_end.items():
						for data in self.cycles:
							self.make_monthwise_computation(key=key,val=val,data=data)
					frappe.msgprint(_("Cycles have been generated"))
				else:
					for key,val in month_end.items():
						for data in self.cycles:
							if key != current_month:
								self.make_monthwise_computation(key=key,val=val,data=data)
					frappe.msgprint(_("Cycles have been generated"))
			else:
				for key,val in month_end.items():
					for data in self.cycles:
						self.make_monthwise_computation(key=key,val=val,data=data)
				frappe.msgprint(_("Cycles have been generated"))

		else:
			if len(cycle_exist_month):
				if getdate(nowdate()) < getdate(cycle_exist_month[0].get('end_date')):
					for data in self.cycles:
						self.make_monthwise_computation(key=self.month,val=month_end.get(self.month),data=data)
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
			company_abbr = frappe.db.get_value("Village Level Collection Centre",self.vlcc,"abbr")
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

def farmer_permission_query(user):

	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)

	cycle_list =['"%s"'%i.get('name') for i in frappe.db.sql("""select name from 
				`tabFarmer Payment Cycle` 
				where vlcc = %s""",(user_doc.get('company')),as_dict=True)]

	if cycle_list:
		if user != 'Administrator' and 'Vlcc Manager' in roles:
			return """`tabFarmer Payment Cycle`.name in ({date})""".format(date=','.join(cycle_list))
	else:
		if user != 'Administrator':
			return """`tabFarmer Payment Cycle`.name = 'Guest' """
