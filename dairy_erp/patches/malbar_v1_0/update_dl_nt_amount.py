from __future__ import unicode_literals
import frappe

def execute():
	vmcr_list = frappe.get_all("Vlcc Milk Collection Record",filters={'docstatus': 1})
	for vmcr in vmcr_list:
		vmcr_doc = frappe.get_doc("Vlcc Milk Collection Record",vmcr.get('name'))
		print vmcr_doc.name,"\n\n"
		dl_nt = frappe.get_doc("Delivery Note",frappe.db.get_value("Delivery Note",{"vlcc_milk_collection_record":vmcr.get('name')},'name'))
		print dl_nt.name,"dl_note\n\n"