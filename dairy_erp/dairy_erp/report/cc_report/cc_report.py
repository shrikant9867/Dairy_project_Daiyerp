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
		_("Milk Value") + ":Float:150"
	]

	return columns

def get_data(filters=None):
	vmcr_list = frappe.db.sql("""
								select
									vmcr.milkquality,
									CASE
									    WHEN vmcr.milkquantity <= 40 THEN 1
									    WHEN vmcr.milkquantity > 40 THEN CEIL(vmcr.milkquantity/40)
									END,
									vmcr.milkquantity,
									vmcr.fat,
									vmcr.snf,
									vmcr.rate,
									vmcr.amount
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									vmcr.shift = '{0}' and
									{1} and date(vmcr.collectiontime) = '{2}' """.format(filters.get('shift'),get_conditions(filters),filters.get('start_date')),as_list=1,debug=1)	
	return vmcr_list

def get_conditions(filters):
	cond = "1=1"
	if filters.get('operator_type') == "Chilling Centre":
		vlcc = frappe.db.get_values("Village Level Collection Centre",{"chilling_centre":filters.get('branch_office')},"name",as_dict=1)
		company = ['"%s"'%comp.get('name') for comp in vlcc]
		cond += " and vmcr.associated_vlcc in  ({company})""".format(company=','.join(company))
	elif filters.get('operator_type') == "VLCC":
		cond += " and vmcr.associated_vlcc = '{0}' """.format(filters.get('vlcc'))
	return cond

@frappe.whitelist()
def get_other_data(role):
	data = {}
	user_doc = frappe.get_doc("User",frappe.session.user)
	if "Vlcc Operator" in role or "Vlcc Manager" in role:
		data['vlcc'] = user_doc.company
		data['operator_type'] = user_doc.operator_type
		data['vlcc_id'] = frappe.db.get_value("Village Level Collection Centre",{'name':user_doc.company},"amcu_id")
		data['branch_office'] = frappe.db.get_value("Village Level Collection Centre",{'name':user_doc.company},"chilling_centre")
		data['address'] = get_address(data.get('branch_office'))
	if "Chilling Center Manager" in role or "Chilling Center Operator" in role:
		data['vlcc'] = ""
		data['operator_type'] = user_doc.operator_type
		data['branch_office'] = user_doc.branch_office
		data['address'] = get_address(user_doc.branch_office)
	return data
		
def get_address(name):
	final_addr = ""
	addr = frappe.get_doc("Address",name)
	if addr.get('address_line1'):
		final_addr += addr.get('address_line1') + "<br>"
	if addr.get('address_line2'):
	    final_addr += addr.get('address_line2') + "<br>"
	if addr.get('city'):
	    final_addr += addr.get('city') + "<br>" 
	if addr.get('state'):
	    final_addr += addr.get('state') + "<br>" 
	if addr.get('pincode'):
	    final_addr += addr.get('pincode') + "<br>" 
	if addr.get('country'):
	    final_addr += addr.get('country') + "<br>" 
	if addr.get('phone'):
	    final_addr += addr.get('phone') + "<br>"
	if addr.get('fax'):
	    final_addr += addr.get('fax') + "<br>"
	if addr.get('email_id'):
	    final_addr += addr.get('email_id') + "<br>"
	return final_addr
