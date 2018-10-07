# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt,nowdate
from dairy_erp.dairy_utils import make_dairy_log
import re
import datetime
from dairy_erp.dairy_utils import make_dairy_log
from frappe.utils import flt, today, getdate
from frappe.model.document import Document



def create_jv():
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
			company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
			je_doc = frappe.new_doc("Journal Entry")
			je_doc.voucher_type = "Journal Entry"
			je_doc.company = company.get('name')
			je_doc.type = "Vlcc Advance"
			je_doc.cycle = cur_cycl
			je_doc.vlcc_advance = data.get('name')
			je_doc.posting_date = nowdate()
			je_doc.append('accounts', {
				'account': "Debtors - "+ company.get('abbr'),
				'debit_in_account_currency': data.get('emi_amount'),
				'party_type': "Customer",
				'party': data.get('vlcc'),
				'cost_center': company.get('cost_center')
				})
			je_doc.append('accounts', {
				'account': "Loans and Advances - "+ company.get('abbr'),
				'credit_in_account_currency':  data.get('emi_amount'),
				'cost_center': company.get('cost_center')
				})
			je_doc.flags.ignore_permissions = True
			je_doc.save()
			je_doc.submit()
			make_cross_jv(data, cur_cycl, company)

			# update advance doc
			paid_instlmnt = 0
			advance_doc = frappe.get_doc("Vlcc Advance",data.get('name'))
			advance_doc.append("cycle",{
				"cycle":cur_cycl,
				"sales_invoice": je_doc.name
				})
			advance_doc.outstanding_amount = data.get('advance_amount') - get_jv_amount(data, je_doc.company)
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

def  make_cross_jv(data, cur_cycl=None, company=None):
	vlcc_attr = frappe.db.get_value("Company", data.get('vlcc'), ['abbr','cost_center'],as_dict=1)
	je_doc = frappe.new_doc("Journal Entry")
	je_doc.voucher_type = "Journal Entry"
	je_doc.company = data.get('vlcc')
	je_doc.type = "Vlcc Advance"
	je_doc.cycle = cur_cycl
	je_doc.vlcc_advance = data.get('name')
	je_doc.posting_date = nowdate()
	je_doc.append('accounts', {
		'account': "Loans and Advances Payable - "+ vlcc_attr.get('abbr'),
		'debit_in_account_currency': data.get('emi_amount'),
		'party_type': "Supplier",
		'party': company.get('name'),
		'cost_center': vlcc_attr.get('cost_center')
		})
	je_doc.append('accounts', {
		'account': "Creditors - "+ vlcc_attr.get('abbr'),
		'credit_in_account_currency': data.get('emi_amount'),
		'cost_center': vlcc_attr.get('cost_center'),
		})
	je_doc.flags.ignore_permissions = True
	je_doc.save()
	je_doc.submit()

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

def get_jv_amount(data, company):
	sum_ = frappe.db.sql("""
			select ifnull(sum(total_debit),0) as total
		from 
			`tabJournal Entry` 
		where 
		vlcc_advance =%s and type = 'Vlcc Advance' and company = %s""",(data.get('name'),company),as_dict=1,debug=1)
	if len(sum_):
		return sum_[0].get('total') if sum_[0].get('total') != None else 0
	else: return 0