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
		_("Rate") + ":Float:100",
		_("Milk Value") + ":Float:150",
		_("Vlcc Name") + ":Data:0",
		_("Vlcc Id") + ":Data:0",
	]

	return columns

def get_data(filters=None):
	vmcr_list = frappe.db.sql("""
								select
									CASE
									    WHEN vmcr.status = "Accept" THEN "G"
									    WHEN vmcr.status = "Reject" THEN "B"
									END,
									CASE
									    WHEN vmcr.milkquantity <= 40 THEN 1
									    WHEN vmcr.milkquantity > 40 THEN CEIL(vmcr.milkquantity/40)
									END,
									vmcr.milkquantity,
									vmcr.fat,
									vmcr.snf,
									vmcr.rate,
									vmcr.amount,
									vmcr.associated_vlcc,
									vmcr.farmerid
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									vmcr.shift = '{0}' and
									{1} and date(vmcr.collectiontime) = '{2}' """.format(filters.get('shift'),get_conditions(filters),filters.get('start_date')),as_list=1,debug=0)	
	
	if filters.get('operator_type') == "Chilling Centre" and (filters.get('vlcc') or filters.get('all_vlcc')):
		return vmcr_list
	elif filters.get('branch_office') and not filters.get('operator_type') == "Chilling Centre":
		return vmcr_list
	else:
		return []	 	

def get_conditions(filters):
	cond = "1=1"
	if filters.get('branch_office'):
		if filters.get('vlcc'):
			cond += " and vmcr.associated_vlcc = '{0}' ".format(filters.get('vlcc'))
		if filters.get('all_vlcc'):
			vlcc = frappe.db.get_values("Village Level Collection Centre",{"chilling_centre":filters.get('branch_office')},"name",as_dict=1)
			company = ['"%s"'%comp.get('name') for comp in vlcc]
			cond += " and vmcr.associated_vlcc in  ({company})""".format(company=','.join(company))
		else:
			cc_id = frappe.db.get_value("Address",{"name":filters.get('branch_office')},"centre_id")
			cond += " and vmcr.societyid = '{0}' ".format(cc_id)
	return cond

@frappe.whitelist()
def get_other_data(role):
	data = {}
	user_doc = frappe.get_doc("User",frappe.session.user)
	data.update({"effective_date":frappe.get_doc("Dairy Setting").rate_effective_from})
	if "Chilling Center Manager" in role or "Chilling Center Operator" in role:
		data['vlcc'] = ""
		data['operator_type'] = user_doc.operator_type
		data['branch_office'] = user_doc.branch_office
	return data