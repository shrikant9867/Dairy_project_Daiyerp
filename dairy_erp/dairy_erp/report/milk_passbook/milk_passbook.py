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
				("Quantity") + ":Int:150",
				("Amount") + ":Currency:150"			
			]
	return columns

def get_conditions(filters):

	conditions = ""
	if filters.get('farmer_id') and filters.get('shift') and filters.get('from_date') and filters.get('to_date'):
		conditions = "where farmerid = {0} and shift = '{1}' and collectiontime between '{2}%' and '{3}%'".format(filters.get('farmer_id'),filters.get('shift'),filters.get('from_date'),filters.get('to_date'))
	elif filters.get('farmer_id'):
		conditions = "where farmerid = {0}".format(filters.get('farmer_id'))
	elif filters.get('shift'):
		conditions = "where shift = '{0}'".format(filters.get('shift'))
	elif filters.get('from_date') and filters.get('to_date'):
		conditions = "where collectiontime between '{0}%' and '{1}%' ".format(filters.get('from_date'),filters.get('to_date'))

	return conditions

def get_data(filters):

	if filters:
		data = frappe.db.sql("""select farmerid,farmer,collectiontime,shift,milktype,milkquantity,amount
						from `tabFarmer Milk Collection Record` {0}""".format(get_conditions(filters)),as_list=True)
	else:
		data = frappe.db.sql("""select farmerid,farmer,collectiontime,shift,milktype,milkquantity,amount
						from `tabFarmer Milk Collection Record`""",as_list=True)

	return data


