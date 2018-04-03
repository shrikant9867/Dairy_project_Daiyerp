import frappe

def update_material_indent(doc, method=None):
	# update is_dropship on material indent if PO is dropship
	if doc.is_dropship:
		material_req = [ row.material_request for row in doc.items if row.material_request]
		if material_req:
			material_req = [ mi for mi in set(material_req)]
			for mi in material_req:
				frappe.db.set_value("Material Request", mi, "is_dropship", doc.is_dropship)
			frappe.db.commit()