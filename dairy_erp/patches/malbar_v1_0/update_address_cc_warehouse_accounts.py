# critical patch for updating warehouse and accounts on address
from __future__ import unicode_literals
import frappe

def execute():
	# company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr'],as_dict=1)

	# if not frappe.db.exists("Warehouse","Pattambi - MM"):
	# 	print"\n Warehouse doesnot exists"
	# 	wr_hs_doc = frappe.new_doc("Warehouse")
	# 	wr_hs_doc.warehouse_name = "PattambiMM"
	# 	wr_hs_doc.company = company.get('name')
	# 	wr_hs_doc.flags.ignore_permissions = True
	# 	wr_hs_doc.save()
	# 	print"\n Warehouse Created>>>>>>>>",wr_hs_doc.name

	# if not frappe.db.exists("Warehouse","Pattambi-Rejected - MM"):
	# 	print"\n Rejected Warehouse doesnot exists"
	# 	wr_hs_doc = frappe.new_doc("Warehouse")
	# 	wr_hs_doc.warehouse_name = "Pattambi-Rejected"
	# 	wr_hs_doc.company = company.get('name')
	# 	wr_hs_doc.flags.ignore_permissions = True
	# 	wr_hs_doc.save()
	# 	print"\n Rejected Warehouse Created>>>>>>>>",wr_hs_doc.name

	# if not frappe.db.get_value("Account", {"company": company.get('name'),"account_name": "Pattambi Income"}, "name"):
	# 	print"\n Income Account Not present"
	# 	account = frappe.new_doc("Account")
	# 	account.update({
	# 		"company": company.get('name'),
	# 		"account_name": "Pattambi Income",
	# 		"parent_account": "Direct Income - "+company.get('abbr'),
	# 		"root_type": "Income",
	# 		"account_type": ""
	# 	})
	# 	account.flags.ignore_permissions = True
	# 	account.save()

	# if not frappe.db.get_value("Account", {"company": company.get('name'),"account_name": "Pattambi Expense"}, "name"):
	# 	print"\n Expence Account Not present"
	# 	account = frappe.new_doc("Account")
	# 	account.update({
	# 		"company": company.get('name'),
	# 		"account_name": "Pattambi Expense",
	# 		"parent_account": "Stock Expenses - "+company.get('abbr'),
	# 		"root_type": "Expenses",
	# 		"account_type": ""
	# 	})
	# 	account.flags.ignore_permissions = True
	# 	account.save()

	# if not frappe.db.get_value("Account", {"company": company.get('name'),"account_name": "Pattambi Stock"}, "name"):
	# 	print"\n Expence Account Not present"
	# 	account = frappe.new_doc("Account")
	# 	account.update({
	# 		"company": company.get('name'),
	# 		"account_name": "Pattambi Stock",
	# 		"parent_account": "Stock Assets  - "+company.get('abbr'),
	# 		"root_type": "Asset",
	# 		"account_type": ""
	# 	})
	# 	account.flags.ignore_permissions = True
	# 	account.save()

	frappe.db.sql("""
		update 
			`tabAddress` 
		set 
			warehouse = 'Pattambi - MM', rejected_warehouse = 'Pattambi-Rejected - MM', income_account = 'Pattambi Income - MM', expence_account = 'Pattambi Expense - MM', stock_account = 'Pattambi Stock - MM'
		where 
			name = 'Pattambi-Chilling Centre' """)
