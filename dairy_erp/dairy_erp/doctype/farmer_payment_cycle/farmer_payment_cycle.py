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

class FarmerPaymentCycle(Document):

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
				elif day.end_day <= day.start_day and day.idx != self.no_of_cycles:
					frappe.throw("End day must be greater than start day for row <b>#{0}</b>".format(day.idx))
				elif day.idx == self.no_of_cycles and day.end_day != last_day:
					frappe.throw("Cycle must be end with <b>{0}</b> for row <b>#{1}</b>".format(last_day,day.idx))


	def on_update(self):

		self.delete_date_computation()
		
		self.make_date_computation()

	def delete_date_computation(self):

		frappe.delete_doc("Farmer Date Computation", frappe.db.sql_list("""select name from `tabFarmer Date Computation`
		where {0}""".format(self.get_conditions())), for_reload=True,ignore_permissions=True,force=True)

	def get_conditions(self):
		condn = "1=1"
		month = getdate(nowdate()).month
		current_month = calendar.month_abbr[month]
		if getdate(nowdate()).day > 10:
			condn += " and month !='{0}'".format(current_month)
		return condn

	def make_date_computation(self):

		month_dict = {}
		month = getdate(nowdate()).month
		current_month = calendar.month_abbr[month]
		fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
		month_list = frappe.db.sql_list("""select month from `tabFarmer Date Computation`
			where month = %s""",(current_month))

		month_end = {
			    "01": "Jan",
			    "02": 'Feb',
			    "03": "Mar",
			    "04": "Apr",
			    "05": "May",
			    "06": "Jun",
			    "07": "Jul",
			    "08": "Aug",
			    "09": "Sep",
			    "10": "Oct",
			    "11": "Nov",
			    "12": "Dec"
		}

		for data in self.cycles:
			for i,val in sorted(month_end.items()):
				if val not in month_list:
					end_date = get_month_details(fiscal_year.get('name'),i).month_end_date
					month_dict.update({i:end_date})

					start_date = getdate(getdate(nowdate()).strftime("%Y") + "-"+i+ "-"+str(data.start_day))

					if data.end_day in [31,30,28,29]:
						end_date = month_dict[i] 
					elif data.end_day < cint(month_dict[i].day):
						end_date = getdate(getdate(nowdate()).strftime("%Y") + "-"+i + "-"+str(data.end_day))

					payble_amount = self.get_payble_amount(start_date,end_date)
					credit_list = [i.get('credit') for i in payble_amount]
				
					date_computation = frappe.new_doc("Farmer Date Computation")
					date_computation.start_date = start_date
					date_computation.end_date = end_date 
					date_computation.month = val
					date_computation.amount = sum(credit_list)
					date_computation.cycle = data.cycle
					date_computation.doc_name = val + "-" +data.cycle
					date_computation.flags.ignore_permissions = True
					date_computation.save()


	def get_payble_amount(self,start_date,end_date):

		vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')

		return frappe.db.sql("""select sum(g.credit) as credit,g.voucher_no ,p.posting_date
				from 
					`tabGL Entry` g,`tabPurchase Invoice` p 
				where 
					g.party = 'vlcc1' and g.against_voucher_type in ('Purchase Invoice') 
					and (g.party is not null and g.party != '') and 
					g.docstatus < 2 and p.name = g.voucher_no and g.company = %s and
					p.status!='Paid' and p.posting_date between %s and %s 
					group by g.against_voucher, g.party having credit > 0""",(vlcc,start_date,end_date),as_dict=1)

