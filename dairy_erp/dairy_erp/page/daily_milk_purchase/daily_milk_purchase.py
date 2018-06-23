from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


@frappe.whitelist()
def get_data():
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")
	fmcr_data = frappe.db.sql("""select farmerid,name,milkquantity,
										clr,fat,snf,rate,amount
								from
									`tabFarmer Milk Collection Record`
								where associated_vlcc = %s
								""",(vlcc),as_dict=True)
	count = frappe.db.sql("""select count(name) as count 
							from 
								`tabFarmer Milk Collection Record`
							where associated_vlcc = %s
		""",(vlcc),as_dict=True)

	return {"fmcr_data":fmcr_data,"count":count[0].count}