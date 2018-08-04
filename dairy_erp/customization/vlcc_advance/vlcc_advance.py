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
			select name,vlcc,emi_amount,advance_amount,emi_deduction_start_cycle,
			outstanding_amount,date_of_disbursement,no_of_instalment,extension,status
		from 
			`tabVlcc Advance`
		where
			status = 'Unpaid' and docstatus = 1
				""",as_dict=1)
	for row in docs:
		cur_cycl = get_current_cycle()
		child_cycl = frappe.db.sql("""select cycle from `tabVlcc Cycle` 
			where parent =%s""",(row.get('name')),as_dict=1)
		cc = [i.get('cycle') for i in child_cycl]
		if len(cur_cycl):
			if cur_cycl[0].get('name') in req_cycle_computation(row) and cur_cycl[0].get('name') not in cc:
				make_si(row,cur_cycl[0].get('name'))

def make_si(data, cur_cycl=None):
	try:
		if data.get('outstanding_amount') > 0:
			company = frappe.db.get_value("Company",{'is_dairy':1},'name')
			si_doc = frappe.new_doc("Sales Invoice")
			si_doc.type = "Vlcc Advance"
			si_doc.customer = data.get('vlcc')
			si_doc.company = company
			si_doc.vlcc_advance_loan = data.get('name')
			si_doc.cycle_ = cur_cycl
			si_doc.append("items",{
				"item_code":"Advance Emi",
				"qty": 1,
				"rate": data.get('emi_amount'),
				"cost_center": frappe.db.get_value("Company", company, "cost_center")
				})
			si_doc.flags.ignore_permissions = True
			si_doc.insert()
			si_doc.submit()
			make_pi(data, cur_cycl, company)

			#update advance doc
			paid_instlmnt = 0
			advance_doc = frappe.get_doc("Vlcc Advance",data.get('name'))
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
		frappe.db.rollback()
		make_dairy_log(title="Sync failed for Data push",method="get_items", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())

def  make_pi(data, cur_cycl=None, company=None):
	pi = frappe.new_doc("Purchase Invoice")
	pi.supplier = company
	pi.company = data.get('vlcc')
	pi.pi_type = "Vlcc Advance"
	pi.cycle = cur_cycl
	pi.vlcc_advance_loan = data.get('name')
	pi.append("items",
		{
			"item_code":"Advance Emi",
			"qty": 1,
			"rate": data.get('emi_amount'),
			"cost_center": frappe.db.get_value("Company", company, "cost_center")
		})
	pi.flags.ignore_permissions = True
	pi.save()
	pi.submit()

def get_current_cycle():
	return frappe.db.sql("""
			select name 
		from
			`tabCyclewise Date Computation`
		where
			now() between start_date and end_date
		""",as_dict=1)


def req_cycle_computation(data):
	if data.get('emi_deduction_start_cycle') > 0:
		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabCyclewise Date Computation`
			where
				'{0}' < start_date  order by start_date limit {1}""".
			format(data.get('date_of_disbursement'),data.get('emi_deduction_start_cycle')),as_dict=1,debug=0)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		if len(not_req_cycl):
			req_cycle = frappe.db.sql("""
					select name
				from
					`tabCyclewise Date Computation`
				where
					'{date}' < start_date and name not in ({cycle}) order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),
					instalment = instalment),as_dict=1)
			
			req_cycl_list = [i.get('name') for i in req_cycle]
			return req_cycl_list

	elif data.get('emi_deduction_start_cycle') == 0:

		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabCyclewise Date Computation`
			where
				'{0}' < start_date order by start_date limit {1}""".
			format(data.get('date_of_disbursement'),data.get('emi_deduction_start_cycle')),as_dict=1,debug=0)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select name
				from
					`tabCyclewise Date Computation`
				where
					'{date}' < start_date  order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),
					instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list

	elif data.get('emi_deduction_start_cycle') == -1:
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select
						name
					from
						`tabCyclewise Date Computation`
					where
					'{date}' < end_date
						order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'),instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list

	return []

def get_si_amount(data):
	sum_ = frappe.db.sql("""
			select ifnull(sum(grand_total),0) as total
		from 
			`tabSales Invoice` 
		where 
		vlcc_advance_loan =%s""",(data.get('name')),as_dict=1)
	if len(sum_):
		return sum_[0].get('total') if sum_[0].get('total') != None else 0
	else: return 0