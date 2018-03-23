import frappe
from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to


def create_manager_operator_user(doc, method=None):
	# create manager and operator if email_id & name available
	if not doc.is_new() and doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		if doc.manager_name and doc.manager_email:
			# make manager user
			role_manager = {"Chilling Centre": "Camp Manager","Camp Office": "Camp Manager","Plant": "Camp Manager"}
			create_user(doc, "Manager", role_manager[doc.address_type])
			
		if doc.different_operator and doc.operator_name and doc.user:
			# make operator user
			role_manager = {"Chilling Centre": "Chilling Center Operator","Camp Office": "Camp Operator","Plant": ""}
			create_user(doc, "Operator", role_manager[doc.address_type])


def create_user(doc, operator_manager,role=None):
	try:
		email = doc.manager_email if operator_manager == "Manager" else doc.user
		if not frappe.db.exists("User", email):
			user = frappe.new_doc("User")
			user.email = email
			user.first_name = doc.manager_name if operator_manager == "Manager" else doc.operator_name
			user.operator_type = doc.address_type
			user.branch_office = doc.name
			user.company = frappe.db.get_value("Company",{"is_dairy":1},"name") or ""
			user.send_welcome_email = 0
			user.new_password = "admin"
			user.flags.ignore_permissions = True
			user.flags.ignore_mandatory = True
			user.save()

			# add role
			if role:
				user.add_roles(role)
			else:
				add_all_roles_to(user.name)
	except Exception as e:
		frappe.throw("Unable to create User. Please contact System Administrator")