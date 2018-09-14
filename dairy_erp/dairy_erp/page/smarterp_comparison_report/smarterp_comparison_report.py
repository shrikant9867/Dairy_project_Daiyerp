# -*- coding: utf-8 -*-


from __future__ import unicode_literals
import frappe
import json
from six import string_types
import collections
from frappe.utils.xlsxutils import make_xlsx
from dairy_erp.dairy_erp.page.dairy_register_one.dairy_register_one import get_local_sale_data
from frappe.utils import flt, cstr, cint

@frappe.whitelist()
def get_data(filters=None):
	filters = json.loads(filters)
	cc_vlcc_details = {}
	cc = frappe.db.get_value("Address",{'name':filters.get('cc')},['centre_id','manager_name'],as_dict=1)
	vlcc = frappe.db.get_value("Village Level Collection Centre",{'name':filters.get('vlcc')},['amcu_id','name1'],as_dict=1)
	if cc and vlcc:
		cc_vlcc_details = {'vlcc_name':vlcc.get('name1'),
							'vlcc_id':vlcc.get('amcu_id'),
							"cc_name":cc.get('manager_name'),
							"cc_id":cc.get('centre_id')
		}
	
	filters.update({
		'vlcc_list':"(" + ",".join([ "'{0}'".format(vlcc.get('name')) for vlcc in frappe.get_all("Village Level Collection Centre", filters=[("chilling_centre", "=", filters.get('cc'))]) ]) + ")",
		'start_date':filters.get('from_date'),
		'end_date':filters.get('to_date')
	})	

	l_sale_date_shift = {}
	fmcr_date_shift = {}
	vmcr_date_shift = {}
	local_sale_data = get_local_sale_data(filters,"smartamcu")
	fmcr_data = get_fmcr_data(filters)
	vmcr_data = get_vmcr_data(filters)

	for si in local_sale_data:
		_si = {}
		if l_sale_date_shift and str(si.get('posting_date'))+"#"+si.get('shift') in l_sale_date_shift:
			pp = l_sale_date_shift[str(si.get('posting_date'))+"#"+si.get('shift')]
			_si['si_qty'] = flt(si.get('qty') + pp.get('si_qty'),2)
			_si['si_grand_total'] = flt(si.get('amount') + pp.get('si_grand_total'),2)
			l_sale_date_shift[str(si.get('posting_date'))+"#"+si.get('shift')] = _si
		else:
			_si = {
					'si_qty':si.get('qty'),
					'si_grand_total':si.get('amount')
			}
			l_sale_date_shift[str(si.get('posting_date'))+"#"+si.get('shift')] = _si

	for fmcr in fmcr_data:
		_fmcr = {}
		if fmcr_date_shift and str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift') in fmcr_date_shift:
			pp = fmcr_date_shift.get(str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift'))
			_fmcr['count'] = pp.get('count') + 1
			_fmcr['fmcr_qty'] = pp.get('fmcr_qty') + fmcr.get('fmcr_qty')
			_fmcr['grand_total'] = pp.get('grand_total') + fmcr.get('fmcr_amount')
			_fmcr['w_fat'] = pp.get('w_fat') + fmcr.get('fmcr_fat')
			_fmcr['w_snf'] = pp.get('w_snf') + fmcr.get('fmcr_snf')
			_fmcr['milk_sold_qty'] = pp.get('milk_sold_qty') + fmcr.get('fmcr_qty')
			fmcr_date_shift[str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift')] = _fmcr
		else:
			_fmcr = {'count':1,
					'fmcr_qty':fmcr.get('fmcr_qty'),
					'grand_total':fmcr.get('fmcr_amount'),
					'w_fat':fmcr.get('fmcr_fat'),
					'w_snf':fmcr.get('fmcr_snf'),
					'diff':" "
					}
			if l_sale_date_shift.get(str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift')):
				_fmcr['milk_sold_qty'] = fmcr.get('fmcr_qty') - l_sale_date_shift.get(str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift')).get('si_qty')
			else:
				_fmcr['milk_sold_qty'] = _fmcr['fmcr_qty']
			fmcr_date_shift[str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift')] = _fmcr

	for vmcr in vmcr_data:
		d_s = str(vmcr.get('vmcr_date'))+"#"+vmcr.get('shift')
		vmcr["vmcr_qty_diff"] = flt(fmcr_date_shift.get(d_s).get('milk_sold_qty') - vmcr['vmcr_qty'],2) if fmcr_date_shift.get(d_s) else - vmcr['vmcr_qty']
		vmcr["vmcr_fat_diff"] = flt(fmcr_date_shift.get(d_s).get('w_fat') - vmcr['vmcr_fat'],2) if fmcr_date_shift.get(d_s) else - vmcr['vmcr_fat']
		vmcr["vmcr_snf_diff"] = flt(fmcr_date_shift.get(d_s).get('w_snf') - vmcr['vmcr_snf'],2) if fmcr_date_shift.get(d_s) else - vmcr['vmcr_snf']
		vmcr_date_shift[str(vmcr['vmcr_date'])+"#"+vmcr['shift']] = vmcr
			

	final_keys = fmcr_date_shift.keys()+vmcr_date_shift.keys()+l_sale_date_shift.keys() 		
	final_dict = {}
	for key in set(final_keys):
		if (fmcr_date_shift.get(key) or vmcr_date_shift.get(key) or l_sale_date_shift.get(key)):
			merged = {}
			merged.update(fmcr_date_shift.get(key,{'count':'','fmcr_qty':'','diff':' ','grand_total':"",'w_snf':'','w_fat':'','milk_sold_qty':''}))
			merged.update(l_sale_date_shift.get(key,{'si_qty':'','si_grand_total':''}))
			if fmcr_date_shift.get(key):	
				merged.update(vmcr_date_shift.get(key,{"vmcr_qty":'','vmcr_fat':'','vmcr_snf':'','vmcr_rate':'','vmcr_amount':'','vmcr_qty_diff':-fmcr_date_shift.get(key).get('milk_sold_qty'),'vmcr_fat_diff':-flt(fmcr_date_shift.get(key).get('w_fat')/fmcr_date_shift.get(key).get('fmcr_qty'),2),'vmcr_snf_diff':-flt(fmcr_date_shift.get(key).get('w_snf')/fmcr_date_shift.get(key).get('fmcr_qty'),2)}))
			else:
				merged.update(vmcr_date_shift.get(key,{"vmcr_qty":'','vmcr_fat':'','vmcr_snf':'','vmcr_rate':'','vmcr_amount':'','vmcr_qty_diff':'','vmcr_fat_diff':'','vmcr_snf_diff':''}))				
			# key = key.split('#')[0].split('-')[2]+"-"+key.split('#')[0].split('-')[1]+"-"+key.split('#')[0].split('-')[0][-2::]+"#"+key.split('#')[1]
			# final_dict[key] = merged
		final_dict[key] = merged

	# for key in final_dict:
	# 	row = key
	# 	key = key.split('#')[0].split('-')[2]+"-"+key.split('#')[0].split('-')[1]+"-"+key.split('#')[0].split('-')[0][-2::]+"#"+key.split('#')[1]
	# 	final_dict[key] = final_dict[row]	
		
	final_dict = collections.OrderedDict(sorted(final_dict.items()))	
	return {'final_dict':final_dict,'cc_vlcc_details':cc_vlcc_details}

def get_fmcr_data(filters):
	fmcr_list = frappe.db.sql("""
								select
									fmcr.name,
									ifnull(fmcr.milkquantity,0) as fmcr_qty,
									ifnull(fmcr.amount,0) as fmcr_amount,
									date(fmcr.collectiontime) as fmcr_date,
									fmcr.shift as shift,
									ifnull(fmcr.fat*fmcr.milkquantity,0) as fmcr_fat,
									ifnull(fmcr.snf*fmcr.milkquantity,0) as fmcr_snf
								from
									`tabFarmer Milk Collection Record` fmcr
								where
									fmcr.docstatus = 1 and
									fmcr.shift in ('MORNING','EVENING')
									{0} order by fmcr.collectiontime """.format(get_fmcr_conditions(filters)),as_dict=1,debug=0)
	return fmcr_list

def get_fmcr_conditions(filters):
	cond = " and 1=1"
	if filters.get('cc') and filters.get('vlcc'):
		cond = "and fmcr.associated_vlcc = '{0}' """.format(filters.get('vlcc'))
	if filters.get('from_date') and filters.get('to_date'):
		cond += " and date(fmcr.collectiontime) between '{0}' and '{1}'".format(filters.get('from_date'),filters.get('to_date'))
	return cond

def get_vmcr_data(filters):
	vmcr_list = frappe.db.sql("""
								select
									ifnull(vmcr.milkquantity,0) as vmcr_qty,
									ifnull(vmcr.fat,0) as vmcr_fat,
									ifnull(vmcr.snf,0) as vmcr_snf,
									ifnull(vmcr.rate,0) as vmcr_rate,
									ifnull(vmcr.amount,0) as vmcr_amount,
									date(vmcr.collectiontime) as vmcr_date,
									vmcr.shift
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									vmcr.shift in ('MORNING','EVENING')
									{0} order by vmcr.collectiontime """.format(get_vmcr_conditions(filters)),as_dict=1,debug=0)
	return vmcr_list

def get_vmcr_conditions(filters):
	cond = " and 1=1"	
	if filters.get('cc') and filters.get('vlcc'):
		cond = "and vmcr.associated_vlcc = '{0}' """.format(filters.get('vlcc'))
	if filters.get('start_date') and filters.get('end_date'):
		cond += " and date(vmcr.collectiontime) between '{0}' and '{1}'".format(filters.get('start_date'),filters.get('end_date'))
	return cond


@frappe.whitelist()
def get_xlsx(data=None):
	raw_data = json.loads(data)
	data = raw_data.get('amcu_data')
	data = collections.OrderedDict(sorted(data.items()))
	cc_vlcc_details = raw_data.get('cc_vlcc_details')
	data_row = [
		["CC ID",cc_vlcc_details.get('cc_id'),"","","","","","CC Name",cc_vlcc_details.get('cc_name')],
		["VLCC ID",cc_vlcc_details.get('vlcc_id'),"","","","","","VLCC Name",cc_vlcc_details.get('vlcc_name')],
		["SmartAMCU - SmartERP Comparison Report"],
		["Date","Session","SmartAMCU","","","SmartERP – Society","","","","","","","","","","","","","SmartERP – Dairy","","","","","","",""],
		["","","No of Records","Qty","Amt.","FMCR","","","Purchase Invoice","","","Local Sale","","Milk Sold to Dairy","","","General Test","","VMCR","","","","","","",""],
		["","","","","","No.","Qty.","Diff.","No","Amt.","Diff.","Qty","Amt.","Qty","Fat","SNF","Fat","SNF","Qty","Qty Diff.","Fat","Fat Diff.","SNF","SNF Diff.","Rate","Amt."]
	]	
	for row in data:
		val = data[row]
		date_ = row.split('#')[0].split('-')[2]+"-"+row.split('#')[0].split('-')[1]+"-"+row.split('#')[0].split('-')[0][-2::]
		if val.get("fmcr_qty"):
			data_row.append([date_,row.split("#")[1][0],"","","",val.get('count'),val.get('fmcr_qty'),"",val.get('count'),val.get('grand_total'),"",val.get("si_qty"),val.get("si_grand_total"),val.get('milk_sold_qty'),flt(val.get('w_fat')/val.get('fmcr_qty'),2),flt(val.get('w_snf')/val.get('fmcr_qty'),2),"","",val.get("vmcr_qty"),val.get("vmcr_qty_diff"),val.get("vmcr_fat"),val.get('vmcr_fat_diff'),val.get("vmcr_snf"),val.get("vmcr_snf_diff"),val.get("vmcr_rate"),val.get("vmcr_amount")])
		else:
			data_row.append([date_,row.split("#")[1][0],"","","",val.get('count'),val.get('fmcr_qty'),"",val.get('count'),val.get('grand_total'),"",val.get("si_qty"),val.get("si_grand_total"),val.get('milk_sold_qty'),"","","","",val.get("vmcr_qty"),val.get("vmcr_qty_diff"),val.get("vmcr_fat"),val.get('vmcr_fat_diff'),val.get("vmcr_snf"),val.get("vmcr_snf_diff"),val.get("vmcr_rate"),val.get("vmcr_amount")])
	xlsx_file = make_xlsx(data_row, "Admin Report")
	frappe.response['filename'] = "Admin Report" + '.xlsx'
	frappe.response['filecontent'] = xlsx_file.getvalue()
	frappe.response['type'] = 'binary'