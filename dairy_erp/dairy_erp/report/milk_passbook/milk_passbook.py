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

	columns =[ ("Farmer ID") + ":Link/Farmer:200",
				("Farmer") + ":Data:200",
				("Date") + ":Datetime:150",
				("Shift") + ":Data:150",
				("Milk Type") + ":Data:150",
				("Quantity") + ":Float:150",
				("Amount") + ":Currency:150"			
			]
	return columns

def get_conditions(filters):
	conditions = " and 1=1"
	if filters.get('farmer_id'):
		conditions += " and farmerid = '{0}'".format(filters.get('farmer_id'))
	if filters.get('shift'):
		conditions += " and shift = '{0}'".format(filters.get('shift'))
	if filters.get('from_date') and filters.get('to_date'):
		conditions += " and date(rcvdtime) between '{0}' and '{1}' ".format(filters.get('from_date'),filters.get('to_date'))
	return conditions

def get_data(filters):
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	data = frappe.db.sql("""select farmerid,farmer,rcvdtime,shift,milktype,round(milkquantity,2),amount
				from `tabFarmer Milk Collection Record` where docstatus = 1 and
				associated_vlcc = '{0}' {1}""".format(
					user_doc.get('company'),
					get_conditions(filters)),as_list=True)

	return data

@frappe.whitelist()
def get_farmer(doctype,txt,searchfields,start,pagelen,filters):
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
						name like '{txt}' """.format(user=user.username,txt= "%%%s%%" % txt),as_list=1)
	return farmer_list