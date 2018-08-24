from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate,date_diff,add_days

@frappe.whitelist()
def get_fmcr_data(start_date=None,end_date=None):
	start_date,end_date
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")
	filters = {
		"start_date":start_date,
		"end_date":end_date,
		"shift":"Both",
		'vlcc':vlcc
	}

	fmcr_list = get_fmcr_list(filters)
	local_sale_list = get_local_sale_data(filters)
	sample_local_sale_list = get_sample_sale_data(filters)
	# date_and_shift_wise_fmcr = {}
	date_and_shift_wise_local_sale = {}
	date_and_shift_wise_sample_local_sale = {}
	# for fmcr in fmcr_list:
	# 	if date_and_shift_wise_fmcr and str(fmcr['date'])+"#"+fmcr['shift'] in date_and_shift_wise_fmcr:
	# 		date_and_shift_wise_fmcr[str(fmcr['date'])+"#"+fmcr['shift']].append(fmcr['name']+"@"+fmcr['farmerid'])
	# 	else:
	# 		date_and_shift_wise_fmcr[str(fmcr['date'])+"#"+fmcr['shift']] = [fmcr['name']+"@"+fmcr['farmerid']]
	
	
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

	for stock_entry in sample_local_sale_list:
		sample_sale_dict = {}
		if date_and_shift_wise_sample_local_sale and str(stock_entry['posting_date'])+"#"+stock_entry['shift'] in date_and_shift_wise_sample_local_sale:
			pp = date_and_shift_wise_sample_local_sale[str(stock_entry['posting_date'])+"#"+stock_entry['shift']]
			sample_sale_dict['stock_qty']  = pp.get('stock_qty') + stock_entry.get('qty')
			sample_sale_dict['stock_amount']  = pp.get('stock_amount') + stock_entry.get('amount')
			date_and_shift_wise_sample_local_sale[str(stock_entry['posting_date'])+"#"+stock_entry['shift']] = sample_sale_dict
		else:
			sample_sale_dict = {
				"stock_qty":stock_entry.get('qty'),
				"stock_amount":stock_entry.get('amount')
			}
			date_and_shift_wise_sample_local_sale[str(stock_entry['posting_date'])+"#"+stock_entry['shift']] = sample_sale_dict
	
	# members = fetch_farmer_data(date_and_shift_wise_fmcr,filters)
	members = fetch_farmer_data(fmcr_list,filters)
	final_keys = members.keys()+date_and_shift_wise_local_sale.keys()+date_and_shift_wise_sample_local_sale.keys()
	final_dict = {}
	
	for key in set(final_keys):
		if (members.get(key) or date_and_shift_wise_local_sale.get(key)
			or date_and_shift_wise_sample_local_sale.get(key)):
			merged = {}
			merged.update(members.get(key, {'member_qty': '-','total_milk_amt': '-', 'non_member_count': '-', 'date': key.split('#')[0], 'member_count': '-', 'member_amt': '-', 'shift': key.split('#')[1], 'non_member_amt': '-', 'non_member_qty': '-', 'total_milk_qty': '-'}))
			merged.update(date_and_shift_wise_local_sale.get(key, {'si_amount': "-", 'si_qty': "-"}))
			merged.update(date_and_shift_wise_sample_local_sale.get(key, {'stock_amount': "-", 'stock_qty': "-"}))
			final_dict[key] = merged
		
	return final_dict

def fetch_farmer_data(fmcr_data,filters):
	final_ = {}
	date_and_shift_wise_fmcr = {}
	for fmcr in fmcr_data:
		if date_and_shift_wise_fmcr and str(fmcr['date'])+"#"+fmcr['shift'] in date_and_shift_wise_fmcr:
			date_and_shift_wise_fmcr[str(fmcr['date'])+"#"+fmcr['shift']].append(fmcr['name']+"@"+fmcr['farmerid'])
		else:
			date_and_shift_wise_fmcr[str(fmcr['date'])+"#"+fmcr['shift']] = [fmcr['name']+"@"+fmcr['farmerid']]
	
	for row in date_and_shift_wise_fmcr:
		farmer_list = []
		for fmcr in date_and_shift_wise_fmcr[row]:
			farmer_list.append(fmcr.split('@')[1])
			filters.update({
				'date':row.split('#')[0],
				'shift':row.split('#')[1]
				})
		final_[row] = get_member_non_menber(farmer_list,filters)
	return final_

