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
		_("Date") + ":Date:90", 
		_("Sales Invoice") + ":Link/Sales Invoice:150",
		_("Item Code") + ":Link/Item:150",
		_("Quantity") + ":Float:150",
		_("Rate") + ":Currency:150",
		_("Total") + ":Currency:100",
		_("Remarks") + ":Data:200"
	]

	return columns

def get_data(filters):
	data = frappe.db.sql("""select
									si.posting_date, 
									si.name,
									si_item.item_name,
									si_item.qty,
									si_item.rate,
									si.grand_total 
							from
								`tabSales Invoice` si,
								`tabSales Invoice Item` si_item
							where
								si.local_sale = 1
								and si.name = si_item.parent
								and si.customer_or_farmer = "Farmer"
								and si_item.item_code not in ('COW Milk','BUFFALO Milk')
								and si.docstatus = 1 and si.company = '{0}'
								{1}""".format(filters.get('vlcc'),get_conditions(filters)),filters,debug=1)
	return data

def get_conditions(filters):
	conditions = " and 1=1"
	if filters.get('farmer') and filters.get('start_date') and filters.get('end_date'):	
		conditions += " and si.posting_date between %(start_date)s and %(end_date)s and si.farmer = %(farmer)s"
	elif filters.get('start_date') and filters.get('end_date'):
		conditions += " and si.posting_date between %(start_date)s and %(end_date)s"
	return conditions