# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import itertools

def execute(filters=None):
	columns = get_colums()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	fmcr_list = frappe.db.sql("""select
									' ',
									fmcr.collectiondate,
									fmcr.milkquantity,
									fmcr.milktype,
									fmcr.fat,
									fmcr.snf,
									fmcr.rate,
									fmcr.amount,
									fmcr.farmerid
						from
							`tabFarmer Milk Collection Record` fmcr
						where
							{0} and fmcr.shift in ("EVENING","MORNING")
							and fmcr.associated_vlcc = '{1}'
							order by fmcr.collectiondate
		""" .format(get_conditions(filters),filters.get('vlcc')),as_list=1,debug=1)
	
	print fmcr_list,"fmcr_list________________________________________________"
	return fmcr_list
	# fmcr_evening_list = []
	# fmcr_morning_list = []
	# for shift in ["EVENING","MORNING"]:
	# 	if shift == "MORNING":
	# 		fmcr_morning_list = get_fmcr_data(shift,filters)
	# 	if shift == "EVENING":
	# 		fmcr_evening_list = get_fmcr_data(shift,filters)

	# print len(fmcr_evening_list),"___________eve length"
	# print len(fmcr_morning_list),"_____________________morning lenght"		

	# final_fmcr_list = []
	# for m_fmcr in fmcr_morning_list:
	# 	for e_fmcr in fmcr_evening_list:
	# 		if m_fmcr[1] == e_fmcr[1]:
	# 			final_fmcr_list.append(m_fmcr+e_fmcr)

	# for fmcr in final_fmcr_list:
	# 	# print fmcr,"fmcr___________________"
	# 	# print fmcr[2],"________________qty 2  index"
	# 	# print fmcr[10],"________________qty 10 index"
	# 	fmcr.append(float(fmcr[2])+float(fmcr[10]))
	# 	fmcr.append(fmcr[7]+fmcr[15])		
	# return final_fmcr_list

# def get_fmcr_data(shift,filters):
# 	fmcr_list = frappe.db.sql("""select
# 									'{1}', 
# 									fmcr.collectiondate,
# 									fmcr.milkquantity,
# 									fmcr.milktype,
# 									fmcr.fat,
# 									fmcr.snf,
# 									fmcr.rate,
# 									fmcr.amount
# 						from 
# 							`tabFarmer Milk Collection Record` fmcr
# 						where	
# 							{0} and shift = '{1}'
# 							order by fmcr.collectiondate 
# 		""" .format(get_conditions(filters),shift),as_list=1,debug=1)
# 	return fmcr_list

def get_conditions(filters):
	conditions = " 1=1"
	if filters.get('cycle'):
		cyclewise_computation = frappe.db.get_values("Cyclewise Date Computation",{"name":filters.get('cycle')},["start_date","end_date"],as_dict=1)
		conditions += " and fmcr.collectiondate BETWEEN '{0}' AND '{1}'".format(cyclewise_computation[0]['start_date'],cyclewise_computation[0]['end_date'])
	if filters.get('farmer'):
		conditions += " and fmcr.farmerid = '{0}'".format(filters.get('farmer'))
	return conditions

def get_colums():
	columns = [("Morning") + ":Data:200",
				("Date") + ":Date:100",
				("Quantity") + ":Float:100",
				("Milk Type") + ":Data:200",
				("FAT") + ":Data:150",
				("SNF") + ":Data:100",
				("Rate") + ":Data:100",
				("Amount") + ":Float:100",
				("Evening") + ":Data:200",
				("Date") + ":Date:100",
				("Quantity") + ":Float:100",
				("Milk Type") + ":Data:200",
				("FAT") + ":Data:150",
				("SNF") + ":Data:100",
				("Rate") + ":Data:100",
				("Amount") + ":Float:100",
				("Total Quantity") + ":Float:100",
				("Total Amount") + ":Float:100",
				]	
	return columns