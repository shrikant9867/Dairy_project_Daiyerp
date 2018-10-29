# critical patch for creating purchace invoices against created purchase receipts
from __future__ import unicode_literals
import frappe

def execute():
	company = frappe.db.get_value("Company",{'is_dairy':1},'name')
	if company:
		pr_list = frappe.get_all("Purchase Receipt",filters={'company': company, \
			'chilling_centre': "Pattambi-Chilling Centre",'milk_type':'G'},
			fields=['supplier','vlcc_milk_collection_record','posting_date','name'])
		for row in pr_list:
			if not frappe.db.get_value("Purchase Invoice Item",{'purchase_receipt': row.get('name')}):
				create_pi(company,row)

def create_pi(company,row):
	dairy_setting = frappe.get_doc("Dairy Setting")
	pr_child_item = frappe.get_all("Purchase Receipt Item",filters={'parent':row.get('name')}\
			, fields=['item_code','qty','rate', 'name', 'parent'])
	pi_obj = frappe.new_doc("Purchase Invoice")
	pi_obj.supplier =  row.get('supplier')
	pi_obj.vlcc_milk_collection_record = row.get('vlcc_milk_collection_record')
	pi_obj.pi_type = "VMCR"
	pi_obj.posting_date = row.get('posting_date')
	pi_obj.due_date = row.get('due_date')
	pi_obj.chilling_centre = "Pattambi-Chilling Centre"
	pi_obj.company = company
	pi_obj.append("items",
		{
			"item_code": pr_child_item[0].get('item_code') if len(pr_child_item) else 'COW Milk',
			"item_name": pr_child_item[0].get('item_code') if len(pr_child_item) else 'COW Milk',
			"description": pr_child_item[0].get('item_code') if len(pr_child_item) else 'COW Milk',
			"uom": "Litre",
			"qty": pr_child_item[0].get('qty') if len(pr_child_item) else 0,
			"rate": pr_child_item[0].get('rate') if len(pr_child_item) else 0,
			"warehouse": "Pattambi - MM", 
			"purchase_receipt": pr_child_item[0].get('parent') if len(pr_child_item) else 'COW Milk'
		}
	)

	account = "Pattambi Expense - MM"
	pi_obj.remarks = "[#"+account+"#]"
	pi_obj.flags.ignore_permissions = True
	pi_obj.submit()

