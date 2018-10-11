# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import has_common

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns ,data 

def get_columns():
	columns = [
		_("Quality Type") + ":Data:100",
		_("Cans") + ":Float:100",
		_("Qty") + ":Float:100",
		_("FAT") + ":Float:100",
		_("SNF") + ":Float:100",
		_("Rate") + ":Data:100",
		_("Milk Value") + ":Data:150",
		_("Route") + ":Data:100",
		_("Vlcc Name") + ":Data:0",
		_("Vlcc Id") + ":Data:0",
	]

	return columns

def get_data(filters=None):
	vmcr_list = frappe.db.sql("""
								select
									ifnull(milkquality,''),
									CASE
									    WHEN vmcr.milkquantity <= 40 THEN 1
									    WHEN vmcr.milkquantity > 40 THEN CEIL(vmcr.milkquantity/40)
									END,
									vmcr.milkquantity,
									vmcr.fat,
									vmcr.snf,
									round(vmcr.rate,2),
									round(vmcr.amount,2),
									vmcr.collectionroute,
									vmcr.associated_vlcc,
									RIGHT(
										if(shift = "MORNING",
											long_format_farmer_id,
											long_format_farmer_id_e),
										5)
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									vmcr.shift = '{0}' and
									{1} and date(vmcr.collectiontime) = '{2}' """.format(filters.get('shift'),get_conditions(filters),filters.get('start_date')),as_list=1,debug=1)	

	if str(get_conditions(filters)) == "1=1":
		return []
	else:
		for row in vmcr_list:
			if row[9]:
				farmerid = row[9].split("_")
			if len(farmerid) == 2 and farmerid[1] and len(farmerid[1]) < 5:
				row[9] = (5 - len(farmerid[1]))*"0"+str(farmerid[1])
			if len(farmerid) == 1 and farmerid[0] and len(farmerid[0]) < 5:
				row[9] = (5 - len(farmerid[0]))*"0"+str(farmerid[0])
		return vmcr_list

def get_conditions(filters):
	roles = frappe.get_roles()
	user = frappe.session.user
	cond = "1=1"
	cc_id = ""
	if filters.get('branch_office'):
		cc_id = frappe.db.get_value("Address",{"name":filters.get('branch_office')},"centre_id")
		filters["cc_id"] = cc_id
	if ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) and \
		user != 'Administrator':
		cond += " and vmcr.associated_vlcc = '{0}' and vmcr.societyid = '{1}' ".format(filters.get('vlcc'),filters.get('cc_id'))
	
	if ('Chilling Center Manager' in roles or 'Chilling Center Operator' in roles) and \
		user != 'Administrator':		
		if filters.get("vlcc"):
			cond += " and vmcr.associated_vlcc = '{0}' and vmcr.societyid = '{1}' ".format(filters.get('vlcc'),filters.get('cc_id'))
		if filters.get("all_vlcc"):
			vlcc = frappe.db.get_values("Village Level Collection Centre",{"chilling_centre":filters.get('branch_office')},"name",as_dict=1)
			company = ['"%s"'%comp.get('name') for comp in vlcc]
			cond += " and vmcr.societyid = '{0}' and vmcr.associated_vlcc in  ({company})""".format(filters.get('cc_id'),company=','.join(company))

	if ('Dairy Manager' in roles) and user != 'Administrator':
		if not filters.get("branch_office") and not filters.get("vlcc") and filters.get("all_vlcc"):
 			vlcc_list = [vlcc.get('name') for vlcc in frappe.get_all("Village Level Collection Centre", 'name')]
 			cond += " and vmcr.associated_vlcc in  {0} """.format("(" + ",".join(["'{0}'".format(vlcc) for vlcc in vlcc_list ]) + ")")
 		if filters.get("branch_office") and filters.get("vlcc"):
 			cond += " and vmcr.associated_vlcc = '{0}' and vmcr.societyid = '{1}' ".format(filters.get('vlcc'),filters.get('cc_id'))
 		if filters.get("branch_office") and not filters.get("vlcc") and filters.get("all_vlcc"):
 			cc_vlcc = [vlcc.get('name') for vlcc in frappe.get_all("Village Level Collection Centre",{'chilling_centre':filters.get("branch_office")},'name')]
 			cond += " and vmcr.societyid = '{0}' and vmcr.associated_vlcc in  {1}".format(filters.get('cc_id'),"(" + ",".join(["'{0}'".format(vlcc) for vlcc in cc_vlcc ]) + ")")
 		if not filters.get("branch_office") and filters.get("vlcc"):
 			cond += " and vmcr.associated_vlcc = '{0}' ".format(filters.get('vlcc'))
 	return cond		

@frappe.whitelist()
def get_other_data(role):
	data = {}
	user_doc = frappe.get_doc("User",frappe.session.user)
	data.update({"effective_date":frappe.get_doc("Dairy Setting").rate_effective_from})
	if "Chilling Center Manager" in role or "Chilling Center Operator" in role:
		data['vlcc'] = ""
		data['branch_office'] = user_doc.branch_office
	if "Vlcc Manager" in role or "Vlcc Operator" in role:
		data['vlcc'] = user_doc.company
		data['branch_office'] = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.company},"chilling_centre")	
	return data