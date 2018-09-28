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
		_("Qlty") + ":Data:100",
		_("TS") + ":Data:100",
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
								group_concat(societyid),
								group_concat(associated_vlcc),
								group_concat("TS"),
								CASE
								    WHEN status = "Accept" THEN group_concat("G")
								    WHEN status = "Reject" THEN group_concat("CS")
								END,
								group_concat(numberofcans),
								group_concat(milkquantity),
								group_concat(fat),
								group_concat(snf),
								group_concat(rate),
								group_concat(round(rate*milkquantity,2))
							from
								`tabVlcc Milk Collection Record`
							where
							{0} and docstatus = 1
							group by collectionroute
							order by date(collectiontime)""".format(date_filters),as_list=1,debug=1)
	for row in vmcr_data:
		for index,data in enumerate(row):	
			if index > 2:
				if index > 6:
					row_ = [float(val) for val in data.split(',')]
					row[index] = row_
					row[index].append(sum(row_))
				else:
					row[index] = [str(val) for val in data.split(',')]
	print vmcr_data,"row\n\n\n\n"
	return vmcr_data