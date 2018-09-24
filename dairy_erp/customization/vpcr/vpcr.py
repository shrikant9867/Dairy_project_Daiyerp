# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from dairy_erp.dairy_utils import make_dairy_log
from frappe.utils import flt, today, getdate, nowdate
from dairy_erp.customization.vlcc_loan.vlcc_loan import get_current_cycle
from dairy_erp.dairy_erp.doctype.vlcc_payment_cycle_report.vlcc_payment_cycle_report\
import get_vlcc_loans_child,get_vlcc_advance_child,get_incentives


def auto_vpcr():
	try:
		vlcc_list = frappe.get_all("Village Level Collection Centre", 'name')
		for vlcc in vlcc_list:
			current_pc = get_current_cycle()
			if len(current_pc):
				is_vpcr = frappe.db.get_value("VLCC Payment Cycle Report", {'cycle': current_pc[0].get('name'), 'vlcc_name': vlcc.get('name')})
				if not is_vpcr:
					start_date = frappe.db.get_value("Cyclewise Date Computation", cur_cycle[0].get('name'), 'start_date')
					end_date = frappe.db.get_value("Cyclewise Date Computation", cur_cycle[0].get('name'), 'end_date')
					generate_vpcr(current_pc[0].get('name'), vlcc.get('name'),start_date,end_date)
	except Exception,e:
		make_dairy_log(title="Sync failed for Data push",method="get_items", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())

def generate_vpcr(cur_cycle, vlcc, start_date, end_date):
	total_bill, tota_qty = 0, 0
	vpcr_doc = frappe.new_doc("VLCC Payment Cycle Report")
	vpcr_doc.vlcc_name = vlcc
	vpcr_doc.date = nowdate()
	vpcr_doc.cycle = cur_cycle
	# vpcr_doc.farmer_id = farmer
	for row in  get_vmcr_data(cur_cycle, vlcc, start_date, end_date):
		total_bill += row.get('amount')
		tota_qty += row.get('milkquantity')
		vpcr_doc.append('vmcr_details',{
			'amount': row.get('amount'),
			'date': row.get('rcvdtime'),
			'shift': row.get('shift'),
			'milkquantity': row.get('milkquantity'),
			'fat': row.get('fat'),
			'snf': row.get('snf'),
			'rate': row.get('rate'),
		})
	for row in get_vlcc_loans_child(start_date,end_date,vlcc,cur_cycle):
		vpcr_doc.append('vlcc_loan_child',{
			'loan_id': row.get('name'),
			'principle': row.get('advance_amount'),
			'outstanding': row.get('outstanding_amount'),
			'emi_amount': row.get('emi_amount'),
			'amount': row.get('emi_amount'),
			'extension': row.get('extension'),
			'paid_instalment': row.get('paid_instalment'),
			'no_of_instalment': row.get('no_of_instalments')
			})
	for row in get_vlcc_advance_child(start_date,end_date,vlcc,cur_cycle):
		vpcr_doc.append('vlcc_advance_child',{
			'adv_id': row.get('name'),
			'principle': row.get('advance_amount'),
			'outstanding': row.get('outstanding_amount'),
			'emi_amount': row.get('emi_amount'),
			'amount': row.get('emi_amount'),
			'extension': row.get('extension'),
			'paid_instalment': row.get('paid_instalment'),
			'no_of_instalment': row.get('no_of_instalment')
			})
	incentives = get_incentives(total_bill, tota_qty, vlcc)
	vpcr_doc.incentives = incentives if incentives else 0
	vpcr_doc.flags.ignore_permissions = True
	vpcr_doc.save()
	vpcr_doc.submit()
	print "#################",get_incentives(total_bill, tota_qty, vlcc),farmer
	

def get_vmcr_data(cur_cycle, vlcc,start_date,end_date):
	vmcr =  frappe.db.sql("""
			select rcvdtime,shift,milkquantity,fat,snf,rate,amount
		from 
			`tabVlcc Milk Collection Record`
		where 
			associated_vlcc = '{0}' and date(rcvdtime) between '{1}' and '{2}'
			""".format(vlcc, start_date, end_date),as_dict=1,debug=0)
