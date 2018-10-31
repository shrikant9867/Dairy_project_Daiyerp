# critical patch for creating purchace invoices against created purchase receipts
from __future__ import unicode_literals
import frappe

def execute():
	company = frappe.db.get_value("Company",{'is_dairy':1},'name')
	if company:
		for row in  frappe.db.get_all("Purchase Receipt",filters=[("vlcc_milk_collection_record", "in", \
			('VMCR- 1810-00791','VMCR- 1810-00605','VMCR- 1810-00606','VMCR- 1810-00607',\
			'VMCR- 1810-00607'))],fields=['name','supplier','company', 'vlcc_milk_collection_record']):
			create_pi_rejected(row, company)


def create_pi_rejected(row, company):
	vmcr_data = frappe.db.get_value("Vlcc Milk Collection Record", row.get('vlcc_milk_collection_record')\
		, ['milkquantity','rate'],as_dict=1)
	pi_obj = frappe.new_doc("Purchase Invoice")
	pi_obj.supplier =  row.get('supplier')
	pi_obj.vlcc_milk_collection_record = row.get('vlcc_milk_collection_record')
	pi_obj.pi_type = "VMCR"
	pi_obj.vlcc_milk_collection_record = row.get('vlcc_milk_collection_record')
	pi_obj.posting_date = row.get('posting_date')
	pi_obj.due_date = row.get('due_date')
	pi_obj.chilling_centre = "Pattambi-Chilling Centre"
	pi_obj.company = company
	pi_obj.append("items",
		{
			"item_code": 'COW Milk',
			"item_name": 'COW Milk',
			"description": 'COW Milk',
			"uom": "Litre",
			"qty": vmcr_data.get('milkquantity'),
			"rate": 0,
			"warehouse": "Pattambi - MM",
			"price_list_rate": 0,
			"purchase_receipt": row.get('name')
		}
	)

	account = "Pattambi Expense - MM"
	pi_obj.remarks = "[#"+account+"#]"
	pi_obj.flags.ignore_permissions = True
	pi_obj.submit()
	print "created -",pi_obj.name
	