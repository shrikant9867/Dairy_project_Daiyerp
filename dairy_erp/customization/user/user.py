import frappe
from frappe.utils import has_common

def add_user_permission(doc, method=None):
	if has_common([doc.operator_type], ["Chilling Centre","Camp Office","Plant"]):
		# address - branch office
		create_user_permission(doc.email, "Address", doc.branch_office)

	if has_common([doc.operator_type], ["Camp Office", "VLCC"]) and doc.company:
		# company - dairy
		create_user_permission(doc.email, "Company", doc.company)
		manager_role = ['Vlcc Manager', 'Camp Manager', 'Dairy Manager']
		roles = frappe.get_roles()
		if doc.operator_type == "VLCC" and has_common(roles, manager_role):
			doc.add_roles("Vlcc Operator")

def create_user_permission(user,doctype,docname):
	try:
		user_perm = frappe.new_doc("User Permission")
		user_perm.user = user
		user_perm.allow = doctype
		user_perm.for_value = docname
		user_perm.apply_for_all_roles = 0
		user_perm.flags.ignore_permissions = True
		user_perm.flags.ignore_mandatory = True
		user_perm.save()
	except Exception as e:
		print frappe.get_traceback()
		frappe.msgprint("User Permission creation failed for user {0}".format(user))