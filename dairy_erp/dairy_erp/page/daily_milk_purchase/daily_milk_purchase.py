from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


@frappe.whitelist()
def get_data():
	
	fmcr_data = frappe.db.sql("""select farmerid,name,milkquantity,
										clr,fat,snf,rate,amount
								from
									`tabFarmer Milk Collection Record`
								where {0}
								""".format(get_conditions()),as_dict=True)
	count = frappe.db.sql("""select count(name) as count 
							from 
								`tabFarmer Milk Collection Record`
							where {0}
		""".format(get_conditions()),as_dict=True)

	return {"fmcr_data":fmcr_data,"count":count[0].count}

def get_conditions():
	conditions = " 1=1"
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")

	if frappe.session.user != 'Administrator':
		conditions += " and associated_vlcc = '{0}'".format(vlcc)

	return conditions