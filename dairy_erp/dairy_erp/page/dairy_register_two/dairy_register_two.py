from __future__ import unicode_literals
import frappe
import collections
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate,date_diff,add_days
from dairy_erp.dairy_erp.page.dairy_register_one.dairy_register_one import get_fmcr_list,fetch_farmer_data,get_local_sale_data

@frappe.whitelist()
def get_vmcr_data(start_date=None,end_date=None):
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")
	vlcc_addr = frappe.db.get_value("Village Level Collection Centre",vlcc,"address_display")
	vlcc_details = {'vlcc_addr':vlcc_addr,"vlcc":vlcc}
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
	# vmcr_data_list = get_vmcr_data_list(filters)
	good_milk = get_vmcr_data_list(filters,"Accept")
	bad_milk = get_vmcr_data_list(filters,"Reject")
	date_and_shift_wise_local_sale = {}
	vmcr_dict = {}
	vmcr_dict_ = {}

	for si in local_sale_list:
		local_sale_dict = {}
		if date_and_shift_wise_local_sale and str(si['posting_date'])+"#"+si['shift'] in date_and_shift_wise_local_sale:
			p = date_and_shift_wise_local_sale[str(si['posting_date'])+"#"+si['shift']]
			local_sale_dict['si_qty']  = flt(p.get('si_qty') + si.get('qty'),2)
			local_sale_dict['si_amount']  = flt(p.get('si_amount') + si.get('amount'),2)
			date_and_shift_wise_local_sale[str(si['posting_date'])+"#"+si['shift']] = local_sale_dict
		else:
			local_sale_dict = {
				"si_qty":si.get('qty'),
				"si_amount":si.get('amount')
			}
			date_and_shift_wise_local_sale[str(si['posting_date'])+"#"+si['shift']] = local_sale_dict
	
	for vmcr in good_milk:
		b_dict = {}
		if vmcr_dict and str(vmcr.get('vmcr_date'))+"#"+vmcr.get('shift') in vmcr_dict:
			p = vmcr_dict[str(vmcr.get('vmcr_date'))+"#"+vmcr.get('shift')]
			b_dict['fat'] = flt(p.get('fat')) + vmcr.get('fat')
			b_dict['snf'] = flt(p.get('snf')) + vmcr.get('snf')
			b_dict['vmcr_qty'] = flt(p.get('vmcr_qty')) + vmcr.get('vmcr_qty')
			b_dict['rate'] = flt(p.get('rate')) + vmcr.get('rate')
			b_dict['vmcr_amount'] = flt(p.get('vmcr_amount')) + vmcr.get('vmcr_amount')
			vmcr_dict[str(vmcr.get('vmcr_date'))+"#"+vmcr.get('shift')] = b_dict
		else:
			b_dict = {
				'fat':vmcr.get('fat'),
				'snf':vmcr.get('snf'),
				'rate':vmcr.get('rate'),
				'vmcr_qty':vmcr.get('vmcr_qty'),
				'vmcr_amount':vmcr.get('vmcr_amount')
			}
			vmcr_dict[str(vmcr['vmcr_date'])+"#"+vmcr['shift']] = b_dict

	for vmcr in bad_milk:
		b_dict = {}
		if vmcr_dict_ and str(vmcr.get('vmcr_date'))+"#"+vmcr.get('shift') in vmcr_dict_:
			p = vmcr_dict_[str(vmcr.get('vmcr_date'))+"#"+vmcr.get('shift')]
			b_dict['spoil_fat'] = flt(p.get('spoil_fat')) + vmcr.get('fat')
			b_dict['spoil_snf'] = flt(p.get('spoil_snf')) + vmcr.get('snf')
			b_dict['spoil_qty'] = flt(p.get('spoil_qty')) + vmcr.get('vmcr_qty')
			b_dict['spoil_rate'] = flt(p.get('spoil_rate')) + vmcr.get('rate')
			b_dict['spoil_amount'] = flt(p.get('spoil_amount')) + vmcr.get('vmcr_amount')
			vmcr_dict_[str(vmcr.get('vmcr_date'))+"#"+vmcr.get('shift')] = b_dict
		else:
			b_dict = {
				'spoil_fat':vmcr.get('fat'),
				'spoil_snf':vmcr.get('snf'),
				'spoil_rate':vmcr.get('rate'),
				'spoil_qty':vmcr.get('vmcr_qty'),
				'spoil_amount':vmcr.get('vmcr_amount'),
			}
			vmcr_dict_[str(vmcr['vmcr_date'])+"#"+vmcr['shift']] = b_dict

	milkquality_keys = vmcr_dict.keys()+vmcr_dict_.keys()
	milkquality_ = {}
	for key in set(milkquality_keys):
		if (vmcr_dict.get(key) or vmcr_dict_.get(key)):
			merged = {}
			merged.update(vmcr_dict.get(key,{'fat':0, 'snf':0, 'rate':0, 'vmcr_qty':0, 'vmcr_amount':0}))
			merged.update(vmcr_dict_.get(key,{'spoil_fat':0, 'spoil_snf':0, 'spoil_rate':0, 'spoil_qty':0, 'spoil_amount':0}))
			milkquality_[key] = merged			
	
	final_keys = members.keys()+date_and_shift_wise_local_sale.keys()+milkquality_.keys()
	final_dict = {}
	
	for key in set(final_keys):
		if (members.get(key) or date_and_shift_wise_local_sale.get(key) or milkquality_.keys()):
			merged = {}
			merged.update(members.get(key, {'total_milk_amt': 0,'total_milk_qty': 0}))
			merged.update(date_and_shift_wise_local_sale.get(key, {'si_amount': 0, 'si_qty': 0}))
			merged.update(milkquality_.get(key,{'spoil_fat':0, 'spoil_qty':0,'spoil_rate': 0, 'spoil_snf': 0, 'spoil_amount': 0,'snf':0, 'vmcr_qty':0,'rate': 0, 'fat': 0, 'vmcr_amount': 0,'shift':key.split('#')[1],'vmcr_date':key.split('#')[0]}))
			merged.update({'daily_sales':flt(merged.get('total_milk_qty')-merged.get('si_qty'),2)})
			merged.update({
				'short_qty':flt(merged.get('daily_sales') - merged.get('vmcr_qty'),2) if flt(merged.get('daily_sales') - merged.get('vmcr_qty'),2) > 0 else 0
				})
			merged.update({
				'excess_qty':flt(merged.get('vmcr_qty') - merged.get('daily_sales'),2) if flt(merged.get('vmcr_qty') - merged.get('daily_sales'),2) > 0 else 0
			})
			if ((merged.get('vmcr_amount') + merged.get('si_amount')) - merged.get('total_milk_amt')) > 0:
				merged.update({'profit': flt(((merged.get('vmcr_amount') + merged.get('si_amount')) - merged.get('total_milk_amt')),2)})
				merged.update({'loss': 0})
			if ((merged.get('vmcr_amount') + merged.get('si_amount')) - merged.get('total_milk_amt')) < 0:
				merged.update({'loss': flt(((merged.get('vmcr_amount') + merged.get('si_amount')) - merged.get('total_milk_amt')),2)})
				merged.update({'profit': 0})
			# if merged.get('total_milk_amt') > merged.get('vmcr_amount') + merged.get('si_amount'):
			# 	merged.update({'profit': flt(merged.get('total_milk_amt') - (merged.get('vmcr_amount')) + merged.get('si_amount'),2)})
			# 	merged.update({'loss': 0})
			# if merged.get('total_milk_amt') < merged.get('vmcr_amount') + merged.get('si_amount'):
			# 	merged.update({'loss':flt((merged.get('vmcr_amount') + merged.get('si_amount')) - merged.get('total_milk_amt'),2)})
			# 	merged.update({'profit': 0})
			formatted_date = key.split('#')[0].split('-')[2]+"-"+key.split('#')[0].split('-')[1]+"-"+key.split('#')[0].split('-')[0][-2::]
			merged.update({'vmcr_date':formatted_date})
			_shift = "aa"+key.split("#")[1] if key.split("#")[1] == "MORNING" else "ae"+key.split("#")[1]
			_key = key.split("#")[0]+"#"+_shift
			final_dict[_key] = merged
		else:
			pass
	final_dict = collections.OrderedDict(sorted(final_dict.items()))
	return {"final_dict":final_dict,"vlcc_details":vlcc_details}

