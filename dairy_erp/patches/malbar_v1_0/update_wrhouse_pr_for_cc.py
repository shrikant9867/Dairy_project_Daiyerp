# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
# Author khushal
# critical patch for Pr update warehouse and 
from __future__ import unicode_literals
import frappe

def execute():
	company = frappe.db.get_value("Company",{'is_dairy':1},'name')
	# insert_field_in_pr()
	if company:
		update_cc_on_pr()
		update_milktype_on_pr()
		pr_list = frappe.get_all("Purchase Receipt",filters={'company': company, \
				'chilling_centre': "Pattambi-Chilling Centre",'milk_type':'G'})
		for row in pr_list:
			child_pr_list = frappe.get_all("Purchase Receipt Item",filters={'parent':row.get('name')},fields=['name','parent'])
			update_child_warehouse(child_pr_list[0], company)
			update_gl_entry(child_pr_list[0])
			update_bin(child_pr_list[0])
	create_missing_pr()		

def update_child_warehouse(child_doc, company):
	if len(child_doc):
		frappe.db.sql("""
				update `tabPurchase Receipt Item` set warehouse = 'Pattambi - MM' 
			where 
				parent=%s and name=%s""",(child_doc.get('parent'),child_doc.get('name')),debug=0)
	
def update_milktype_on_pr():
	for row in frappe.get_all("Vlcc Milk Collection Record",fields=['milkquality','name']):
		purchase_rec = frappe.db.get_value("Purchase Receipt",{'vlcc_milk_collection_record':\
								row.get('name')},'name')
		frappe.db.sql("""
				update `tabPurchase Receipt` set milk_type =%s 
			where 
				name = %s""",(row.get('milkquality'),purchase_rec),debug=0)

def update_gl_entry(child_doc):
	frappe.db.sql("""
			update `tabStock Ledger Entry` set warehouse = 'Pattambi - MM'
			where voucher_no = %s
		""",(child_doc.get('parent')),debug=0)

def update_bin(child_doc):
	frappe.db.sql("""
		update `tabBin` set warehouse = 'Pattambi - MM' where warehouse = 'Stores - MM'
		 and item_code = 'COW Milk'""",debug=0)

def insert_field_in_pr():
	frappe.db.sql("""
		alter table `tabPurchase Receipt` add column milk_type varchar(140)
		""", debug=1)

def update_cc_on_pr():
	if frappe.db.exists("Address", "Milma Test-Chilling Centre"):
		frappe.db.sql("""
			update `tabPurchase Receipt` set chilling_centre = 'Milma Test-Chilling Centre'
			where name = 'PREC-1810-00009'
			""")

def create_missing_pr():
	vmcr_list = frappe.db.sql("""
		select 
				name,rate,milkquantity,milktype,amount,milkquality,associated_vlcc
		from
				`tabVlcc Milk Collection Record` 
		where 
				milkquality = 'G' and societyid = '3000' 
				and docstatus= 1 and name not in 
				(select vlcc_milk_collection_record from 
				`tabPurchase Receipt` where chilling_centre =  'Pattambi-Chilling Centre')""",as_dict=1)

	for vmcr in vmcr_list:
		make_pr(vmcr)

def make_pr(vmcr):
	purchase_rec = frappe.new_doc("Purchase Receipt")
	purchase_rec.supplier = vmcr.get('associated_vlcc')
	purchase_rec.vlcc_milk_collection_record = vmcr.get('name')
	purchase_rec.milk_type = vmcr.get('milkquality')
	purchase_rec.company = 'Milma Malabar'
	purchase_rec.chilling_centre = 'Pattambi-Chilling Centre'
	purchase_rec.milk_type = vmcr.get('milkquality')
	# purchase_rec.camp_office = co
	purchase_rec.append("items",
		{
			"item_code": vmcr.get('milktype')+ ' Milk',
			"item_name": vmcr.get('milktype')+ ' Milk',
			"description": vmcr.get('milktype')+ ' Milk',
			"uom": "Litre",
			"qty": vmcr.get('milkquantity'),
			"rate": vmcr.get('rate'),
			"price_list_rate": vmcr.get('rate'),
			"amount": vmcr.get('amount'),
			"warehouse": 'Pattambi - MM'
		}
	)
	purchase_rec.status = "Completed"
	purchase_rec.per_billed = 100
	purchase_rec.flags.ignore_permissions = True
	purchase_rec.submit()
	print "Purchase receipt Created-",purchase_rec.name
	make_pi(purchase_rec,vmcr)

def make_pi(pr,vmcr):
	if not frappe.db.exists("Purchase Invoice Item",{'purchase_receipt':pr.name}):
		pi_obj = frappe.new_doc("Purchase Invoice")
		pi_obj.supplier =  pr.get('supplier')
		pi_obj.vlcc_milk_collection_record = pr.get('vlcc_milk_collection_record')
		pi_obj.pi_type = "VMCR"
		pi_obj.posting_date = pr.get('posting_date')
		pi_obj.due_date = pr.get('due_date')
		pi_obj.chilling_centre = "Pattambi-Chilling Centre"
		pi_obj.company = pr.company
		pi_obj.append("items",
			{
				"item_code": vmcr.get('milktype')+ ' Milk',
				"item_name": vmcr.get('milktype')+ ' Milk',
				"description": vmcr.get('milktype')+ ' Milk',
				"uom": "Litre",
				"qty": vmcr.get('milkquantity'),
				"rate": vmcr.get('rate'),
				"warehouse": "Pattambi - MM",
				"purchase_receipt": pr.name
			}
		)

		account = "Pattambi Expense - MM"
		pi_obj.remarks = "[#"+account+"#]"
		pi_obj.flags.ignore_permissions = True
		pi_obj.submit()
		print "Purchase Invoice Created-",pi_obj.name