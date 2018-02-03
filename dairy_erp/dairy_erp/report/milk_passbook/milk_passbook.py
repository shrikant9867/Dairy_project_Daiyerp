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
	if filters.get('farmer_id') and filters.get('shift'):
		print "inside bot.....\n\n\n"
		conditions = "where farmerid = {0} and shift = '{1}'".format(filters.get('farmer_id'),filters.get('shift'))
	elif filters.get('farmer_id'):
		conditions = "where farmerid = {0}".format(filters.get('farmer_id'))
	elif filters.get('shift'):
		conditions = "where shift = '{0}'".format(filters.get('shift'))
	elif filters.get('from_date') and filters.get('to_date'):
		pass
		# from_date = frappe.utils.get_datetime().strftime("%Y-%m-%d")
		# conditions = "where collectiontime between %s and %s",(filters.get('from_date'),filters.get('to_date'))

	return conditions

def get_data(filters):

	if filters:
		data = frappe.db.sql("""select farmerid,farmer,collectiontime,shift,milktype,milkquantity,amount
						from `tabFarmer Milk Collection Record` {0}""".format(get_conditions(filters)),as_list=1)
	else:
		data = frappe.db.sql("""select farmerid,farmer,collectiontime,shift,milktype,milkquantity,amount
						from `tabFarmer Milk Collection Record`""",as_list=1)

	return data


