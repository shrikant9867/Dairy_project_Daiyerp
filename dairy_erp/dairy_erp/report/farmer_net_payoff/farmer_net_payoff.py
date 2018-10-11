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
		("Payable for Milk purchased from farmer") + ":Currency",
		("Incentive") + ":Currency",
		("Net Payable to Farmer") + ":Currency:200",
		("Local Purchase by Farmer") + ":Currency:200",
		("Any Vet Service Availed") + ":Currency:200",
		("Advance EMI") + ":Currency:200",
		("Feed & Fodder Advance EMI") + ":Currency:230",
		("Loan EMI") + ":Currency:200",
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
	if party_type == "Supplier": outstd_idx, voucher_type = 10, "Purchase Invoice"
	else: outstd_idx, voucher_type = 8, ["Sales Invoice","Journal Entry"]
	for d in data:
		if d[2] in voucher_type:
			if frappe.db.get_value(party_type, d[1], "farmer"):
				if d[1] not in filtered_data:
					filtered_data[d[1]] = d[outstd_idx]
				else:
					filtered_data[d[1]] += d[outstd_idx]
	return filtered_data

def merge_data(payable, receivable):
	# [ farmer_id, full_name, payable, receivable, payable-receivable ]
	#updated report section refer farmer advance and loan document 25 jun
	data = []
	for f in get_farmers():
		if payable.get(f[1]) or receivable.get(f[1]):
			pi_data = get_pi_data(f)
			si_data = get_si_data(f)
			pay = payable.get(f[1], 0)
			rec = receivable.get(f[1], 0)
			net = pay - rec
			data.append([f[0], f[1], pi_data.get('fmcr'), pi_data.get('incentive'), \
				pay, si_data.get('local_sale'), si_data.get('vet_service'), si_data.get('advance'), si_data.get('fnf_advance'), si_data.get('loan'), rec, pay-rec])
	return data		  

def get_farmers():
	return [ [f.get('name'), f.get('full_name')] for f in frappe.get_all("Farmer", fields=["name", "full_name"]) ]

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
def get_filtered_company_(doctype,text,searchfields,start,pagelen,filters):
	pass

def get_pi_data(f):
	if len(f):
		fmcr = frappe.db.sql("""
				select ifnull(sum(outstanding_amount),0) as total
			from 
				`tabPurchase Invoice`
			where 
				 supplier = '{0}' and docstatus = 1
			""".format(f[1]),as_dict=1,debug=0)
		incentive = frappe.db.sql("""
				select ifnull(sum(outstanding_amount),0) as total
			from 
				`tabPurchase Invoice`
			where 
				pi_type = 'Incentive' and supplier = '{0}' and docstatus = 1
			""".format(f[1]),as_dict=1,debug=0)
		return {'fmcr':fmcr[0].get('total') - incentive[0].get('total') , 'incentive':incentive[0].get('total')}
	return {'fmcr':0, 'incentive':0}

def get_si_data(f):
	if len(f):
		local_sale = frappe.db.sql("""
				select ifnull(sum(outstanding_amount),0) as total
			from 
				`tabSales Invoice`
			where 
				local_sale = 1 and local_sale_type !='Feed And Fodder Advance' and customer = '{0}' and docstatus =1
			""".format(f[1]),as_dict=1,debug=0)
		# local_sale_faf = frappe.db.sql("""
		# 		select ifnull(sum(outstanding_amount),0) as total
		# 	from 
		# 		`tabSales Invoice`
		# 	where 
		# 		local_sale = 1 and local_sale_type='Feed And Fodder Advance' and customer = '{0}' and docstatus =1
		# 	""".format(f[1]),as_dict=1,debug=0)
		vet_service = frappe.db.sql("""
				select ifnull(sum(outstanding_amount),0) as total
			from 
				`tabSales Invoice`
			where 
				service_note = 1 and customer = '{0}' and docstatus =1
			""".format(f[1]),as_dict=1,debug=0)
		loan = frappe.db.sql("""
				select ifnull(sum(total_debit),0) as total
			from 
				`tabJournal Entry`
			where 
				type = 'Farmer Loan' and reference_party = '{0}' and docstatus =1
			""".format(f[1]),as_dict=1,debug=0)
		advance = frappe.db.sql("""
				select ifnull(sum(total_debit),0) as total
			from 
				`tabJournal Entry`
			where 
				type = 'Farmer Advance' and reference_party = '{0}' and is_feed_and_fodder=0 and docstatus =1
			""".format(f[1]),as_dict=1,debug=0)
		fnf_advance = frappe.db.sql("""
				select ifnull(sum(total_debit),0) as total
			from 
				`tabJournal Entry`
			where 
				type = 'Farmer Advance' and reference_party = '{0}' and is_feed_and_fodder=1 and docstatus =1
			""".format(f[1]),as_dict=1,debug=0)
		return {
				'local_sale':local_sale[0].get('total'),
			 	'vet_service': vet_service[0].get('total'),
			 	'loan': loan[0].get('total'),
			 	'advance': advance[0].get('total'),
			 	'fnf_advance': fnf_advance[0].get('total')
			 	}
	return {
				'local_sale': 0 ,
			 	'vet_service': 0,
			 	'loan': 0,
			 	'advance': 0,
			 	'fnf_advance':0
			 	}

