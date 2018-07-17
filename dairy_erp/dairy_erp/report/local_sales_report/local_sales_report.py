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
		_("Date") + ":Date:90", _("Customer") + ":Link/Customer:150",
		 _("Sales Invoice") + ":Link/Sales Invoice:150",
		_("Amount") + ":Currency:100"
	]

	return columns

def get_data(filters):

	vlcc_comp = frappe.db.get_value("User",frappe.session.user,"company")

	data = frappe.db.sql("""select posting_date, customer, name,grand_total 
							from 
								`tabSales Invoice`
							where 
								local_sale = 1 and docstatus = 1 and company = '{0}'
								{1}""".format(vlcc_comp,get_conditions(filters)),
								filters)
	return data

def get_conditions(filters):
	conditions = " and 1=1"

	if filters.get('customer'):
		conditions += " and customer = %(customer)s"
	if filters.get('from_date') and filters.get('to_date'):
		conditions += " and posting_date between %(from_date)s and %(to_date)s"

	return conditions

def get_customer(doctype,text,searchfields,start,pagelen,filters):
	branch_office = frappe.db.get_value("User", frappe.session.user, ['branch_office','company'],as_dict=True)
	if has_common(frappe.get_roles(), ["Vlcc Manager", "Vlcc Operator"]) and frappe.session.user != 'Administrator':
		return frappe.db.sql("""select name, customer_group,company
							from
								`tabCustomer`
							where
								customer_group not in ('Dairy','Vlcc') and 
								name like '{text}' and company = '{comp}'""".
								format(text= "%%%s%%" % text,comp = branch_office.get('company')))
	elif frappe.session.user == 'Administrator':
		return frappe.db.sql("""select name, customer_group,company
							from
								`tabCustomer`
							where
								customer_group not in ('Dairy','Vlcc') and 
								name like '{text}' """.
								format(text= "%%%s%%" % text)) 

	