# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):

	columns =[ ("Date") + ":Data:80",
				("Shift") + ":Data:50",
				("Milk Type") + ":Data:80",
				("Quantity") + ":Float:100",
				("FAT") + ":Float:100",
				("SNF") + ":Float:100",
				("Rate") + ":Float:100",
				("Total") + ":Currency:100"			
			]
	return columns

def get_conditions(filters):
	conditions = " and 1=1"
	if filters.get('farmer_id'):
		conditions += " and farmerid = '{0}'".format(filters.get('farmer_id'))
	if filters.get('shift'):
		conditions += " and shift = '{0}'".format(filters.get('shift'))
	if filters.get('from_date') and filters.get('to_date'):
		conditions += " and date(collectiontime) between '{0}' and '{1}' ".format(filters.get('from_date'),filters.get('to_date'))
	return conditions

def get_data(filters):
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	data = frappe.db.sql("""select 
									DATE_FORMAT(collectiontime, "%d-%m-%y"),
									LEFT(shift,1),
									milktype,
									round(milkquantity,2),
									round(fat,2),
									round(snf,2),
									round(rate,2),
									amount
							from 
								`tabFarmer Milk Collection Record` 
							where 
								docstatus = 1 and
								associated_vlcc = '{0}' {1}""".format(
					user_doc.get('company'),
					get_conditions(filters)),as_list=True)
	if data:
		g_total = 0
		qty_total = 0
		for row in data:
			qty_total += row[3]
			g_total += row[7]
		data.append(["","","Grand Total",qty_total,"","","",g_total])
	return data

@frappe.whitelist()
def trim_farmer_id_and_name(doctype,txt,searchfields,start,pagelen,filters):
	user = frappe.get_doc("User",frappe.session.user)
	farmer_list = frappe.db.sql("""
				select
						RIGHT(full_name,4),
						TRIM(RIGHT(full_name,9) FROM full_name),
						contact_number
				from
						`tabFarmer`
				where
						vlcc_name = '{user}'
				and
						name like '{txt}' """.format(user=user.company,txt= "%%%s%%" % txt),as_list=1,debug=1)
	return farmer_list