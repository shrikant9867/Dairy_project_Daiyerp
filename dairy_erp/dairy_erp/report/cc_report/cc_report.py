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
		_("Type") + ":Data:100",
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
									    WHEN vmcr.milkquantity > 40 THEN FLOOR(vmcr.milkquantity/40)
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