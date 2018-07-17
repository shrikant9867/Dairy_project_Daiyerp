import frappe
from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to


def create_manager_operator_user(doc, method=None):
	# create manager and operator if email_id & name available
	if not doc.is_new() and doc.address_type in ["Chilling Centre","Camp Office","Plant"]:
		if doc.manager_name and doc.manager_email:
			# make manager user
			role_manager = {"Chilling Centre": "Chilling Center Manager","Camp Office": "Camp Manager","Plant": "Plant Manager"}
			create_user(doc, "Manager", role_manager[doc.address_type])
			
		if doc.different_operator and doc.operator_name and doc.user:
			# make operator user
			role_manager = {"Chilling Centre": "Chilling Center Operator","Camp Office": "Camp Operator","Plant": "Plant Operator"}
			create_user(doc, "Operator", role_manager[doc.address_type])

def check_camp_office_for_cc(doc, method=None):
	# camp office should be mandatory for CC
	if doc.address_type == "Chilling Centre" and not doc.associated_camp_office:
		frappe.throw("Associated Camp Office is mandatory for Address type Chilling Centre")
	if doc.address_type in ['Chilling Centre', 'Camp Office', 'Plant'] and (not doc.manager_name or not doc.manager_email):
		frappe.throw("<b>Manager Name</b> and <b>Manager Email</b> are manadatory")


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

def address_permission(user):
	roles = frappe.get_roles()
	user_comp = frappe.db.get_value("User", frappe.session.user, \
		['company','operator_type','vet','branch_office'],as_dict=1)
	head_office = frappe.db.get_value("Address", {"address_type": "Head Office"}, "name")
	
	if ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) and \
		user != 'Administrator':
		vlcc_addr = frappe.db.get_value("Address", {"vlcc":user_comp.get('company'),"address_type":"Vlcc"}, "name")
		vet_addr = frappe.db.get_value("Address", {"vlcc":user_comp.get('company'),"address_type":"Veterinary AI Tech"}, "name")
		addresses = list(frappe.db.get_value("Village Level Collection Centre", user_comp.get('company'), 
						["plant_office", "camp_office", "chilling_centre"]))
		addresses.extend([head_office, vlcc_addr,vet_addr])
		return """(`tabAddress`.name in {0})""".format("(" + ",".join(["'{0}'".format(a) for a in addresses ]) + ")")
	if 'Vet/AI Technician' in roles and user != "Administrator":
		return """(`tabAddress`.vet = '{0}')""".format(user_comp.get('vet'))
	
	if ('Camp Manager' in roles or 'Camp Operator' in roles) and \
		user != "Administrator":
			return """(`tabAddress`.name = '{0}')""".format(user_comp.get('branch_office'))
			# return """(`tabAddress`.associated_camp_office = '{0}' 
			# or `tabAddress`.name = '{0}')""".format(user_comp.get('branch_office'))
	
	if ('Chilling Center Manager' in roles or 'Chilling Center Operator' in roles) and \
		user != "Administrator":
		camp = frappe.db.get_value("Address", user_comp.get('branch_office'),\
			'associated_camp_office')
		return """(`tabAddress`.associated_camp_office = '{0}'
			or `tabAddress`.name = '{0}')""".format(camp)



def set_vet_map(doc, method = None):
	if doc.address_type == "Veterinary AI Tech":
		vlcc = frappe.db.get_value("Veterinary AI Technician",doc.vet,'vlcc')
		doc.vlcc = vlcc