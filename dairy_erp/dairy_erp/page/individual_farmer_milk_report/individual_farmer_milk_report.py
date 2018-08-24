from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate,date_diff,add_days

@frappe.whitelist()
def get_fmcr_data(vlcc=None,cycle=None,farmer=None):
	cyclewise_computation = frappe.db.get_values("Cyclewise Date Computation",{"name":cycle},["start_date","end_date"],as_dict=1)
	start_date = cyclewise_computation[0]['start_date']
	end_date = cyclewise_computation[0]['end_date']	
	filters = {
				'start_date':start_date,
				'end_date':end_date,
				'vlcc':vlcc,
				'farmer':farmer
				}
	fmcr_list = get_fmcr(filters)
	previous_balance = get_pi_outstanding(filters)

	date_and_shift_wise_fmcr = {}
	for fmcr in fmcr_list:
		if date_and_shift_wise_fmcr and str(fmcr[0])+"#"+str(fmcr[7]) in date_and_shift_wise_fmcr:
			date_and_shift_wise_fmcr[str(fmcr[0])+"#"+str(fmcr[7])].append(fmcr)
		else:
			date_and_shift_wise_fmcr[str(fmcr[0])+"#"+str(fmcr[7])] = [fmcr]

	final_ = []
	for k,v in date_and_shift_wise_fmcr.items():
		if len(date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'MORNING', [])) and len(date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'EVENING', [])):
			final_.append(date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'MORNING').pop(0) + date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'EVENING').pop(0))
		
		elif len(date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'MORNING',[])):
			l = len(date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'MORNING',[]))
			for i in range(l):
				final_.append(date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'MORNING').pop(0) + ['-',0,'-','-','-','-',0,'-'])
			date_and_shift_wise_fmcr[k.split('#')[0]+'#'+'MORNING'] = []

		elif len(date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'EVENING', [])):
			l = len(date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'EVENING',[]))
			for i in range(l):
				date = date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'EVENING')[0][0]
				final_.append([date,0,'-','-','-','-',0,'-'] + date_and_shift_wise_fmcr.get(k.split('#')[0]+'#'+'EVENING').pop(0))
			date_and_shift_wise_fmcr[k.split('#')[0]+'#'+'EVENING'] = []

	final_.append(['',0,'','','','',0,0,'','','','',0,0,0])
	for i,row in enumerate(final_):
		if i < len(final_) - 1:
			row.insert(16,row[1] + row[9])
			row.insert(17,row[6] + row[14])
			final_[-1][1] += row[1]
			final_[-1][6] += row[6]
			final_[-1][7] += row[9]
			final_[-1][12] += row[14]
			final_[-1][13] += row[16]
			final_[-1][14] += row[17]
	return {
			"fmcr":final_,
			"previous_balance":get_pi_outstanding(filters),
			"total_milk_amount":get_fmcr_milk_data(filters),
			"payment":get_si_outstanding(filters),
			"cattle_feed":cattle_feed_amount(filters)
			}

def get_fmcr(filters):	
	fmcr_list = frappe.db.sql("""select
									date(fmcr.collectiondate),
									fmcr.milkquantity,
									fmcr.milktype,
									fmcr.fat,
									fmcr.snf,
									fmcr.rate,
									fmcr.amount,
									fmcr.shift
						from
							`tabFarmer Milk Collection Record` fmcr
						where
							{0}
							group by fmcr.collectiondate,fmcr.shift,fmcr.name
		""".format(get_conditions(filters)),as_list=1,debug=0)
	return fmcr_list

def get_conditions(filters):
	if filters:
		conditions = "fmcr.collectiondate between '{0}' and '{1}' \
					and fmcr.farmerid = '{2}'\
					and fmcr.associated_vlcc = '{3}'".format(filters.get('start_date'),filters.get('end_date'),filters.get('farmer'),filters.get('vlcc'))
		return conditions

def get_pi_outstanding(filters):
	pi_data = frappe.db.sql("""
								select
									sum(pi.outstanding_amount)
								from
									`tabPurchase Invoice` pi
								where
									pi.supplier_type = 'Farmer'
									and pi.docstatus = 1
									and pi.supplier = '{0}'
									and pi.posting_date < '{1}'
								""".format(filters.get('farmer'),filters.get('start_date')),as_list=1,debug=1)
	return pi_data[0][0]

def get_si_outstanding(filters):
	si_data = frappe.db.sql("""
								select
									sum(si.outstanding_amount)
								from
									`tabSales Invoice` si
								where
									si.customer_or_farmer = 'Farmer'
									and si.docstatus = 1
									and si.customer = '{0}'
									and si.posting_date < '{1}'
								""".format(filters.get('farmer'),filters.get('start_date')),as_list=1,debug=1)
	return si_data[0][0]

def get_fmcr_milk_data(filters):
	total_milk_amount = frappe.db.sql("""
										select
											sum(fmcr.milkquantity)
										from
											`tabFarmer Milk Collection Record` fmcr
										where
											fmcr.milktype in ('COW','BUFFALO') and
											fmcr.collectiondate between '{0}' and '{1}'
											and fmcr.farmerid = '{2}'
											and fmcr.associated_vlcc = '{3}'"""
											.format(filters.get('start_date'),
													filters.get('end_date'),
													filters.get('farmer'),
													filters.get('vlcc')),as_list=1,debug=1)
	return total_milk_amount[0][0]

def cattle_feed_amount(filters):
	cattle_feed_amount = frappe.db.sql("""
								select
									sum(si.outstanding_amount)
								from
									`tabSales Invoice` si
								where
									si.customer_or_farmer = 'Farmer'
									and si.docstatus = 1
									and si.customer = '{0}'
									and si.posting_date between '{1}' and '{2}'
								""".format(filters.get('farmer'),filters.get('start_date'),filters.get('end_date')),as_list=1,debug=1)
	return cattle_feed_amount[0][0]