def get_vmcr_data_list(filters,status):
	cond = " 1=1 and"
	if status == "Accept":
		cond = " vmcr.status = 'Accept' and vmcr.milkquality in ('G') and"
	vmcr_list = frappe.db.sql("""
								select
									vmcr.milkquantity as vmcr_qty,
									vmcr.fat,
									vmcr.snf,
									vmcr.rate,
									vmcr.amount as vmcr_amount,
									date(vmcr.collectiontime) as vmcr_date,
									vmcr.shift,
									vmcr.milkquality,
									vmcr.status
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									{0}
									vmcr.shift in ('MORNING','EVENING') and
									{1} """.format(cond,get_conditions(filters)),as_dict=1,debug=1)	
	if status == "Reject":
		cond = " vmcr.status = 'Reject' and vmcr.milkquality in ('CT','CS','SS') and"	
		vmcr_list = frappe.db.sql("""
								select
									vmcr.milkquantity as vmcr_qty,
									vmcr.fat*vmcr.milkquantity as fat,
									vmcr.snf*vmcr.milkquantity as snf,
									vmcr.rate,
									vmcr.amount as vmcr_amount,
									date(vmcr.collectiontime) as vmcr_date,
									vmcr.shift,
									vmcr.milkquality,
									vmcr.status
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									{0}
									vmcr.shift in ('MORNING','EVENING') and
									{1} """.format(cond,get_conditions(filters)),as_dict=1,debug=1)	
	return vmcr_list

def get_conditions(filters):
	cond = "1=1"
	if filters.get('operator_type') == "VLCC":
		cond += " and vmcr.associated_vlcc = '{0}' """.format(filters.get('vlcc'))
	if filters.get('start_date') and filters.get('end_date'):
		cond += " and date(vmcr.collectiontime) between '{0}' and '{1}'".format(filters.get('start_date'),filters.get('end_date'))
	return cond