import frappe
import json
from frappe.utils import has_common

def contact_permission(user):
	roles = frappe.get_roles()
	user_comp = frappe.db.get_value("User", frappe.session.user, ['company','operator_type'],as_dict=1)
	
	if 'Vlcc Manager' in roles or 'Vlcc Operator' in roles:
		return """(`tabContact`.vlcc = '{0}')""".format(user_comp.get('company'))