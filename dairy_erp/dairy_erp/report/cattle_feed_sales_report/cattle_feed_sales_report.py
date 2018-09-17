# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import has_common

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns ,data 

def get_columns():

	columns = [
		_("Date") + ":Data:90", 
		_("Sales Invoice") + ":Link/Sales Invoice:150",
		_("Item Code") + ":Data:150",
		_("Quantity") + ":Float:150",
		_("Rate") + ":Currency:150",
		_("Total") + ":Currency:100",
		_("Remarks") + ":Data:200"
	]

	return columns

def get_data(filters):
	data = frappe.db.sql("""select
									DATE_FORMAT(si.posting_date, "%d-%m-%y"), 
									si.name,
									si_item.item_name,
									si_item.qty,
									si_item.rate,
									si_item.qty*si_item.rate 
							from
								`tabSales Invoice` si,
								`tabSales Invoice Item` si_item
							where
								si.local_sale = 1
								and si.name = si_item.parent
								and si.customer_or_farmer = "Farmer"
								and si_item.item_code not in ('COW Milk','BUFFALO Milk')
								and si.docstatus = 1 and si.company = '{0}'
								{1} order by si.posting_date """.format(filters.get('vlcc'),get_conditions(filters)),as_list=1,debug=0)
	if data:
		g_total = 0
		for row in data:
			g_total += row[5]
		data.append(["","","Grand Total","","",g_total,""])	
	return data

def get_conditions(filters):
	conditions = " and 1=1"
	if filters.get('farmer') and filters.get('start_date') and filters.get('end_date'):	
		conditions += " and si.posting_date between '{0}' and '{1}' and si.farmer = '{2}'".format(filters.get('start_date'),filters.get('end_date'),filters.get('farmer'))
	elif filters.get('start_date') and filters.get('end_date'):
		conditions += " and si.posting_date between '{0}' and '{1}' ".format(filters.get('start_date'),filters.get('end_date'))
	return conditions


