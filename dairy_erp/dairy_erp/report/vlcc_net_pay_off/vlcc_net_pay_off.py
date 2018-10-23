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
		("Milk Incentives") + ":Currency:200",
		("Net Payable to Vlcc") + ":Currency:200",
		("Advance Emi") + ":Currency:200",
		("Loan Emi") + ":Currency:200",
		("Net Receivable from Vlcc") + ":Currency:200",
		("Net Pay Off to Vlcc")+ ":Currency:200"
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
	if party_type == "Supplier": outstd_idx, naming_field, voucher_type = 10, "supplier_name", "Purchase Invoice"
	else: outstd_idx, naming_field, voucher_type = 8, "customer_name", "Sales Invoice"
	for d in data:
		if d[2] == voucher_type:
			if not frappe.db.get_value(party_type, {naming_field: d[1]}, "farmer"):
				if d[1] not in filtered_data:
					filtered_data[d[1]] = d[outstd_idx]
				else:
					filtered_data[d[1]] += d[outstd_idx]
	return filtered_data

def merge_data(payable, receivable):
	# [ farmer_id, full_name, incentives, payable, advance, loan, receivable, payable-receivable ]
	data = []
	for f in get_vlccs():
		if payable.get(f) or receivable.get(f):
			pi_data = get_pi(f)
			si_data = get_si(f)
			pay = payable.get(f, 0)
			rec = receivable.get(f, 0)
			net = pay - rec
			data.append([f, pi_data.get('incentive'), pay, si_data.get('advance'), si_data.get('loan'), rec, net])
	return data		  


def get_vlccs():
	camp_office = frappe.db.get_value("User", frappe.session.user, "branch_office")
	return [ f.get('name')for f in frappe.get_all("Village Level Collection Centre", filters={"camp_office":camp_office} , fields=["name"]) ]

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

@frappe.whitelist()
def get_filtered_vlccs(doctype,text,searchfields,start,pagelen,filters):
	return frappe.db.sql("""select name,vlcc_type from 
		`tabVillage Level Collection Centre`""")

def get_pi(f):
	if len(f):
		print "###############",f
		incentive = frappe.db.sql("""
				select ifnull(sum(outstanding_amount),0) as total
			from 
				`tabPurchase Invoice`
			where 
				pi_type = 'Incentive' and supplier = '{0}' and docstatus = 1
			""".format(f),as_dict=1,debug=1)
		return {'incentive':incentive[0].get('total')}
	return {'incentive': 0}

def get_si(f):
	if len(f):
		# loan = frappe.db.sql("""
		# 			select ifnull(sum(outstanding_amount),0) as total
		# 		from 
		# 			`tabSales Invoice`
		# 		where 
		# 			type = 'Vlcc Loan' and customer = '{0}'  and docstatus =1
		# 		""".format(f),as_dict=1,debug=0)
		# advance = frappe.db.sql("""
		# 		select ifnull(sum(outstanding_amount),0) as total
		# 	from 
		# 		`tabSales Invoice`
		# 	where 
		# 		type = 'Vlcc Advance' and customer = '{0}'  and docstatus =1
		# 	""".format(f),as_dict=1,debug=0)
		# SG 11-10
		loan = frappe.db.sql("""
				select ifnull(sum(total_debit),0) as total
			from 
				`tabJournal Entry`
			where 
				type = 'Vlcc Loan' and reference_party = '{0}' and docstatus =1
			""".format(f),as_dict=1,debug=0)
		advance = frappe.db.sql("""
				select ifnull(sum(total_debit),0) as total
			from 
				`tabJournal Entry`
			where 
				type = 'Vlcc Advance' and reference_party = '{0}' and docstatus =1
			""".format(f),as_dict=1,debug=1)
		return {
				 	'loan': loan[0].get('total'),
				 	'advance': advance[0].get('total')
				}
	return {
			 	'loan': 0,
			 	'advance': 0
			 }
