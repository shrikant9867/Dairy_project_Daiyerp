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
		("Village Level Collection Centre") + ":Link/Village Level Collection Centre:200",
		("Net Payable to Camp Operator") + ":Currency:200",
		("Net Receivable from Vlcc") + ":Currency:200",
		("Net Pay Off to Vlcc")+ ":Currency:200",
	]
	return columns

def get_data(filters):
	if not filters.get('company'):
		filters['company'] = frappe.db.get_value("User", frappe.session.user, "company")
	receivable_data = get_receivable_data(filters)[1] if len(get_receivable_data(filters)) > 1 else []
	payable_data = get_payable_data(filters)[1] if len(get_payable_data(filters)) > 1 else []
	receivable, payable = filter_vlcc_data(receivable_data, "Customer"), filter_vlcc_data(payable_data, "Supplier") 
	data = merge_data(payable, receivable)
	return data

def get_receivable_data(filters):
	customer_args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}
	camp = frappe.db.get_value("Village Level Collection Centre",filters.get("vlcc"),"camp_office")
	if camp:
		camp_new = camp.split("-")[0]
	else:
		camp_new = ""
	filters["customer"] = filters.get('vlcc')
	filters.pop("supplier", None)
	return ReceivablePayableReport(filters).run(customer_args)

def get_payable_data(filters):
	supplier_args = {
		"party_type": "Supplier",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	camp = frappe.db.get_value("Village Level Collection Centre",filters.get("vlcc"),"camp_office")
	if camp:
		camp_new = camp.split("-")[0]
	else:
		camp_new = ""
	filters["supplier"] = filters.get('vlcc')
	filters.pop("customer", None)
	return ReceivablePayableReport(filters).run(supplier_args)

def filter_vlcc_data(data, party_type):
	#return only farmer's data
	filtered_data = {}
	if party_type == "Supplier": outstd_idx, naming_field = 10, "supplier_name"
	else: outstd_idx, naming_field = 8, "customer_name"
	for d in data:
		if not frappe.db.get_value(party_type, {naming_field: d[1]}, "farmer"):
			if d[1] not in filtered_data:
				filtered_data[d[1]] = d[outstd_idx]
			else:
				filtered_data[d[1]] += d[outstd_idx]
	return filtered_data

def merge_data(payable, receivable):
	# [ farmer_id, full_name, payable, receivable, payable-receivable ]
	data = []
	for f in get_vlccs():
		if payable.get(f) or receivable.get(f):
			pay = payable.get(f, 0)
			rec = receivable.get(f, 0)
			net = pay - rec
			data.append([f, pay, rec, net])
	return data		  

def get_vlccs():
	return [ f.get('name')for f in frappe.get_all("Village Level Collection Centre", fields=["name"]) ]

@frappe.whitelist()
def get_filtered_farmers(doctype,text,searchfields,start,pagelen,filters):
	user_name = frappe.session.user
	company_name= frappe.db.sql("""select company from `tabUser` where name ='{0}'""".format(str(frappe.session.user)),as_list=1)
	farmers = frappe.db.sql(""" select name,full_name from `tabFarmer` where vlcc_name ='{0}'""".format(company_name[0][0]),as_list=1)
	return farmers


@frappe.whitelist()
def get_filtered_company(doctype,text,searchfields,start,pagelen,filters):
	user_name = frappe.session.user
	company_name= frappe.db.sql("""select company from `tabUser` where name ='{0}'""".format(str(frappe.session.user)),as_list=1)
	return company_name