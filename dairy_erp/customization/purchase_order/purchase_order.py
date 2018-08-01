import frappe
from frappe import _

def update_material_indent(doc, method=None):
	# update is_dropship on material indent if PO is dropship
	if doc.is_dropship:
		material_req = [ row.material_request for row in doc.items if row.material_request]
		if material_req:
			material_req = [ mi for mi in set(material_req)]
			for mi in material_req:
				frappe.db.set_value("Material Request", mi, "is_dropship", doc.is_dropship)
				mi_doc = frappe.get_doc("Material Request",mi)
				for row in mi_doc.items:
					frappe.db.set_value("Material Request Item", row.name ,"is_dropship", doc.is_dropship) 
			frappe.db.commit()

def validate_price_list(doc, method = None):
	user_doc = frappe.db.get_value("User",frappe.session.user,\
			['company','operator_type','branch_office'],as_dict=1)
	
	if user_doc.get('operator_type') == "VLCC":
		if doc.buying_price_list not in ["GTVLCCB","LVLCCB-"+doc.get('company')]:
			frappe.throw(_("Please Create Material Price List First"))
	
	if user_doc.get('operator_type') == "Camp Office":
		if doc.buying_price_list not in ["GTCOB", "LCOB-"+ user_doc.get('branch_office')]:
			frappe.throw(_("Please Create Material Price List First"))

@frappe.whitelist()	
def make_is_dropship():
	if frappe.db.get_singles_dict('Dairy Configuration').get('is_dropship'):
		return "True"
	else:
		return "False"	
