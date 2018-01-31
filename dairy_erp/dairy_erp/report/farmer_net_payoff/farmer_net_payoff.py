# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport
from frappe import _


def execute(filters=None):
	columns, data = get_column(), get_data(filters)
	return columns, data

def get_column():
	columns =[ 	
		("Farmer ID") + ":Link/Farmer:200",
		("Farmer") + ":Data:200",
		("Net Payable to Farmer") + ":Currency:200",
		("Net Receivable from Farmer") + ":Currency:200",
		("Net Pay Off to Farmer")+ ":Currency:200",
	]
	return columns

def get_data(filters):
	if not filters.get('company'):
		filters['company'] = frappe.db.get_value("User", frappe.session.user, "company")
	receivable_data = get_receivable_data(filters)[1] if len(get_receivable_data(filters)) > 1 else []
	payable_data = get_payable_data(filters)[1] if len(get_payable_data(filters)) > 1 else []
	receivable, payable = filter_farmer_data(receivable_data, "Customer"), filter_farmer_data(payable_data, "Supplier") 
	data = merge_data(payable, receivable)
	return data

def get_receivable_data(filters):
	customer_args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}
	filters["customer"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")
	filters.pop("supplier", None)
	return ReceivablePayableReport(filters).run(customer_args)

def get_payable_data(filters):
	supplier_args = {
		"party_type": "Supplier",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	filters["supplier"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")
	filters.pop("customer", None)
	return ReceivablePayableReport(filters).run(supplier_args)

def filter_farmer_data(data, party_type):
	#return only farmer's data
	filtered_data = {}
	outstd_idx = 10 if party_type == "Supplier" else 8
	for d in data:
		if frappe.db.get_value(party_type, d[1], "farmer"):
			if d[1] not in filtered_data:
				filtered_data[d[1]] = d[outstd_idx]
			else:
				filtered_data[d[1]] += d[outstd_idx]
	return filtered_data

def merge_data(payable, receivable):
	# [ farmer_id, full_name, payable, receivable, payable-receivable ]
	data = []
	for f in get_farmers():
		if payable.get(f[1]) or receivable.get(f[1]):
			pay = payable.get(f[1], 0)
			rec = receivable.get(f[1], 0)
			net = pay - rec
			data.append([f[0], f[1], pay, rec, pay-rec])
	return data		  

def get_farmers():
	return [ [f.get('name'), f.get('full_name')] for f in frappe.get_all("Farmer", fields=["name", "full_name"]) ]

@frappe.whitelist()
def get_filtered_farmers(doctype,text,searchfields,start,pagelen,filters):
	user_name = frappe.session.user
	company_name= frappe.db.sql("""select company from `tabUser` where name ='{0}'""".format(str(frappe.session.user)),as_list=1)
	farmers = frappe.db.sql(""" select name,full_name from `tabFarmer` where vlcc_name ='{0}'""".format(company_name[0][0]),as_list=1)
	return farmers
