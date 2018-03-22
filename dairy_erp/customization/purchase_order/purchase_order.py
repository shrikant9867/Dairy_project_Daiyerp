import frappe

def update_material_indent(doc, method=None):
	# update is_dropship on material indent if PO is dropship
	if doc.is_dropship:
		material_req = [ row.material_request for row in doc.items if row.material_request]
		if len(material_req):
			mi = "(" + ",".join("'{0}'".format(mr) for mr in set(material_req))  + ")"
			frappe.db.sql(""" update `tabMaterial Request` set is_dropship = 1 
				where name in {0} """.format(mi))
			frappe.db.commit()