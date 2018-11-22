# Copyright (c) 2018, Stellapps Technologies Private Ltd.
# License: GNU General Public License v3. See license.txt

from __future__ import print_function, unicode_literals
import frappe
from frappe.utils import has_common, flt


def get_associated_vlcc(doctype,text,searchfields,start,pagelen,filters):

	if has_common(frappe.get_roles(), ["Camp Manager"]) and frappe.session.user != 'Administrator':
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
	else:
		return frappe.db.sql("""select name 
						from
							`tabCompany`
						where
							name like '{text}'""".
							format(text= "%%%s%%" % text))



def get_filtered_warehouse(doctype,text,searchfields,start,pagelen,filters):

	branch_office = frappe.db.get_value("User", frappe.session.user, ['branch_office','company'],as_dict=True)

	if has_common(frappe.get_roles(), ["Camp Manager", "Camp Operator"]) and frappe.session.user != 'Administrator':
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

	elif has_common(frappe.get_roles(), ["Vlcc Manager", "Vlcc Operator"]) and frappe.session.user != 'Administrator':
		return frappe.db.sql("""select name 
						from
							`tabWarehouse`
						where
							company = '{comp}' and 
							name like '{text}'""".
							format(comp=branch_office.get('company'),text= "%%%s%%" % text))
	else:
		return frappe.db.sql("""select name 
						from
							`tabWarehouse`
						where
							name like '{text}'""".
							format(text= "%%%s%%" % text))


def get_actual_qty_from_bin(item_code, warehouse):
	if item_code and warehouse:
		balance_qty = frappe.db.sql("""select ifnull(actual_qty,0) from `tabBin`
			where item_code=%s and warehouse=%s""", (item_code, warehouse))

		return flt(balance_qty[0][0]) if balance_qty else 0.0
