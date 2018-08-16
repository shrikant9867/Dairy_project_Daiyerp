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

def check_vlcc_local_customer(doc, method=None):
	vlcc_name = frappe.db.get_value("User",frappe.session.user,'company')
	cust_name = frappe.db.get_value("Customer",{'company':vlcc_name,'customer_group':'Vlcc Local Customer'},"name")
	if cust_name:
		cust_company = cust_name.split('-Local')[0]
		if doc.customer_group == "Vlcc Local Customer" and cust_name and cust_company and cust_company == vlcc_name: 
			frappe.throw(_("You can not create multiple 'vlcc local customer',because by default one 'Vlcc local customer' has created on creation of vlcc."))
