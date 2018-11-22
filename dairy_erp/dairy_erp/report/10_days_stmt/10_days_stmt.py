# Copyright (c) 2018, Stellapps Technologies Private Ltd.
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
		_("Fat Per") + ":Data:100", 
		_("Snf Per") + ":Data:100",
		_("Fat Kg") + ":Data:100",
		_("Snf Kg") + ":Data:100",
		_("Tot Quantity") + ":Data:100",
		_("Quality Type") + ":Data:100"
	]

	return columns

def get_data(filters=None):
	date_filters = " 1=1 "
	if filters.get("from_date") and filters.get("to_date"):
		date_filters += " and date(collectiondate) between '{0}' and '{1}' ".format(filters.get('from_date'),filters.get('to_date'))
	if filters.get('societyid'):
		date_filters += " and societyid = '{0}'".format(filters.get("societyid"))
	vmcr_data = frappe.db.sql("""
							select
								DATE_FORMAT(date(collectiondate), "%d-%m-%Y"),
								CASE
								    WHEN shift = "MORNING" THEN "AM"
								    WHEN shift = "EVENING" THEN "PM"
								END,
								fat,
								snf,
								fat,
								snf,
								milkquantity,
								CASE
								    WHEN status = "Accept" THEN "G"
								    WHEN status = "Reject" THEN "CS"
								END
							from
								`tabVlcc Milk Collection Record`
							where
							{0} and docstatus = 1 order by date(collectiontime)""".format(date_filters),as_list=1,debug=0)
	if vmcr_data:
		g_fat_total = 0
		g_snf_total = 0
		g_qty_total = 0
		cs_fat_total = 0
		cs_snf_total = 0
		cs_qty_total = 0
		for row in vmcr_data:
			if row[7] == "G":
				g_fat_total += row[4]
				g_snf_total += row[5]
				g_qty_total += row[6]
			if row[7] == "CS":
				cs_fat_total += row[4]
				cs_snf_total += row[5]
				cs_qty_total += row[6]
		vmcr_data.append(["Total","","","",str(flt(g_fat_total,2)),str(flt(g_snf_total,2)),str(flt(g_qty_total,2)),"G"])
		vmcr_data.append(["Total","","","",str(flt(cs_fat_total,2)),str(flt(cs_snf_total,2)),str(flt(cs_qty_total,2)),"CS"])
	return vmcr_data