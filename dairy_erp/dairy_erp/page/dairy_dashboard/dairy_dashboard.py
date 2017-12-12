from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


@frappe.whitelist()
def get_address():
	final_addr = ""
	address = frappe.db.sql("""select pincode,address_line1,state,address_line2,city,country,email_id,phone,fax 
								from `tabAddress` where address_type = 'Head Office' """,as_dict=1)
	if address:
		for addr in address:
			if addr.get('address_line1'):
				final_addr = addr.get('address_line1') + "<br>"
			if addr.get('address_line2'):
				final_addr += addr.get('address_line2') + "<br>"
			if addr.get('city'):
				final_addr += addr.get('city') + "<br>" 
			if addr.get('state'):
				final_addr += addr.get('state') + "<br>" 
			if addr.get('pincode'):
				final_addr += addr.get('pincode') + "<br>" 
			if addr.get('country'):
				final_addr += addr.get('country') + "<br>" 
			if addr.get('phone'):
				final_addr += addr.get('phone') + "<br>"
			if addr.get('fax'):
				final_addr += addr.get('fax') + "<br>"
			if addr.get('email_id'):
				final_addr += addr.get('email_id') + "<br>"