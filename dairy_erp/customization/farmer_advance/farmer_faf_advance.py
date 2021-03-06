# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stellapps Technologies Private Ltd.
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
			no_of_instalment,extension,vlcc
		from 
			`tabFarmer Advance`
		where
			status = 'Unpaid' and docstatus = 1
				""",as_dict=1)
	for row in docs:
		cur_cycl = get_current_cycle(row)
		child_cycl = frappe.db.sql("""select cycle from `tabFarmer Cycle` where parent =%s""",(row.get('name')),as_dict=1)
		cc = [i.get('cycle') for i in child_cycl]	
		if len(cur_cycl):
			if cur_cycl[0].get('name') in req_cycle_computation(row) and cur_cycl[0].get('name') not in cc:
				make_si(row,cur_cycl[0].get('name'))


def make_si(data, cur_cycl=None):
	try:
		if data.get('outstanding_amount') > 0:
			si_doc = frappe.new_doc("Sales Invoice")
			si_doc.type = "Advance"
			si_doc.customer = data.get('farmer_name')
			si_doc.company = data.get('vlcc')
			si_doc.farmer_advance = data.get('name')
			si_doc.cycle_ = cur_cycl
			si_doc.append("items",{
				"item_code":"Advance Emi",
				"qty": 1,
				"rate": data.get('emi_amount'),
				"cost_center": frappe.db.get_value("Company", data.get('vlcc'), "cost_center")
				})
			si_doc.flags.ignore_permissions = True
			si_doc.insert()
			si_doc.submit()

			#update advance doc
			paid_instlmnt = 0
			advance_doc = frappe.get_doc("Farmer Advance",data.get('name'))
			advance_doc.append("cycle",{
				"cycle":cur_cycl,
				"sales_invoice": si_doc.name
				})
			advance_doc.outstanding_amount = data.get('advance_amount') - get_si_amount(data)
			if advance_doc.outstanding_amount == 0:
				advance_doc.outstanding_amount = 0
				advance_doc.status = "Paid"
			for i in advance_doc.cycle:
				paid_instlmnt += 1
			advance_doc.paid_instalment = paid_instlmnt
			advance_doc.flags.ignore_permissions = True
			advance_doc.save()
	
	except Exception,e:
		make_dairy_log(title="Sync failed for Data push",method="get_items", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())


def get_si_amount(data):
	sum_ = frappe.db.sql("""
			select ifnull(sum(grand_total),0) as total
		from 
			`tabSales Invoice` 
		where 
		farmer_advance =%s""",(data.get('name')),as_dict=1)
	if len(sum_):
		return sum_[0].get('total') if sum_[0].get('total') != None else 0
	else: return 0


def get_current_cycle(data):
	return frappe.db.sql("""
			select name 
		from
			`tabFarmer Date Computation`
		where
			vlcc = %s and now() between start_date and end_date
		""",(data.get('vlcc')),as_dict=1)


def req_cycle_computation(data):
	if data.get('emi_deduction_start_cycle') > 0:
		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabFarmer Date Computation`
			where
				'{0}' < start_date and vlcc = '{1}' order by start_date limit {2}""".
			format(data.get('date_of_disbursement'),data.get('vlcc'),data.get('emi_deduction_start_cycle')),as_dict=1)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
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

	elif data.get('emi_deduction_start_cycle') == 0:
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select
						name
					from
						`tabFarmer Date Computation`
					where
					'{date}' < end_date
						order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'),instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list

	return []

