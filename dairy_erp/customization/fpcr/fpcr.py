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
				cur_date = getdate(nowdate())
				if end_date < cur_date:
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


def get_weighted_fmcr_data(fmcr_data):
	if len(fmcr_data) == 0:
		return
	milkquantity, fat, snf, rate, amount = 0, 0, 0, 0, 0

	for data in fmcr_data:
		milkquantity += data.get('milkquantity')
		fat += data.get('fat')*data.get('milkquantity')
		snf += data.get('snf')*data.get('milkquantity') 
		rate += data.get('rate')*data.get('milkquantity')
		amount += data.get('amount')

	fat, snf , rate = fat/milkquantity, snf/milkquantity, rate/milkquantity

	return {
		"milkquantity" : milkquantity,
		"fat" : fat,
		"snf" : snf,
		"rate": rate,
		"amount" : amount
	}

def generate_fpcr(cur_cycle, farmer, vlcc, start_date, end_date):
	total_bill, tota_qty = 0, 0
	fpcr_doc = frappe.new_doc("Farmer Payment Cycle Report")
	fpcr_doc.vlcc_name = vlcc
	fpcr_doc.date = nowdate()
	fpcr_doc.cycle = cur_cycle
	fpcr_doc.farmer_id = farmer
	fpcr_doc.collection_to = str(end_date)
	fpcr_doc.collection_from = str(start_date)

	fmcr = get_fmcr(cur_cycle, farmer, vlcc, start_date, end_date)
	loans = get_loans_child(start_date,end_date,vlcc,farmer,cur_cycle)
	advance = get_advance_child(start_date,end_date,vlcc,farmer,cur_cycle)

	if fmcr and not advance and not loans:
		# get weighted fmcr data
		weighted_fmcr_data = get_weighted_fmcr_data(fmcr)

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

		# generate weighted fmcr_details present in the bottom of the FMCR Table
		if len(fmcr) > 0:
	        fpcr_doc.append('fmcr_details', {
	                'amount' : weighted_fmcr_data.get('amount'),
	                'date' : '',
	                'shift' : '<b>Total Quantity</b>',
	                'litres' : weighted_fmcr_data.get('milkquantity'),
	                'fat' : weighted_fmcr_data.get('fat'),
	                'snf' : weighted_fmcr_data.get('snf'),
	                'rate' : weighted_fmcr_data.get('rate') 
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
