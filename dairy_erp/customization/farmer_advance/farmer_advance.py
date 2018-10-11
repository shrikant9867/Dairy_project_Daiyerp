# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, nowdate
from dairy_erp.dairy_utils import make_dairy_log
import re
import datetime
from dairy_erp.dairy_utils import make_dairy_log, make_journal_entry
from frappe.utils import flt, today, getdate
from frappe.model.document import Document

def create_jv():
	docs = frappe.db.sql("""
			select name,farmer_name,emi_amount,advance_amount,farmer_id,
			vlcc,emi_deduction_start_cycle,outstanding_amount,date_of_disbursement,
			no_of_instalment,extension,vlcc,advance_type
		from 
			`tabFarmer Advance`
		where
			status = 'Unpaid' and docstatus = 1
				""",as_dict=1)
	for row in docs:
		cur_cycl = get_current_cycle(row)
		child_cycl = frappe.db.sql("""select cycle from `tabFarmer Cycle` where parent =%s""",(row.get('name')),as_dict=1)
		cc = [i.get('cycle') for i in child_cycl]
		req_cycle = req_cycle_computation(row)
		print req_cycle,cur_cycl,row.get('name')
		if len(req_cycle) > 0:
			req_cycle.pop(-1)
		if len(cur_cycl) and len(req_cycle) > 0:
			if cur_cycl[0].get('name') in req_cycle and cur_cycl[0].get('name') not in cc:
				make_jv(row,cur_cycl[0].get('name'))

def make_jv(data, cur_cycl=None):
	try:
		if data.get('outstanding_amount') > 0:
			if data.get('advance_type') == "Money Advance":
				je_doc = make_journal_entry(voucher_type = "Journal Entry",company = data.get('vlcc'),
			          posting_date = nowdate(),debit_account = "Debtors - ",credit_account = "Loans and Advances - ", 
			          type = "Farmer Advance", cycle = cur_cycl, amount = data.get('emi_amount'), faf_flag = 0, 
			          party_type = "Customer", party = data.get('farmer_name'), master_no = data.get('name'))
				if je_doc.name:
					update_advance_doc(data, je_doc, cur_cycl)
			elif data.get('advance_type') == "Feed And Fodder Advance":
				je_doc = make_journal_entry(voucher_type = "Journal Entry",company = data.get('vlcc'),
			          posting_date = nowdate(),debit_account = "Feed And Fodder Advances Temporary Account - ",credit_account = "Feed And Fodder Advance - ", 
			          type = "Farmer Advance", cycle = cur_cycl, amount = data.get('emi_amount'), faf_flag = 1, 
			          party_type = "Customer", party = data.get('farmer_name'), master_no = data.get('name'))
			
				if je_doc.name:
					update_advance_doc(data, je_doc, cur_cycl)
					
	except Exception,e:
		make_dairy_log(title="JV creation Against Advance Failed",method="make_jv", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())

def update_advance_doc(data, je_doc, cur_cycl):
	paid_instlmnt = 0
	advance_doc = frappe.get_doc("Farmer Advance",data.get('name'))
	advance_doc.append("cycle",{
		"cycle":cur_cycl,
		"sales_invoice": je_doc.name
		})
	out_stand_amt = get_jv_amount(data) - data.get('advance_amount') 
	"""Added by Jitendra, fixes negative outstading amount"""
	if 0 < out_stand_amt < 1:
		advance_doc.outstanding_amount = 0
	else:
		advance_doc.outstanding_amount = data.get('advance_amount') - get_jv_amount(data)
	
	if advance_doc.outstanding_amount == 0:
		advance_doc.outstanding_amount = 0
		advance_doc.status = "Paid"
	for i in advance_doc.cycle:
		paid_instlmnt += 1
	advance_doc.paid_instalment = paid_instlmnt
	advance_doc.flags.ignore_permissions = True
	advance_doc.save()

def get_jv_amount(data):
	sum_ = frappe.db.sql("""
			select ifnull(sum(total_debit),0) as total
		from 
			`tabJournal Entry` 
		where 
		farmer_advance =%s and type = 'Farmer Advance'""",(data.get('name')),as_dict=1,debug=0)
	if len(sum_):
		return sum_[0].get('total') if sum_[0].get('total') != None else 0
	else: return 0


def get_current_cycle(data):
	return frappe.db.sql("""
			select name 
		from
			`tabFarmer Date Computation`
		where
			vlcc = %s and date(now()) between start_date and end_date
		""",(data.get('vlcc')),as_dict=1,debug=0)


def req_cycle_computation(data):
	if data.get('emi_deduction_start_cycle') > 0:
		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabFarmer Date Computation`
			where
				'{0}' < start_date or date('{0}') between start_date and end_date 
				and vlcc = '{1}' order by start_date limit {2}""".
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
					'{date}' <= end_date and vlcc= '{vlcc}'
						order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'),vlcc=data.get('vlcc'),instalment = instalment),as_dict=1,debug=1)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list

	return []
