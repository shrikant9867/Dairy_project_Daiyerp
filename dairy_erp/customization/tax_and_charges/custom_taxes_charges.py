import frappe
from dairy_erp.dairy_erp.doctype.village_level_collection_centre.village_level_collection_centre import create_taxes_charges_template

def autoname(doc, method):
	if not doc.vlcc:
		doc.name = doc.title
	else:
		vlcc_abbr = frappe.db.get_value("Company", doc.vlcc, "abbr")
		doc.name = doc.title + " - " + vlcc_abbr

def auto_create_vlcc_tax(doc, method=None):
	if not doc.flags.auto_created:
		is_dairy = frappe.db.get_value("Company", doc.company, "is_dairy")
		if is_dairy:
			temp_type = doc.doctype
			vlcc_list = frappe.get_all("Village Level Collection Centre")
			for vlcc in vlcc_list:
				if frappe.db.exists("Company", vlcc.get('name')):
					create_taxes_charges_template(temp_type, doc, vlcc.get('name'))

def sales_temp_permission(user):
	return template_permission('Sales Taxes and Charges Template', user)

def purchase_temp_permission(user):
	return template_permission('Purchase Taxes and Charges Template', user)

def template_permission(doctype,user=None):
	if not user:
		user = frappe.session.user
	company = frappe.db.get_value("User", user, "company")
	if user != 'Administrator':
		return """`tab{0}`.company = '{1}' """.format(doctype,company)