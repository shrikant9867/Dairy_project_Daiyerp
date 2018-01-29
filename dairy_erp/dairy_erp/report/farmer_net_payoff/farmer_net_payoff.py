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
	Payable = ReceivablePayableReport(filters).run(supplier_args)
	new_payable = []
	for i in Payable[1]:
		new_payable.append([i[1],i[7]])
	outstanding_amount = 0
	pay_data = Payable[1]
	for i in pay_data:
		outstanding_amount += i[7]



	customer_args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}

	Receivable = ReceivablePayableReport(filters).run(customer_args)
	new_Receivable = []

	# testing
	l1 = [['Jayvant',10,'Purchase Invoice'],['Jayvant',20,'Sales Invoice'],['Shraddha',30,'Purchase Invoice'],['Jayvant',40,'Sales Invoice'],['Shraddha',50,'Sales Invoice']]
	dict1 = {}
	# for l in l1:
	# 	print "++++++++++++",l[0]
	# 	if l[0] not in dict1:
	# 		dict1[l[0]] = l[1]
	# 	else:
	# 		dict1[l[0]] += l[1]
	# print dict1

	for i in Receivable[1]:
		# print "++++++++++++",i[1]
		if i[1] not in dict1:
			dict1[i[1]] = i[10]
		else:
			dict1[i[1]] += i[10]
		
		new_Receivable.append([i[1],i[10]])

	for key, value in dict.iteritems():
	    temp = [key,value]
	    dictlist.append(temp)
	print "++++++++++++",dict1

	Vlcc_data = frappe.db.sql("select vlcc_name from `tabFarmer`")


	outstanding_amount_receive = 0
	recv_data = Receivable[1]
	for i in recv_data:
		outstanding_amount_receive += i[10]

	for p in new_payable:
		for r in new_Receivable:
				if(p[0] == r[0]):
					farmer_vlcc = frappe.db.get_values("Farmer", {"full_name":p[0]} ,"vlcc_name")
					b = [list(x) for x in farmer_vlcc]
					c = [j for i in farmer_vlcc for j in i]
					data.append([p[0], p[1]-r[1], c[0]])

	if customer_args.get("party_type") == "Customer":
		
		columns += [_("Farmer") + ":Link/Farmer"]
	
		columns.append({
		"label": "Outstanding",
		"fieldtype": "Currency",
		"options": "currency",
		"width": 120
	})
		columns += [_("Vlcc") + ":Link/Village Level Collection Centre"]
	return columns, data
