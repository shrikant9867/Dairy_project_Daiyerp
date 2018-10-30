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
		_("Farmer Id") + ":Link/Farmer:150",
		_("Famer Name") + ":Data:200",
		_("Sales Invoice") + ":Link/Sales Invoice:150",
		_("Date Of Advance Taken") + ":Date:170", 
		_("Item Details") + ":Link/Item:150",
		_("Advance Amount") + ":Float:150",
		_("Cleared Amount") + ":Float:150",
		_("Pending/Balance") + ":Float:150",
		_("Remarks") + ":Data:200"
	]

	return columns

def get_data(filters):
	data = frappe.db.sql("""select
									si.customer,
									si.farmer,
									si.name,
									si.posting_date,
									SUBSTRING_INDEX(GROUP_CONCAT(si_item.item_name), ' ', 2),
									si.grand_total,
									si.grand_total - si.outstanding_amount,
									si.outstanding_amount,
									"",
									si.local_sale_type
							from
								`tabSales Invoice` si,
								`tabSales Invoice Item` si_item
							where
								si.local_sale = 1
								and si.name = si_item.parent
								and si.local_sale_type = 'Feed And Fodder Advance'
								and si.customer_or_farmer = "Farmer"
								and si_item.item_code not in ('COW Milk','BUFFALO Milk')
								and si.docstatus = 1 and si.company = '{0}'
								{1} GROUP BY si.name """.format(filters.get('vlcc'),get_conditions(filters)),filters,as_list=1,debug=0)

	if len(data):
		advance_data = []
		for row in data:
			if row[9] == "Feed And Fodder Advance" and len(row[2].split('-')) > 2:
				advance_data = get_feed_advance(row[2])
				if advance_data:
					row[5] = advance_data[0]
					row[6] = advance_data[1]
					row[7] = advance_data[2]
	return data


def get_feed_advance(invoice):
	if invoice:
		advance_name = frappe.get_value("Farmer Advance",{"feed_and_fodder_si":invoice},"name")
		if advance_name:
			advance_doc = frappe.get_doc("Farmer Advance",advance_name)
			return [advance_doc.advance_amount,advance_doc.advance_amount-advance_doc.outstanding_amount,advance_doc.outstanding_amount]

def get_conditions(filters):
	conditions = " and 1=1"
	if filters.get('farmer') and filters.get('start_date') and filters.get('end_date'):	
		conditions += " and si.posting_date between %(start_date)s and %(end_date)s and si.farmer = %(farmer)s"
	elif filters.get('start_date') and filters.get('end_date'):
		conditions += " and si.posting_date between %(start_date)s and %(end_date)s"
	return conditions