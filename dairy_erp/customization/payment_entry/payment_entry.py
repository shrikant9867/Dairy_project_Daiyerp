import frappe

def validate_by_credit_invoice(doc, method=None):
	if not doc.flags.ignore_credit_validation:
		for inv in doc.references:
			if inv.get('reference_doctype') == "Sales Invoice":
				by_credit_amt = frappe.db.get_value("Sales Invoice", inv.get('reference_name'), "by_credit")
				if by_credit_amt > 0:
					frappe.throw("You can not make payment of Invoice {0} as By credit amount is present.".format(inv.get('reference_name')))