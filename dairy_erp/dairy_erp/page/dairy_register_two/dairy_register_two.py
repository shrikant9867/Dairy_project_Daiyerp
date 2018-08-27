from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate,date_diff,add_days
from dairy_erp.dairy_erp.page.dairy_register_one.dairy_register_one import get_fmcr_list,fetch_farmer_data,get_local_sale_data

@frappe.whitelist()
def get_vmcr_data(start_date=None,end_date=None):
	# return start_date,end_date
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")
	filters = {
		"start_date":start_date,
		"end_date":end_date,
		"shift":"Both",
		'vlcc':vlcc,
		'from_report':"Dairy Register 2",
		'operator_type':'VLCC'
	}
	fmcr_list = get_fmcr_list(filters)
	local_sale_list = get_local_sale_data(filters)
	members = fetch_farmer_data(fmcr_list,filters)
	vmcr_data_list = get_vmcr_data_list(filters)
	date_and_shift_wise_local_sale = {}
	vmcr_dict = {}
	for si in local_sale_list:
		local_sale_dict = {}
		if date_and_shift_wise_local_sale and str(si['posting_date'])+"#"+si['shift'] in date_and_shift_wise_local_sale:
			p = date_and_shift_wise_local_sale[str(si['posting_date'])+"#"+si['shift']]
			local_sale_dict['si_qty']  = p.get('si_qty') + si.get('qty')
			local_sale_dict['si_amount']  = p.get('si_amount') + si.get('amount')
			date_and_shift_wise_local_sale[str(si['posting_date'])+"#"+si['shift']] = local_sale_dict
		else:
			local_sale_dict = {
				"si_qty":si.get('qty'),
				"si_amount":si.get('amount')
			}
			date_and_shift_wise_local_sale[str(si['posting_date'])+"#"+si['shift']] = local_sale_dict
	
		for vmcr in vmcr_data_list:
			vmcr_dict[str(vmcr['vmcr_date'])+"#"+vmcr['shift']] = vmcr

	print "vmcr_dict\n\n\n",vmcr_dict
	final_keys = members.keys()+date_and_shift_wise_local_sale.keys()+vmcr_dict.keys()
	final_dict = {}
	
	for key in set(final_keys):
		if (members.get(key) or date_and_shift_wise_local_sale.get(key) or vmcr_dict.keys()):
			merged = {}
			merged.update(members.get(key, {'total_milk_amt': 0,'total_milk_qty': 0}))
			merged.update(date_and_shift_wise_local_sale.get(key, {'si_amount': 0, 'si_qty': 0}))
			merged.update(vmcr_dict.get(key,{'snf':0, 'vmcr_qty':0,'rate': 0, 'fat': 0, 'vmcr_amount': 0,'shift':key.split('#')[1],'vmcr_date':key.split('#')[0]}))
			merged.update({'daily_sales':merged.get('total_milk_qty')-merged.get('si_qty')})		
			merged.update({'excess_qty':merged.get('daily_sales') - merged.get('vmcr_qty')})
			merged.update({'short_qty':merged.get('vmcr_qty') - merged.get('daily_sales')})
			if merged.get('vmcr_amount') + merged.get('si_amount') > merged.get('total_milk_amt'):
				merged.update({'profit': (merged.get('vmcr_amount') + merged.get('si_amount')) - merged.get('total_milk_amt')})
				merged.update({'loss': 0})
			if merged.get('vmcr_amount') + merged.get('si_amount') < merged.get('total_milk_amt'):
				merged.update({'loss': merged.get('total_milk_amt') - (merged.get('vmcr_amount') + merged.get('si_amount'))})
				merged.update({'profit': 0})
			final_dict[key] = merged
		else:
			pass
	
	# print "vmcr_data_list\n\n\n\n",vmcr_data_list		
	print "final_dict\n\n\n",final_dict
	return final_dict

def get_vmcr_data_list(filters):
	vmcr_list = frappe.db.sql("""
								select
									vmcr.milkquantity as vmcr_qty,
									vmcr.fat,
									vmcr.snf,
									vmcr.rate,
									vmcr.amount as vmcr_amount,
									date(vmcr.collectiondate) as vmcr_date,
									vmcr.shift
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									vmcr.shift in ('MORNING','EVENING') and
									{0} """.format(get_conditions(filters)),as_dict=1,debug=1)	
	return vmcr_list

def get_conditions(filters):
	cond = "1=1"
	if filters.get('operator_type') == "VLCC":
		cond += " and vmcr.associated_vlcc = '{0}' """.format(filters.get('vlcc'))
	if filters.get('start_date') and filters.get('end_date'):
		cond += " and date(vmcr.collectiondate) between '{0}' and '{1}'".format(filters.get('start_date'),filters.get('end_date'))
	return cond