def get_member_non_menber(farmer_list,filters):
	print filters,"inside get_member_non_menber\n\n"
	non_member_count,member_count,non_member_qty,member_qty,member_amt,non_member_amt = 0 , 0 , 0, 0,0,0
	member_dict = {}
	if farmer_list:
		for farmer in set(farmer_list):
			farmer_id = frappe.db.get_value("Farmer",farmer,["registration_date","is_member"],as_dict=1)
			months_to_member = frappe.db.get_value("VLCC Settings",{"vlcc":filters.get('vlcc')},"months_to_member")
			if farmer_id and months_to_member:
				date_ = add_months(getdate(farmer_id.get('registration_date')),months_to_member)
				if getdate() < date_  and not farmer_id.get('is_member'):
					non_member_count += 1
					non_member_data = frappe.db.sql("""select ifnull(sum(milkquantity),0) as qty ,
										ifnull(sum(amount),0) as amt 
								from 
									`tabFarmer Milk Collection Record`
								where docstatus = 1 and farmerid = '{0}' {1} 
					""".format(farmer,get_conditions(filters)),as_dict=1,debug=0)
					non_member_qty += flt(non_member_data[0].get('qty'))
					non_member_amt += flt(non_member_data[0].get('amt'))
			if farmer_id and farmer_id.get('is_member'):
				member_count += 1
				member_data = frappe.db.sql("""select ifnull(sum(milkquantity),0) as qty ,
										ifnull(sum(amount),0) as amt 
								from
									`tabFarmer Milk Collection Record`
								where docstatus = 1 and farmerid = '{0}' {1}
					""".format(farmer,get_conditions(filters)),as_dict=1,debug=0)
				member_qty += flt(member_data[0].get('qty'))
				member_amt += flt(member_data[0].get('amt'))

	 	if filters.get('from_report') == "Dairy Register 2":
		 	member_dict.update({
					"total_milk_qty":round(member_qty+non_member_qty,2),
					"total_milk_amt":round(member_amt+non_member_amt,2)
					})
		else:
			member_dict.update({"non_member_count":non_member_count,
					"member_count":member_count,
					"non_member_qty":round(non_member_qty,2),
					"member_qty":round(member_qty,2),
					"member_amt":round(member_amt,2),
					"non_member_amt":round(non_member_amt,2),
					"date":filters.get('date'),
					"shift":filters.get('shift'),
					"total_milk_qty":round(member_qty+non_member_qty,2),
					"total_milk_amt":round(member_amt+non_member_amt,2)
					}) 	

	return member_dict

def get_fmcr_list(filters):
	fmcr_data = frappe.db.sql("""select 
									date(collectiondate) as date,name,shift,farmerid
								from
									`tabFarmer Milk Collection Record`
								where
									docstatus = 1 {0}
								""".format(get_conditions(filters)),as_dict=True,debug=0)
	return fmcr_data

def get_conditions(filters):
	conditions = " and 1=1"
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")

	if frappe.session.user != 'Administrator':
		conditions += " and associated_vlcc = '{0}'".format(vlcc)
	if filters.get('start_date') and filters.get('end_date'):
		conditions += " and date(collectiondate) between '{0}' and '{1}' ".format(filters.get('start_date'),filters.get('end_date'))
	if filters.get('shift') == "Both":
		conditions += " and shift in ('MORNING','EVENING')"
	if filters.get('date'):
		conditions += " and date(collectiondate) = '{0}' ".format(filters.get('date'))
	return conditions

def get_local_sale_data(filters):
	vlcc_comp = frappe.db.get_value("User",frappe.session.user,"company")
	si_data = frappe.db.sql("""
							select 
								si.posting_date,
								si_item.qty,
								si_item.item_code,
								si.grand_total as amount,
								si.name,
								si.shift
							from 
								`tabSales Invoice` si,
								`tabSales Invoice Item` si_item
							where
								si.local_sale = 1 and
								si_item.item_code in ("COW Milk","BUFFALO Milk") and
								si.customer_or_farmer in ('Vlcc Local Customer','Vlcc Local Institution')
								and si_item.parent = si.name
								and si.docstatus = 1 and si.company = '{0}'
								{1}""".format(vlcc_comp,get_si_conditions(filters)),
								filters,debug=0,as_dict=1)
	return si_data

def get_si_conditions(filters):
	conditions = " and 1=1"
	if filters.get('start_date') and filters.get('end_date'):
		conditions += " and si.posting_date between '{0}' and '{1}' ".format(filters.get('start_date'),filters.get('end_date'))
	if filters.get('shift') == "Both":
		conditions += " and si.shift in ('MORNING','EVENING')"
	return conditions

def get_sample_sale_data(filters):
	stock_entry = frappe.db.sql("""
								select
									se.posting_date,
									se.shift,
									sed.qty,
									(sed.qty*sed.basic_rate) as amount
								from	
									`tabStock Entry` se,
									`tabStock Entry Detail` sed
								where
									sed.parent = se.name
									and se.is_reserved_farmer = 1
									and se.docstatus = 1
									and se.company = '{0}'
									and se.posting_date between '{1}' and '{2}'
									and se.shift in ('MORNING','EVENING') """.format(filters.get('vlcc'),filters.get('start_date'),filters.get('end_date')),as_dict=1,debug=0)
	return stock_entry