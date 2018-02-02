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
	receivable_data = get_receivable_data(filters)[1] if len(get_receivable_data(filters)) > 1 else []
	payable_data = get_payable_data(filters)[1] if len(get_payable_data(filters)) > 1 else []
	filter_farmer_data(receivable_data, "Customer")
	# print "_________________Receivable_____________________\n\n", receivable_data, "\n\n"
	# print "_________________Payable_____________________\n\n", payable_data, "\n\n"
	return []

def get_receivable_data(filters):
	customer_args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}
	filters["customer"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")
	return ReceivablePayableReport(filters).run(customer_args)

def get_payable_data(filters):
	supplier_args = {
		"party_type": "Supplier",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	filters["supplier"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")
	return ReceivablePayableReport(filters).run(supplier_args)

def filter_farmer_data(data, party_type):
	for d in data:
		print "\n\ndd",d	,"\n\n"
# def get_data_old(filters):
# 	supplier_args = {
# 		"party_type": "Supplier",
# 		"naming_by": ["Buying Settings", "supp_master_name"],
# 	}

# 	filters["supplier"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")

# 	customer_args = {
# 		"party_type": "Customer",
# 		"naming_by": ["Selling Settings", "cust_master_name"],
# 	}

# 	filters["customer"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")

# 	Payable = ReceivablePayableReport(filters).run(supplier_args)
# 	Receivable = ReceivablePayableReport(filters).run(customer_args)

# 	sup_payable = []
# 	customer_recv = []
# 	sup_payable = get_payable_data(Payable)
# 	customer_recv = get_receivable_data(Receivable)
# 	sup_payable_list = []
# 	customer_recv_list = []
# 	return_list =[]
# 	data = []
	
# 	for ele in sup_payable:
# 		temp ={
# 			'name':ele[0],
# 			'amt':ele[1],
# 			'payable':ele[1]
# 		}
# 		sup_payable_list.append(temp)
	
# 	for ele in customer_recv:
# 		temp ={
# 			'name':ele[0],
# 			'amt':ele[1],
# 			"receivable":ele[1]
# 		}
# 		customer_recv_list.append(temp)
# 	return_list = customer_recv_list
	
# 	for ele in sup_payable_list:
# 		name = ele.get('name')
# 		amt =ele.get('amt')
# 		payable =ele.get('payable')
# 		for item in return_list:
# 			if item.get('name') == name:
# 				item['amt'] = amt - item['amt']
# 				item['payable'] =payable


# 	if return_list and sup_payable_list:
# 		for ele in return_list:
# 			farmer_fullname = ele.get('name')
# 			farmer_id = frappe.db.get_values("Farmer", {"full_name":farmer_fullname} ,"farmer_id",as_dict=1)
# 			payable = receivable = 0
# 			payable = ele.get('payable') if ele.get('payable') else 0
# 			receivable = ele.get('receivable') if ele.get('receivable') else 0
# 			net_pay_off = ele.get('amt')
# 			if not payable:
# 				# receivable = -(receivable)
# 				net_pay_off = -(net_pay_off)

# 			temp =[farmer_id[0].get('farmer_id'),ele.get('name'),payable,receivable,net_pay_off]
# 			data.append(temp)	
# 	else:
# 		if len(sup_payable_list)>1 and len(return_list)==0:
# 			temp_list = sup_payable_list
# 			for ele in temp_list:
# 				farmer_fullname = ele.get('name')
# 				farmer_id = frappe.db.get_values("Farmer", {"full_name":farmer_fullname} ,"farmer_id",as_dict=1)
# 				payable = receivable = 0
# 				payable = ele.get('payable') if ele.get('payable') else 0
# 				net_pay_off = ele.get('amt')

# 				temp =[farmer_id[0].get('farmer_id'),ele.get('name'),payable,0,net_pay_off]
# 				data.append(temp)
# 		if len(sup_payable_list)==1 and len(return_list)==1:
# 			data =[]

# 		else:
# 			data =[]
# 	return data

# def get_payable_data(Payable):
# 	new_payable = []
# 	dict1 = {}
# 	temp1 = []
# 	dictList1 = []
# 	for i in Payable[1]:
# 		if i[1] not in dict1:
# 			dict1[i[1]] = i[7]
# 		else:
# 			dict1[i[1]] += i[7]
# 		new_payable.append([i[1],i[7]])

# 	for key, value in dict1.iteritems():
# 	    temp1 = [key,value]
# 	    dictList1.append(temp1)
# 	return dictList1

# def get_receivable_data(Receivable):
# 	new_Receivable = []
# 	dict2 = {}
# 	temp2 = []
# 	dictList2 = []

# 	for i in Receivable[1]:
# 		if i[1] not in dict2:
# 			dict2[i[1]] = i[10]
# 		else:
# 			dict2[i[1]] += i[10]
# 		new_Receivable.append([i[1],i[10]])

# 	for key, value in dict2.iteritems():
# 	    temp2 = [key,value]
# 	    dictList2.append(temp2)
# 	return dictList2


# @frappe.whitelist()
# def get_user_company():
# 	user_name = frappe.session.user
# 	company_name= frappe.db.sql("""select company from `tabUser` where name ='{0}'""".format(str(frappe.session.user)),as_list=1)
# 	return company_name

# @frappe.whitelist()
# def get_farmers(doctype,text,searchfields,start,pagelen,filters):
# 	user_name = frappe.session.user
# 	company_name= frappe.db.sql("""select company from `tabUser` where name ='{0}'""".format(str(frappe.session.user)),as_list=1)
# 	farmers = frappe.db.sql(""" select name,full_name from `tabFarmer` where vlcc_name ='{0}'""".format(company_name[0][0]),as_list=1)
# 	return farmers