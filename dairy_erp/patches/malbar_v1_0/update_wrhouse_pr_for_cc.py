# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
# Author khushal
# critical patch for Pr update warehouse and 
from __future__ import unicode_literals
import frappe

def execute():
	company = frappe.db.get_value("Company",{'is_dairy':1},'name')
	insert_field_in_pr()
	if company:
		update_milktype_on_pr()
		pr_list = frappe.get_all("Purchase Receipt",filters={'company': company, \
				'chilling_centre': "Pattambi-Chilling Centre",'milk_type':'Good'})
		for row in pr_list:
			child_pr_list = frappe.get_all("Purchase Receipt Item",filters={'parent':row.get('name')},fields=['name','parent'])
			update_child_warehouse(child_pr_list[0], company)
			update_gl_entry(child_pr_list[0])
			update_bin(child_pr_list[0])

def update_child_warehouse(child_doc, company):
	if len(child_doc):
		frappe.db.sql("""
				update `tabPurchase Receipt Item` set warehouse = 'Pattambi - MM' 
			where 
				parent=%s and name=%s""",(child_doc.get('parent'),child_doc.get('name')),debug=1)
	
def update_milktype_on_pr():
	for row in frappe.get_all("Vlcc Milk Collection Record",fields=['milk_quality_type','name']):
		purchase_rec = frappe.db.get_value("Purchase Receipt",{'vlcc_milk_collection_record':\
								row.get('name')},'name')
		frappe.db.sql("""
				update `tabPurchase Receipt` set milk_type =%s 
			where 
				name = %s""",(row.get('milk_quality_type'),purchase_rec),debug=0)

def update_gl_entry(child_doc):
	frappe.db.sql("""
			update `tabStock Ledger Entry` set warehouse = 'Pattambi - MM'
			where voucher_no = %s
		""",(child_doc.get('parent')),debug=0)

def update_bin(child_doc):
	frappe.db.sql("""
		update `tabBin` set warehouse = 'Pattambi - MM' where warehouse = 'Stores - MM'
		 and item_code = 'COW Milk'""")

def insert_field_in_pr():
	pass