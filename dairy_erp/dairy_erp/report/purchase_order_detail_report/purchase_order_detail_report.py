# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = get_colums()
	data = get_data(filters)
	return columns, data


def get_data(filters):
	result = []
	result = frappe.db.sql("""select po.name,
										po.camp_office,
										po.supplier,
										po.grand_total,
										po.status,
										po_item.material_request,
										mi.company,
										po.transaction_date
			from `tabPurchase Order` po, 
			`tabPurchase Order Item` po_item,
			`tabMaterial Request` mi
			{0} and
			po_item.parent = po.name
			and mi.name = po_item.material_request
			""" .format(get_conditions(filters)),as_list=1,debug=1)
	return result	

def get_conditions(filters):
	cond = ''
	if filters.get('camp_office') and filters.get('from_date') and filters.get('to_date') and filters.get('vlcc_company'):
		cond = "where po.camp_office = '{0}' and (po.transaction_date BETWEEN '{1}' AND '{2}') and mi.company = '{3}' ".format(filters.get('camp_office'),filters.get('from_date'),filters.get('to_date'),filters.get('vlcc_company'))

	elif filters.get('camp_office') and filters.get('from_date') and filters.get('to_date'):
		cond = "where po.camp_office = '{0}' and (po.transaction_date BETWEEN '{1}' AND '{2}')".format(filters.get('camp_office'),filters.get('from_date'),filters.get('to_date'))
	
	elif filters.get('camp_office') and filters.get('from_date'):
		cond = "where po.camp_office = '{0}' and po.transaction_date >= '{1}'".format(filters.get('camp_office'),filters.get('from_date'))

	elif filters.get('camp_office') and filters.get('to_date'):
		cond = "where po.camp_office = '{0}' and po.transaction_date < '{1}'".format(filters.get('camp_office'),filters.get('to_date'))

	elif filters.get('from_date') and filters.get('to_date'):
		cond = "where (po.transaction_date BETWEEN '{0}' AND '{1}') ".format(filters.get('from_date'),filters.get('to_date'))

	elif filters.get('vlcc_company'):
		cond = "where mi.company = '{0}' ".format(filters.get("vlcc_company"))

	elif filters.get('camp_office'):
		cond = "where po.camp_office = '{0}' ".format(filters.get("camp_office"))	

	elif filters.get('camp_office') and filters.get('vlcc_company'):
		cond = "where po.camp_office = '{0}' and mi.company = '{1}'".format(filters.get('camp_office'),filters.get('vlcc_company'))

	elif filters.get('camp_office') and filters.get('to_date') and filters.get('vlcc_company'):
		cond = "where po.camp_office = '{0}' and po.transaction_date < '{1}' and mi.company = '{2}'".format(filters.get('camp_office'),filters.get('to_date'),filters.get('vlcc_company'))

	elif filters.get('camp_office') and filters.get('from_date') and filters.get('vlcc_company'):
		cond = "where po.camp_office = '{0}' and po.transaction_date > '{1}' and mi.company = '{2}'".format(filters.get('camp_office'),filters.get('from_date'),filters.get('vlcc_company'))

	elif filters.get('from_date') and filters.get('to_date') and filters.get('vlcc_company') :
		cond = "where (po.transaction_date BETWEEN '{0}' AND '{1}') and mi.company = '{2}' ".format(filters.get('from_date'),filters.get('to_date'),filters.get('vlcc_company'))

	elif filters.get('from_date'):
		cond = "where po.transaction_date >= '{0}'".format(filters.get('from_date'))

	elif filters.get('to_date'):
		cond = "where po.transaction_date <= '{0}'".format(filters.get("to_date"))	

	else:
		cond = "where 1=1"	

	return cond


def get_colums():
	columns = [("Name") + ":Link/Purchase Order:100",
				("Camp Office") + ":Link/Address:100",
				("Supplier") + ":Link/Supplier:100",
				("Grand Total") + ":Float:100",
				("Status") + ":Data:100",
				("Material Indent") + ":Link/Material Request:100",
				("VLCC Company") + ":Link/Company:100",
				("Posting Date") + ":Date:100",
				]	
	return columns