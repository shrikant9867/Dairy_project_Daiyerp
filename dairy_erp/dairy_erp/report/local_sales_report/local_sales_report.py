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
		_("Customer") + ":Link/Customer:150",
		_("Shift") + ":Data:90",
		_("Sales Invoice") + ":Link/Sales Invoice:150",
		_("Item Code") + ":Link/Item:150",
		_("Quantity") + ":Float:150",
		_("Rate") + ":Float:150",
		_("Amount") + ":Currency:100"
	]

	return columns

def get_data(filters):

	vlcc_comp = frappe.db.get_value("User",frappe.session.user,"company")

	data = frappe.db.sql("""select DATE_FORMAT(si.posting_date, "%d-%m-%y"),
								   si.customer,
								   LEFT(si.shift,1),
								   si.name,
								   si_item.item_name,
								   si_item.qty,
								   si_item.rate,
								   si.grand_total
							from 
								`tabSales Invoice` si,
								`tabSales Invoice Item` si_item,
								`tabCustomer` cus
							where 
								si.local_sale = 1 and
								si.customer = cus.name
								and si.name = si_item.parent
								and si.docstatus = 1 and si.company = '{0}'
								{1}""".format(vlcc_comp,get_conditions(filters)),as_list=1,debug=1)
	
	if data:
		if filters.get('customer_type') == "Farmer":
			g_total = 0
			qty_total = 0
			for row in data:
				qty_total += row[5]
				g_total += row[7]
			data.append(["","","Grand Total","","",qty_total,"",g_total])		
		else:
			g_total = 0
			for row in data:
				g_total += row[7]
			data.append(["","","Grand Total","","","","",g_total])
	return data

def get_conditions(filters):
	conditions = " and 1=1"
	if filters.get('customer_type'):
		conditions += " and cus.customer_group = '{0}'".format(filters.get('customer_type'))
	if filters.get('customer'):
		conditions += " and si.customer = '{0}'".format(filters.get('customer'))
	if filters.get('from_date') and filters.get('to_date'):
		conditions += " and si.posting_date between '{0}' and '{1}' ".format(filters.get('from_date'),filters.get('to_date'))

	return conditions

def get_customer(doctype,text,searchfields,start,pagelen,filters):
	branch_office = frappe.db.get_value("User", frappe.session.user, ['branch_office','company'],as_dict=True)
	if filters.get('customer_type'):
		if has_common(frappe.get_roles(), ["Vlcc Manager", "Vlcc Operator"]) and frappe.session.user != 'Administrator':
			# return frappe.db.sql("""select name, customer_group,company
			# 					from
			# 						`tabCustomer`
			# 					where
			# 						customer_group not in ('Dairy','Vlcc') and 
			# 						name like '{text}' and company = '{comp}'""".
			# 						format(text= "%%%s%%" % text,comp = branch_office.get('company')))
			return frappe.db.sql("""select name, customer_group,company
								from
									`tabCustomer`
								where
									customer_group = '{customer_group}' and 
									name like '{text}' and company = '{comp}'""".
									format(text= "%%%s%%" % text,comp = branch_office.get('company'),customer_group = filters.get('customer_type')))
		elif frappe.session.user == 'Administrator':
			return frappe.db.sql("""select name, customer_group,company
								from
									`tabCustomer`
								where
									customer_group not in ('Dairy','Vlcc') and 
									name like '{text}' """.
									format(text= "%%%s%%" % text))
	