import frappe
from dairy_erp.dairy_erp.doctype.village_level_collection_centre.village_level_collection_centre import create_taxes_charges_template

def autoname(doc, method):
	if not doc.vlcc:
		doc.name = doc.title
	else:
		vlcc_abbr = frappe.db.get_value("Company", doc.vlcc, "abbr")
		doc.name = doc.title + " - " + vlcc_abbr

def auto_create_vlcc_tax(doc, method=None):
	temp_type = doc.doctype
	vlcc_list = frappe.get_all("Village Level Collection Centre")
	for vlcc in vlcc_list:
		if frappe.db.exists("Company", vlcc.get('name')):
			create_taxes_charges_template(temp_type, doc, vlcc.get('name'))

