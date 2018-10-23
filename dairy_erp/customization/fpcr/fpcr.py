# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from dairy_erp.dairy_utils import make_dairy_log
from frappe.utils import flt, today, getdate, nowdate
from dairy_erp.dairy_erp.doctype.farmer_payment_cycle_report.farmer_payment_cycle_report\
import get_loans_child, get_advance_child, get_incentives

@frappe.whitelist()
def auto_fpcr():
	try:
		farmer_list = frappe.get_all("Farmer",['farmer_id','vlcc_name','full_name'])
		for farmer in farmer_list:
			cur_cycle = get_current_cycle(farmer)
			if len(cur_cycle):
				start_date = frappe.db.get_value("Farmer Date Computation", cur_cycle[0], 'start_date')
				end_date = frappe.db.get_value("Farmer Date Computation", cur_cycle[0], 'end_date')
				generate_fpcr(cur_cycle[0], farmer.get('farmer_id'), farmer.get('vlcc_name'), start_date, end_date)
	except Exception,e:
		make_dairy_log(title="Auto Fpcr Failed",method="auto_fpcr", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())

def get_current_cycle(data):
	# return frappe.db.sql("""
	# 		select name
	# 	from
	# 		`tabFarmer Date Computation`
	# 	where
	# 		vlcc = %s and date(now()) between start_date and end_date
	# 	""",(data.get('vlcc_name')),as_dict=1, debug=0)
	cycle_name = frappe.db.sql("""
			select name
		from
			`tabFarmer Date Computation`
		where
			 end_date < now() and vlcc = '{0}'
		order by end_date
		""".format(data.get('vlcc_name')),as_list=1,debug=0)

	return cycle_name[-1]

def generate_fpcr(cur_cycle, farmer, vlcc, start_date, end_date):
	total_bill, tota_qty = 0, 0
	fpcr_doc = frappe.new_doc("Farmer Payment Cycle Report")
	fpcr_doc.vlcc_name = vlcc
	fpcr_doc.date = nowdate()
	fpcr_doc.cycle = cur_cycle
	fpcr_doc.farmer_id = farmer

	fmcr = get_fmcr(cur_cycle, farmer, vlcc, start_date, end_date)
	loans = get_loans_child(start_date,end_date,vlcc,farmer,cur_cycle)
	advance = get_advance_child(start_date,end_date,vlcc,farmer,cur_cycle)

	if fmcr and not advance and not loans:
		for row in  fmcr:
			total_bill += row.get('amount')
			tota_qty += row.get('milkquantity')
			print "############",row.get('milkquantity')
			fpcr_doc.append('fmcr_details',{
				'amount': row.get('amount'),
				'date': row.get('rcvdtime'),
				'shift': row.get('shift'),
				'litres': row.get('milkquantity'),
				'fat': row.get('fat'),
				'snf': row.get('snf'),
				'rate': row.get('rate'),
			})

		# for row in get_loans_child(start_date,end_date,vlcc,farmer,cur_cycle):
		# 	fpcr_doc.append('loan_child',{
		# 		'loan_id': row.get('name'),
		# 		'principle': row.get('advance_amount'),
		# 		'outstanding': row.get('outstanding_amount'),
		# 		'emi_amount': row.get('emi_amount'),
		# 		'amount': row.get('emi_amount'),
		# 		'extension': row.get('extension'),
		# 		'paid_instalment': row.get('paid_instalment'),
		# 		'no_of_instalment': row.get('no_of_instalments')
		# 		})
		# for row in advance:
		# 	fpcr_doc.append('advance_child',{
		# 		'adv_id': row.get('name'),
		# 		'principle': row.get('advance_amount'),
		# 		'outstanding': row.get('outstanding_amount'),
		# 		'emi_amount': row.get('emi_amount'),
		# 		'amount': row.get('emi_amount'),
		# 		'extension': row.get('extension'),
		# 		'paid_instalment': row.get('paid_instalment'),
		# 		'no_of_instalment': row.get('no_of_instalment')
		# 	})		
		incentives = get_incentives(total_bill, tota_qty, vlcc)
		fpcr_doc.total_amount = total_bill
		fpcr_doc.incentives = incentives if incentives else 0
		fpcr_doc.total_bill = flt(total_bill) + flt(fpcr_doc.incentives)
		fpcr_doc.flags.ignore_permissions = True
		fpcr_doc.save()
		fpcr_doc.submit()


def get_fmcr(cur_cycle, farmer, vlcc, start_date, end_date):
	return  frappe.db.sql("""
			select rcvdtime,shift,milkquantity,fat,snf,rate,amount,name,associated_vlcc
		from 
			`tabFarmer Milk Collection Record`
		where 
			associated_vlcc = '{0}' and date(rcvdtime) between '{1}' and '{2}' and farmerid= '{3}'
			""".format(vlcc, start_date, end_date, farmer),as_dict=1,debug=0)