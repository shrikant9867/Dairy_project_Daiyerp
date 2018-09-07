# -*- coding: utf-8 -*-


from __future__ import unicode_literals
import frappe
import json
from six import string_types
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
	
	SmartAMCU = {}
	local_sale_data = get_local_sale_data(filters,"smartamcu")
	l_sale_date_shift = {}
	fmcr_data = get_fmcr_data(filters)
	fmcr_date_shift = {}
	vmcr_data = get_vmcr_data(filters)
	vmcr_date_shift = {}

	for vmcr in vmcr_data:
		vmcr_date_shift[str(vmcr['vmcr_date'])+"#"+vmcr['shift']] = vmcr

	for fmcr in fmcr_data:
		_fmcr = {}
		if fmcr_date_shift and str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift') in fmcr_date_shift:
			pp = fmcr_date_shift.get(str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift'))
			_fmcr['count'] = pp.get('count') + 1
			_fmcr['fmcr_qty'] = pp.get('fmcr_qty') + fmcr.get('fmcr_qty')
			_fmcr['grand_total'] = pp.get('grand_total') + fmcr.get('fmcr_amount')
			_fmcr['w_fat'] = flt((pp.get('w_fat') + fmcr.get('fmcr_fat'))/_fmcr.get('fmcr_qty'),2)
			_fmcr['w_snf'] = flt((pp.get('w_snf') + fmcr.get('fmcr_snf'))/_fmcr.get('fmcr_qty'),2)
			fmcr_date_shift[str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift')] = _fmcr
		else:
			_fmcr = {'count':1,
					'fmcr_qty':fmcr.get('fmcr_qty'),
					'grand_total':fmcr.get('fmcr_amount'),
					'w_fat':fmcr.get('fmcr_fat'),
					'w_snf':fmcr.get('fmcr_snf'),
					'diff':" "
					}
			fmcr_date_shift[str(fmcr.get('fmcr_date'))+"#"+fmcr.get('shift')] = _fmcr
	
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

	final_keys = fmcr_date_shift.keys()+vmcr_date_shift.keys()+l_sale_date_shift.keys() 		
	final_dict = {}
	for key in set(final_keys):
		if (fmcr_date_shift.get(key) or vmcr_date_shift.get(key) or l_sale_date_shift.get(key)):
			merged = {}
			merged.update(fmcr_date_shift.get(key,{'count':'-','fmcr_qty':'-','diff':' ','grand_total':"-",'w_snf':'-','w_fat':'-'}))
			merged.update(l_sale_date_shift.get(key,{'si_qty':'-','si_grand_total':'-'}))
			merged.update(vmcr_date_shift.get(key,{"vmcr_qty":'-','vmcr_fat':'-','vmcr_snf':'-','vmcr_rate':'-','vmcr_amount':'-'}))
		final_dict[key] = merged

	# smartamcu = {"fmcr":fmcr_date_shift,'local_sale':l_sale_date_shift}
	return final_dict

def get_fmcr_data(filters):
	fmcr_list = frappe.db.sql("""
								select
									fmcr.name,
									fmcr.milkquantity as fmcr_qty,
									fmcr.amount as fmcr_amount,
									date(fmcr.collectiontime) as fmcr_date,
									fmcr.shift as shift,
									fmcr.fat*fmcr.milkquantity as fmcr_fat,
									fmcr.snf*fmcr.milkquantity as fmcr_snf
								from
									`tabFarmer Milk Collection Record` fmcr
								where
									fmcr.docstatus = 1 and
									fmcr.shift in ('MORNING','EVENING')
									{0} order by fmcr.collectiontime """.format(get_fmcr_conditions(filters)),as_dict=1,debug=0)
	return fmcr_list

def get_fmcr_conditions(filters):
	cond = " and 1=1"
	if filters.get('cc') and filters.get('vlcc_list'):
		cond = "and fmcr.associated_vlcc in {0} """.format(filters.get('vlcc_list'))
	if filters.get('from_date') and filters.get('to_date'):
		cond += " and date(fmcr.collectiontime) between '{0}' and '{1}'".format(filters.get('from_date'),filters.get('to_date'))
	return cond

def get_vmcr_data(filters):
	vmcr_list = frappe.db.sql("""
								select
									vmcr.milkquantity as vmcr_qty,
									vmcr.fat as vmcr_fat,
									vmcr.snf as vmcr_snf,
									vmcr.rate as vmcr_rate,
									vmcr.amount as vmcr_amount,
									date(vmcr.collectiontime) as vmcr_date,
									vmcr.shift
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									vmcr.shift in ('MORNING','EVENING')
									{0} order by vmcr.collectiontime """.format(get_vmcr_conditions(filters)),as_dict=1,debug=1)
	return vmcr_list

def get_vmcr_conditions(filters):
	cond = " and 1=1"	
	if filters.get('cc') and filters.get('vlcc_list'):
		cond = "and vmcr.associated_vlcc in {0} """.format(filters.get('vlcc_list'))
	if filters.get('start_date') and filters.get('end_date'):
		cond += " and date(vmcr.collectiontime) between '{0}' and '{1}'".format(filters.get('start_date'),filters.get('end_date'))
	return cond


@frappe.whitelist()
def get_xlsx(data=None):
	# print data,"data___________________________"
	data_row = [
		["Date","Session","SmartAMCU","","","SmartERP – Society","","","","","","","","","","","","","SmartERP – Dairy","","","","","","",""],
		["","","No of Records","Qty","Amt.","FMCR","","","Purchase Invoice","","","Local Sale","","Milk Sold to Dairy","","","General Test","","VMCR","","","","","","",""],
		["","","","","","No.","Qty.","Diff.","No","Amt.","Diff.","Qty","Amt.","Qty","Fat","SNF","Fat","SNF","Qty","Qty Diff.","Fat","Fat Diff.","SNF","SNF Diff.","Rate","Amt."]
	]	
	# data = json.loads(data)
	# for row in data:
	# 	print row,"row__________"
	# 	val = data[row]
	# 	if val.get('fmcr_qty') >= 0 and val.get('si_qty') >= 0 and type(val.get('si_qty')) is float and type(val.get('fmcr_qty')) is float:
	# 		val["sold_qty"] = flt(val.get('fmcr_qty') - val.get('si_qty'),2)
	# 		if val.get('vmcr_qty') >= 0 and type(val.get('vmcr_qty')) is float:
	# 			val["vmcr_qty_diff"] = flt(val.get('sold_qty') - val.get('vmcr_qty'),2)
	# 		if val.get('vmcr_qty') == "-":
	# 			val["vmcr_qty_diff"] = val.get('sold_qty')
	# 	if val.get('fmcr_qty') >= 0 and val.get('si_qty') == "-" and type(val.get('fmcr_qty')) is float:
	# 		val["sold_qty"] = val.get('fmcr_qty')
	# 		if val.get('vmcr_qty') >= 0 and type(val.get('vmcr_qty')) is float:
	# 			val["vmcr_qty_diff"] = flt(val.get('sold_qty') - val.get('vmcr_qty'),2)
	# 		if val.get('vmcr_qty') == "-":
	# 			val["vmcr_qty_diff"] = val.get('sold_qty')
	# 	if val.get('fmcr_qty') == "-" and val.get('si_qty') >= 0 and type(val.get('si_qty')) is float:
	# 		val["sold_qty"] = "-"
	# 		val["vmcr_qty_diff"] = "-" 	
	# 	data_row.append([row.split("#")[0],row.split("#")[1],"","","",val.get('count'),val.get('fmcr_qty'),"",val.get('count'),val.get('grand_total'),"",val.get("si_qty"),val.get("si_grand_total"),val.get("sold_qty"),val.get("w_fat"),val.get("w_snf"),"","",val.get("vmcr_qty"),"",val.get("vmcr_fat"),"",val.get("vmcr_snf"),"",val.get("vmcr_rate"),val.get("vmcr_amount")])
	xlsx_file = make_xlsx(data_row, "Admin Report")
	frappe.response['filename'] = "Admin Report" + '.xlsx'
	frappe.response['filecontent'] = xlsx_file.getvalue()
	frappe.response['type'] = 'binary'