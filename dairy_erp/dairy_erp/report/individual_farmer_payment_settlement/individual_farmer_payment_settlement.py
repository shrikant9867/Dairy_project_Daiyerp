# Copyright (c) 2018, Stellapps Technologies Private Ltd.
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import itertools as it

def execute(filters=None):
	columns = get_column()
	data = []
	data1=[]
	x=""

	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')
	number_farmer = frappe.db.sql("""  Select name,full_name from `tabFarmer` where vlcc_name = '{0}'""".format(vlcc))
	for i in number_farmer:
		farmer_id,farmer_name =i[0],i[1] 
		data.append(get_data(filters,farmer_id,farmer_name))

	for itm in data:
		for i in itm:
			if i != x:
				data1.append(i)
				x=i

	return columns,data1



def get_column(filters=None):
	columns = [
		("Farmer Name") + ":Data:100",
		("cycle") + ":Data:100",
		#("Date") + ":Date:150",
		("Total Payable")+":Data:200",
		("Total Receivable")+":Data:200",
		("Total Settlment Amt") + ":Data:200",
		("Actual Amt To be Settle") + ":Data:200",
	]
	return columns

def get_data(filters,farmer_id,farmer_name):
	vlcc = frappe.db.get_value("User",{"name":frappe.session.user},'company')
	if filters.cycle and not filters.farmer and not filters.full_name:
			data = frappe.db.sql(""" select g1.farmer,g1.cycle,
			(select sum(grand_total) from `tabPurchase Invoice` 
			where 
				supplier_type='Farmer' 
				and supplier='{0}' 
				and posting_date between 
					(select start_date from `tabFarmer Date Computation` where name='{1}') 
				and (select end_date from `tabFarmer Date Computation` where name='{1}')),
					(select 
					sum(grand_total) from `tabSales Invoice` where customer='{0}' 
				and posting_date between (select start_date from `tabFarmer Date Computation` 
					where name='{1}') 
						and (select end_date from `tabFarmer Date Computation` where name='{1}'))+
						(
							select sum(total_debit) 
							from `tabJournal Entry` 
								where 
							title='{0}' and cycle='{1}' and type in ('Farmer Advance','Farmer Loan')
						),
							(select sum(settled_amount*2 + set_amt_manual) from `tabFarmer Payment Log` where farmer='{0}' 
						and cycle='{1}')as actual_amt_settle,(( select sum(outstanding_amount) from `tabSales Invoice` 
							where customer='{0}' 
							and 
								posting_date between (select start_date from `tabFarmer Date Computation` where name='{1}') 
							and (select end_date from `tabFarmer Date Computation` where name='{1}') )+(select sum(outstanding_amount) from `tabPurchase Invoice` 
								where 
								supplier_type='Farmer' 
								and supplier='{0}' 
								and posting_date between (select start_date from `tabFarmer Date Computation` where name='{1}') 
								and (select end_date from `tabFarmer Date Computation` where name='{1}'))+(select sum(allocated_amount) from `tabPayment Entry Reference` where reference_name in (select sales_invoice from `tabFarmer Cycle` where parent in (select name from `tabFarmer Advance` where farmer_id='{2}' and farmer_name='{0}')) and reference_doctype='Journal Entry')) from `tabFarmer Payment Log` as g1 
									where g1.farmer='{0}' and g1.cycle='{1}' and 1=1 order by name desc limit 1"""
									.format(farmer_name,filters.cycle,farmer_id),debug=0,as_list=1)
	else:
		data = frappe.db.sql(""" select g1.farmer,g1.cycle,
			(select sum(grand_total) from `tabPurchase Invoice` 
			where 
				supplier_type='Farmer' 
				and supplier='{0}' 
				and posting_date between 
					(select start_date from `tabFarmer Date Computation` where name='{1}') 
				and (select end_date from `tabFarmer Date Computation` where name='{1}')),
					(select 
					sum(grand_total) from `tabSales Invoice` where customer='{0}' 
				and posting_date between (select start_date from `tabFarmer Date Computation` 
					where name='{1}') 
						and (select end_date from `tabFarmer Date Computation` where name='{1}'))+
						(
							select sum(total_debit) 
							from `tabJournal Entry` 
								where 
							title='{0}' and cycle='{1}' and type in ('Farmer Advance','Farmer Loan')
						),
							(select sum(settled_amount*2 + set_amt_manual) from `tabFarmer Payment Log` where farmer='{0}' 
						and cycle='{1}')as actual_amt_settle,(( select sum(outstanding_amount) from `tabSales Invoice` 
							where customer='{0}' 
							and 
								posting_date between (select start_date from `tabFarmer Date Computation` where name='{1}') 
							and (select end_date from `tabFarmer Date Computation` where name='{1}') )+(select sum(outstanding_amount) from `tabPurchase Invoice` 
								where 
								supplier_type='Farmer' 
								and supplier='{0}' 
								and posting_date between (select start_date from `tabFarmer Date Computation` where name='{1}') 
								and (select end_date from `tabFarmer Date Computation` where name='{1}'))+(select sum(allocated_amount) from `tabPayment Entry Reference` where reference_name in (select sales_invoice from `tabFarmer Cycle` where parent in (select name from `tabFarmer Advance` where farmer_id='{2}' and farmer_name='{0}')) and reference_doctype='Journal Entry')) from `tabFarmer Payment Log` as g1 
									where g1.farmer='{0}' and g1.cycle='{1}' and 1=1 order by name desc limit 1"""
									.format(filters.full_name,filters.cycle,filters.farmer),debug=0,as_list=1)



	
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





