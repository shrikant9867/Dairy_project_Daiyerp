from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document


def set_party_account(doc, method=None):
	if not doc.accounts:
		vlcc_name = frappe.db.get_value("User",frappe.session.user,'company')
		custmer_doc = doc
		custmer_doc.company = vlcc_name
		custmer_doc.append("accounts",
			{
			"company": vlcc_name,
			"account": frappe.db.get_value("Company",vlcc_name, "default_receivable_account")
			})