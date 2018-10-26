# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	user_email = frappe.get_doc("User",frappe.session.user).email
	societyid = frappe.db.get_value('Address',{'manager_email':user_email,'address_type':'Chilling Centre'},'centre_id')
	filters.update({
		'societyid':societyid
		})
	columns, data = get_columns(), get_data(filters)
	return columns ,data

def get_columns():

	columns = [
		_("Date") + ":Data:100",
		_("Shift") + ":Data:100",
		_("Route") + ":Data:100",
		_("CC") + ":Data:100",
		_("VLCC") + ":Data:100",
		_("TS") + ":Data:100",
		_("Qlty") + ":Data:100",
		_("Cans") + ":Data:100",
		_("Qty") + ":Data:100",
		_("Fat") + ":Data:100", 
		_("Snf") + ":Data:100",
		_("Rate") + ":Data:100",
		_("Value") + ":Data:100"
	]

	return columns

def get_data(filters=None):
	date_filters = " 1=1 "
	if filters.get("from_date"):
		date_filters += " and date(collectiondate) = '{0}'".format(filters.get('from_date'))
	if filters.get("shift"):
		date_filters += " and shift = '{0}'".format(filters.get('shift'))	
	if filters.get('societyid'):
		date_filters += " and societyid = '{0}'".format(filters.get("societyid"))
	vmcr_data = frappe.db.sql("""
							select
								DATE_FORMAT(date(collectiondate), "%d-%m-%Y"),
								CASE
								    WHEN shift = "MORNING" THEN "AM"
								    WHEN shift = "EVENING" THEN "PM"
								END,
								collectionroute,
								group_concat(long_format_farmer_id),
								group_concat(associated_vlcc),
								group_concat(fat+snf),
								group_concat(milkquality),
								group_concat(numberofcans),
								group_concat(milkquantity),
								group_concat(round(milkquantity*fat/1000,2)),
								group_concat(round(milkquantity*snf/1000,2)),
								group_concat(round((((milkquantity*(fat+snf)*289.3)/100)/milkquantity),2)),
								group_concat(round((milkquantity*(fat+snf)*289.3)/100,2))
							from
								`tabVlcc Milk Collection Record`
							where
							{0} and docstatus = 1
							group by collectionroute
							order by date(collectiontime),collectionroute """.format(date_filters),as_list=1,debug=0)

	for row in vmcr_data:
		for index,data in enumerate(row):	
			if index > 2:
				if index > 6:
					row_ = [float(val) for val in data.split(',')]
					row[index] = row_
					row[index].append(flt(sum(row_),2))
				if index == 4 or index == 3 or index == 6:
					if index == 3:
						row[index] = [str(val.split('_')[3]) for val in data.split(',')]
					else:
						row[index] = [str(val) for val in data.split(',')]
					row[index].append(" ")
				if index == 5:
					row[index] = [flt(val,2) for val in data.split(',')]
					row[index].append(" ")

	last_row = ["Grand Total",get_total_and_good_milk_qty(date_filters,"Accept"),get_total_and_good_milk_qty(date_filters,"Reject","CS"),get_total_and_good_milk_qty(date_filters,"Reject","CT"),get_total_and_good_milk_qty(date_filters,"Reject","SS")]
	vmcr_data.append(last_row)
	return vmcr_data


def get_total_and_good_milk_qty(filters,status=None,bad_milk_type=None):
	cond = " and 1=1 "
	if status and status == "Accept":
		cond += " and status = 'Accept' "
	if status and status == "Reject":
		if bad_milk_type and bad_milk_type == "CS":
			cond += " and status = 'Reject' and milkquality =  'CS' "
		if bad_milk_type and bad_milk_type == "CT":
			cond += " and status = 'Reject' and milkquality =  'CT' "
		if bad_milk_type and bad_milk_type == "SS":
			cond += " and status = 'Reject' and milkquality =  'SS' "
	qty = frappe.db.sql("""
		select 
				sum(milkquantity)
		from
				`tabVlcc Milk Collection Record`
		where
			{0} and docstatus = 1
			{1}
		""".format(filters,cond),as_list=1,debug=1)

	return qty