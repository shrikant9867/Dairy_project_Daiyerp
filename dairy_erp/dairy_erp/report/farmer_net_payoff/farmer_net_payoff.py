# # Copyright (c) 2013, indictrans technologies and contributors
# # For license information, please see license.txt

# from __future__ import unicode_literals
# import frappe

# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data


# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport
from frappe import _


def execute(filters=None):
	columns, data = [], []
	columns = get_column(filters)
	data = get_data(filters)
	return columns, data

def get_column(filters):
	columns =[ ("Farmer ID") + ":Link/Farmer:200",
				("Farmer") + ":Data:150",
				("Net Payable to Farmer") + ":Currency:150",
				("Net Receivable from Farmer") + ":Currency:150",
				("Net Pay Off to Farmer")+ ":Currency:150",
			]		
	return columns




	# if customer_args.get("party_type") == "Customer":
		
	# 	columns += [_("Farmer ID") + ":Link/Farmer"]
	# 	columns += [_("Farmer")]

	# 	columns.append({
	# 	"label": "Net Payable to Farmer",
	# 	"fieldtype": "Currency",
	# 	"options": "currency",
	# 	"width": 200
	# 	})

	# 	columns.append({
	# 	"label": "Net Receivable to Farmer",
	# 	"fieldtype": "Currency",
	# 	"options": "currency",
	# 	"width": 200
	# 	})

	# 	columns.append({
	# 	"label": "Net Pay Off to Farmer",
	# 	"fieldtype": "Currency",
	# 	"options": "currency",
	# 	"width": 200
	# 	})

def get_data(filters):
	print "\n \n \n \n ------------------------------------------------------------"
	print "filters",filters

	supplier_args = {
		"party_type": "Supplier",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}

	filters["supplier"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")

	customer_args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}

	filters["supplier"] = ""
	filters["customer"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")

	Payable = ReceivablePayableReport(filters).run(supplier_args)
	Receivable = ReceivablePayableReport(filters).run(customer_args)
	
	print "\n Payable",Payable

	sup_payable = []
	customer_recv = []
	sup_payable = get_payable_data(Payable)
	customer_recv = get_receivable_data(Receivable)
	sup_payable_list = []
	customer_recv_list = []
	return_list =[]
	data = []
	print "sup_payable",sup_payable
	print "customer_recv",customer_recv
	
	for ele in sup_payable:
		temp ={
			'name':ele[0],
			'amt':ele[1],
			'payable':ele[1]
		}
		sup_payable_list.append(temp)
	
	for ele in customer_recv:
		temp ={
			'name':ele[0],
			'amt':ele[1],
			"receivable":ele[1]
		}
		customer_recv_list.append(temp)
	return_list = customer_recv_list
	print "sup_payable",sup_payable_list
	print "customer_recv",customer_recv_list
	
	for ele in sup_payable_list:
		name = ele.get('name')
		amt =ele.get('amt')
		payable =ele.get('payable')
		for item in return_list:
			if item.get('name') == name:
				item['amt'] = amt - item['amt']
				item['payable'] =payable
	print "\nReturn List",return_list


	if return_list and sup_payable:
		for ele in return_list:
			farmer_fullname = ele.get('name')
			farmer_id = frappe.db.get_values("Farmer", {"full_name":farmer_fullname} ,"farmer_id",as_dict=1)
			Payable = receivable = 0
			Payable = ele.get('payable') if ele.get('payable') else 0
			receivable = ele.get('receivable') if ele.get('receivable') else 0
			net_pay_off = ele.get('amt')
			if not Payable:
				# receivable = -(receivable)
				net_pay_off = -(net_pay_off)

			temp =[farmer_id[0].get('farmer_id'),ele.get('name'),Payable,receivable,net_pay_off]
			data.append(temp)	
	else:
		# print "\n Data",data
		# if len(return_list)>1:
		# 	temp_list = return_list
		# 	for ele in temp_list:
		# 		farmer_fullname = ele.get('name')
		# 		farmer_id = frappe.db.get_values("Farmer", {"full_name":farmer_fullname} ,"farmer_id",as_dict=1)
		# 		Payable = receivable = 0
		# 		Payable = ele.get('payable') if ele.get('payable') else 0
		# 		receivable = ele.get('receivable') if ele.get('receivable') else 0
		# 		net_pay_off = ele.get('amt')
		# 		if not Payable:
		# 			# receivable = -(receivable)
		# 			net_pay_off = -(net_pay_off)

		# 		temp =[farmer_id[0].get('farmer_id'),ele.get('name'),Payable,receivable,net_pay_off]
		# 		data.append(temp)

		# 	print "\n Data",data
		if len(sup_payable_list)>1:
			temp_list = sup_payable_list
			for ele in temp_list:
				farmer_fullname = ele.get('name')
				farmer_id = frappe.db.get_values("Farmer", {"full_name":farmer_fullname} ,"farmer_id",as_dict=1)
				Payable = receivable = 0
				Payable = ele.get('payable') if ele.get('payable') else 0
				receivable = ele.get('receivable') if ele.get('receivable') else 0
				net_pay_off = ele.get('amt')
				if not Payable:
					# receivable = -(receivable)
					net_pay_off = -(net_pay_off)

				temp =[farmer_id[0].get('farmer_id'),ele.get('name'),Payable,receivable,net_pay_off]
				data.append(temp)

			print "\n Data",data
		else:
			print "\n Data",data
			data =[]
	return data

def get_payable_data(Payable):
	new_payable = []
	dict1 = {}
	temp1 = []
	dictList1 = []
	for i in Payable[1]:
		if i[1] not in dict1:
			dict1[i[1]] = i[7]
		else:
			dict1[i[1]] += i[7]
		new_payable.append([i[1],i[7]])

	for key, value in dict1.iteritems():
	    temp1 = [key,value]
	    dictList1.append(temp1)
	return dictList1

def get_receivable_data(Receivable):
	new_Receivable = []
	dict2 = {}
	temp2 = []
	dictList2 = []

	for i in Receivable[1]:
		if i[1] not in dict2:
			dict2[i[1]] = i[10]
		else:
			dict2[i[1]] += i[10]
		new_Receivable.append([i[1],i[10]])

	for key, value in dict2.iteritems():
	    temp2 = [key,value]
	    dictList2.append(temp2)
	return dictList2


@frappe.whitelist()
def get_user_company():
	user_name = frappe.session.user
	company_name= frappe.db.sql("""select company from `tabUser` where name ='{0}'""".format(str(frappe.session.user)),as_list=1)
	return company_name