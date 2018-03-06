from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json

'''

'''
@frappe.whitelist()
def get_partial_quatity(doc,method):
	if doc.status == "To Bill" and doc.docstatus == 1:
		for item in doc.items:
			if item.material_request:	
				mi_doc = frappe.get_doc("Material Request",item.material_request)
				for mi_item in mi_doc.items:
					if item.item_code == mi_item.item_code:
						if mi_item.new_dn_qty >= item.qty:
							new_dn_qty = mi_item.new_dn_qty - item.qty
							if new_dn_qty == 0:
								frappe.db.sql(""" update `tabMaterial Request Item` 
									set new_dn_qty = {0} where name = '{1}' """.format(new_dn_qty,mi_item.name),debug =1)
								
								frappe.db.sql(""" update `tabMaterial Request` 
									set status = 'Delivered',per_delivered = 100 where name = '{0}' """.format(item.material_request),debug =1)
								mr_doc = frappe.get_doc("Material Request",item.material_request)
								mr_doc.per_delivered = 100
								mr_doc.set_status("Delivered")
								mr_doc.save()
							
							else:	
								frappe.db.sql(""" update  `tabMaterial Request Item` 
									set new_dn_qty = {0} where name = '{1}' """.format(new_dn_qty,mi_item.name),debug =1)
						else:
							frappe.throw(_("<b>Dispatch Quantity</b> should not be greater than <b>Requested Quantity</b>"))
					



