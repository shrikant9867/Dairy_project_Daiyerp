# Copyright (c) 2015, Indictrans Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import print_function, unicode_literals
import frappe
from frappe.utils import has_common


def get_associated_vlcc(doctype,text,searchfields,start,pagelen,filters):

	if has_common(frappe.get_roles(), ["Camp Manager"]):
		user_details = frappe.db.get_value("User", frappe.session.user, ['branch_office','company'],as_dict=True)
		
		comp = frappe.db.sql_list("""
					select name
						from
					`tabVillage Level Collection Centre`
						where
					camp_office = %s
			""",(user_details.get('branch_office')))
		comp.extend([user_details.get('company')])

		return frappe.db.sql("""select name 
						from
							`tabCompany`
						where
							name in {0} and 
							name like '{text}'""".
							format("(" + ",".join(["'{0}'".format(a) for a in comp ]) + ")",
							text= "%%%s%%" % text))


def get_filtered_warehouse(doctype,text,searchfields,start,pagelen,filters):

	branch_office = frappe.db.get_value("User", frappe.session.user, ['branch_office','company'],as_dict=True)

	if has_common(frappe.get_roles(), ["Camp Manager", "Camp Operator"]):
		camp_wh = frappe.db.get_value("Address",branch_office.get('branch_office'), 'warehouse')
		vlcc_wh = frappe.db.sql_list("""select warehouse from `tabVillage Level Collection Centre` 
						where camp_office = %s""",(branch_office.get('branch_office')))
		vlcc_wh.extend([camp_wh])
		return frappe.db.sql("""select name 
						from
							`tabWarehouse`
						where
							name in {0} and 
							name like '{text}'""".
							format("(" + ",".join(["'{0}'".format(a) for a in vlcc_wh ]) + ")",
							text= "%%%s%%" % text))

	if has_common(frappe.get_roles(), ["Vlcc Manager", "Vlcc Operator"]):
		return frappe.db.sql("""select name 
						from
							`tabWarehouse`
						where
							company = %s and 
							name like '{text}'""".
							format(text= "%%%s%%" % text),(branch_office.get('company')))


