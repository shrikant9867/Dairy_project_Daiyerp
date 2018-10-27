# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
# Author khushal
# critical patch for Pr update warehouse and 
from __future__ import unicode_literals
import frappe

def execute():
	company = frappe.db.get_value("Company",{'is_dairy':1},'name')
	if company:
		pr_list = frappe.get_all("Purchase Receipt",filters={'company': company, \
							'chilling_centre': "Pattambi-Chilling Centre"})
		for row in pr_list:
			child_pr_list = frappe.get_all("Purchase Receipt Item",filters={'parent':row.get('name')})
			update_child_warehouse(child_pr_list, company)

def update_child_warehouse(child_doc, company):
	# frappe.db.sql("""update `tabPurchase Receipt Item` set warehouse = 'Pattambi - MM' """)
	pass