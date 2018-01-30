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
	supplier_args = {
		"party_type": "Supplier",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}

	filters["supplier"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")

	# Payable
	Payable = ReceivablePayableReport(filters).run(supplier_args)
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
	print "----------------",dictList1

	outstanding_amount = 0
	pay_data = Payable[1]
	for i in pay_data:
		outstanding_amount += i[7]



	customer_args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}

	filters["supplier"] = ""
	filters["customer"] = frappe.db.get_value("Farmer",filters.get("farmer"),"full_name")


	Receivable = ReceivablePayableReport(filters).run(customer_args)
	new_Receivable = []

	# Receivable
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

	Vlcc_data = frappe.db.sql("select vlcc_name from `tabFarmer`")


	outstanding_amount_receive = 0
	recv_data = Receivable[1]
	for i in recv_data:
		outstanding_amount_receive += i[10]

	# Report Data
	for p in dictList1:
		for r in dictList2:
			print "7777777777&&&&&&&&&&&&&&&&&&&&&",p[0],r[0]
			if(p[0] == r[0]):
				print "Payable - Receivable:",p[1]-r[1]
				pay_farmerid = frappe.db.get_values("Farmer", {"full_name":p[0]} ,"farmer_id")
				recv_farmerid = frappe.db.get_values("Farmer", {"full_name":r[0]} ,"farmer_id")
				data.append([pay_farmerid[0][0],p[0],p[1],r[1], p[1]-r[1]])
			else:
				if frappe.db.exists("Farmer",str(pay_farmer_id[0][0])) and (str(p[0]) or str(r[0]) == "") :
					data.append([pay_farmerid[0][0],p[0],p[1],r[1], p[1]-r[1]])
				if frappe.db.exists("Farmer",str(recv_farmer_id[0][0])) and (str(r[0]) or str(p[0]) == "") :
					data.append([recv_farmer_id[0][0],p[0],p[1],r[1], p[1]-r[1]])


	if customer_args.get("party_type") == "Customer":
		
		columns += [_("Farmer ID") + ":Link/Farmer"]
		columns += [_("Farmer")]

		columns.append({
		"label": "Net Payable to Farmer",
		"fieldtype": "Currency",
		"options": "currency",
		"width": 200
		})

		columns.append({
		"label": "Net Receivable to Farmer",
		"fieldtype": "Currency",
		"options": "currency",
		"width": 200
		})

		columns.append({
		"label": "Net Pay Off to Farmer",
		"fieldtype": "Currency",
		"options": "currency",
		"width": 200
		})
	return columns, data
