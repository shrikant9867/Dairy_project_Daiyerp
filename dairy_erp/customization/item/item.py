from __future__ import unicode_literals
import frappe
from frappe import _

def update_uom(doc, method=None):
	item_list = frappe.get_all("Item", filters=[("stock_uom", "=", doc.name)])
	for item in item_list:
		frappe.db.set_value("Item",item.get('name'),'is_whole_no',\
							doc.must_be_whole_number)