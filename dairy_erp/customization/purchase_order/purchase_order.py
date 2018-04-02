import frappe

def update_material_indent(doc, method=None):
	# update is_dropship on material indent if PO is dropship
	if doc.is_dropship or doc.chilling_centre:
		material_req = [ row.material_request for row in doc.items if row.material_request]
		if material_req:
			material_req = [ mi for mi in set(material_req)]
			for mi in material_req:
				frappe.db.set_value("Material Request", mi, "is_dropship", doc.is_dropship)
				frappe.db.set_value("Material Request", mi, "chilling_centre", doc.chilling_centre)
			frappe.db.commit()

def update_chilling_centre_flag(doc, method=None):
	pass
	# if user is cc and dropship checked , check chilling centre
	# user = frappe.session.user
	# operator_type = frappe.db.get_value("User", user, "operator_type")
	# if operator_type and operator_type == "Chilling Centre" and doc.is_dropship:
	# 	doc.chilling_centre = 1
	# elif doc.chilling_centre:
	# 	doc.chilling_centre = 0