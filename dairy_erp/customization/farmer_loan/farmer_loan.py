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
			select name,farmer_name,emi_amount,advance_amount,farmer_id,
			vlcc,emi_deduction_start_cycle,outstanding_amount,date_of_disbursement,
			no_of_instalments,extension,vlcc
		from 
			`tabFarmer Loan`
		where
			status = 'Unpaid' and docstatus = 1
				""",as_dict=1)
	
	for row in docs:
		cur_cycl = get_current_cycle(row)
		child_cycl = frappe.db.sql("""select cycle from `tabFarmer Cycle` where parent =%s""",(row.get('name')),as_dict=1)
		cc = [i.get('cycle') for i in child_cycl]	
		if len(cur_cycl):
			if cur_cycl[0].get('name') in req_cycle_computation(row) and cur_cycl[0].get('name') not in cc and  not frappe.db.get_value("Farmer Settings",{'vlcc': row.get('vlcc')}, 'is_fpcr'):
				make_si(row,cur_cycl[0].get('name'))



def make_si(data,cur_cycl=None):
	try:	
		if data.get('outstanding_amount') > 0:
			si_doc = frappe.new_doc("Sales Invoice")
			si_doc.type = "Loan"
			si_doc.customer = data.get('farmer_name')
			si_doc.company = data.get('vlcc')
			si_doc.farmer_advance = data.get('name')
			si_doc.cycle_ = cur_cycl
			si_doc.append("items",{
				"item_code":"Milk Incentives",
				"qty": 1,
				"rate": data.get('emi_amount'),
				"cost_center": frappe.db.get_value("Company", data.get('vlcc'), "cost_center")
				})
			si_doc.flags.ignore_permissions = True
			si_doc.save()
			si_doc.submit()

			#update loan doc
			paid_instlmnt = 0
			loan_doc = frappe.get_doc("Farmer Loan",data.get('name'))
			loan_doc.outstanding_amount = float(data.get('advance_amount'))- get_si_amount(data)
			if loan_doc.outstanding_amount == 0:
				loan_doc.outstanding_amount = 0
				loan_doc.status = "Paid"
			loan_doc.append("cycle",{
				"cycle":cur_cycl
				})
			for i in loan_doc.cycle:
				paid_instlmnt += 1
			loan_doc.paid_instalment = paid_instlmnt
			loan_doc.flags.ignore_permissions = True
			loan_doc.save()
	except Exception,e:
		make_dairy_log(title="Sync failed for Data push",method="get_items", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())


def get_current_cycle(data):
	return frappe.db.sql("""
			select name 
		from
			`tabFarmer Date Computation`
		where
			vlcc = %s and now() between start_date and end_date
		""",(data.get('vlcc')),as_dict=1)


def req_cycle_computation(data):
	
	not_req_cycl = frappe.db.sql("""
			select name
		from
			`tabFarmer Date Computation`
		where
			'{0}' < start_date and vlcc = '{1}' order by start_date limit {2}""".
		format(data.get('date_of_disbursement'),data.get('vlcc'),data.get('emi_deduction_start_cycle')),as_dict=1)
	not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
	instalment = int(data.get('no_of_instalments')) + int(data.get('extension'))
	if len(not_req_cycl):
		req_cycle = frappe.db.sql("""
				select name
			from
				`tabFarmer Date Computation`
			where
				'{date}' < start_date and name not in ({cycle}) and vlcc = '{vlcc}' order by start_date limit {instalment}
			""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),vlcc = data.get('vlcc'),
				instalment = instalment),as_dict=1)
		
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list
	return []

def get_si_amount(data):
	sum_ = frappe.db.sql("""
			select ifnull(sum(grand_total),0) as total
		from 
			`tabSales Invoice` 
		where 
		farmer_advance =%s and total is not null""",(data.get('name')),as_dict=1)
	
	if len(sum_):
		return sum_[0].get('total') if sum_[0].get('total') != None else 0
	else: return 0



		
