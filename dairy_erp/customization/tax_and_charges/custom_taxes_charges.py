import frappe

def autoname(doc, method):
	if not doc.vlcc:
		doc.name = doc.title
	else:
		vlcc_abbr = frappe.db.get_value("Company", doc.vlcc, "abbr")
		doc.name = doc.title + " - " + vlcc_abbr