# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_column(), get_data(filters)
	return columns, data

def get_column(filters=None):
	columns = [
		("Farmer Name") + ":Data:100",
		("cycle") + ":Data:100",
		#("Date") + ":Date:150",
		("Total Payable\n(Grand Total of PI)")+":Data:200",
		("Total Receivable\n(Grand Total of SI)")+":Data:200",
		("Total Settlment Amt") + ":Data:200",
		("Actual Amt To be Settle") + ":Data:200",
	]
	return columns

def get_data(filters):
	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')
	data = frappe.db.sql(""" select g1.farmer,g1.cycle,(select sum(grand_total) from `tabPurchase Invoice` where supplier_type='Farmer' and supplier='{0}' and posting_date between (select start_date from `tabFarmer Date Computation` where name='{1}') and (select end_date from `tabFarmer Date Computation` where name='{1}')),(select sum(grand_total) from `tabSales Invoice` where customer_or_farmer='Farmer' and customer='{0}' and posting_date between (select start_date from `tabFarmer Date Computation` where name='{1}') and (select end_date from `tabFarmer Date Computation` where name='{1}')),(select sum(settled_amount*2 + set_amt_manual) from `tabFarmer Payment Log` where farmer='{0}' and cycle='{1}')as actual_amt_settle,(( select sum(outstanding_amount) from `tabSales Invoice` where customer_or_farmer='Farmer' and customer='{0}' and posting_date between (select start_date from `tabFarmer Date Computation` where name='{1}') and (select end_date from `tabFarmer Date Computation` where name='{1}') )+(select sum(outstanding_amount) from `tabPurchase Invoice` where supplier_type='Farmer' and supplier='{0}' and posting_date between (select start_date from `tabFarmer Date Computation` where name='{1}') and (select end_date from `tabFarmer Date Computation` where name='{1}'))) from `tabFarmer Payment Log` as g1 where g1.farmer='{0}' and g1.cycle='{1}' order by name desc limit 1;""".format(filters.full_name,filters.cycle),debug=1)
	return data





def get_conditions(filters):
	conditions = ''
	# if filters.farmer:
	# 	conditions += "fpl.farmer='{0}'".format(filters.full_name)
	# 	print "\n\n conditions ====",conditions
	# if filters.vlcc:
	#  	conditions += " and fpl.vlcc='{0}'".format(filters.vlcc)
	#  	print "\n\n conditions ====",conditions	
	# if filters.cycle:
	#  	conditions += "and fpl.cycle='{0}'".format(filters.cycle)
	#  	print "\n\n conditions ====",conditions
	
	return conditions





