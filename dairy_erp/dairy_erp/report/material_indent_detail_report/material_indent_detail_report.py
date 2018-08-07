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
	result = frappe.db.sql("""select 
										mi.name,
										mi.material_request_type,
										mi.camp_office,
										mi.company,
										mi.transaction_date,
										mi.status,
										mi.schedule_date,
										mi_item.item_code,
										mi_item.qty

							from 
								`tabMaterial Request` mi,
								`tabMaterial Request Item` mi_item
								{0} and
								mi_item.parent = mi.name
			""" .format(get_conditions(filters)),as_list=1,debug=1)
	return result

def get_conditions(filters):
	cond = ''
	if filters.get('camp_office') and filters.get('from_date') and filters.get('to_date') and filters.get('vlcc_company'):
		cond = "where mi.camp_office = '{0}' and (mi.transaction_date BETWEEN '{1}' AND '{2}') and mi.company = '{3}' ".format(filters.get('camp_office'),filters.get('from_date'),filters.get('to_date'),filters.get('vlcc_company'))

	elif filters.get('camp_office') and filters.get('from_date') and filters.get('to_date'):
		cond = "where mi.camp_office = '{0}' and (mi.transaction_date BETWEEN '{1}' AND '{2}')".format(filters.get('camp_office'),filters.get('from_date'),filters.get('to_date'))
	
	elif filters.get('camp_office') and filters.get('from_date'):
		cond = "where mi.camp_office = '{0}' and mi.transaction_date >= '{1}'".format(filters.get('camp_office'),filters.get('from_date'))

	elif filters.get('camp_office') and filters.get('to_date'):
		cond = "where mi.camp_office = '{0}' and mi.transaction_date < '{1}'".format(filters.get('camp_office'),filters.get('to_date'))

	elif filters.get('from_date') and filters.get('to_date'):
		cond = "where (mi.transaction_date BETWEEN '{0}' AND '{1}') ".format(filters.get('from_date'),filters.get('to_date'))

	elif filters.get('vlcc_company'):
		cond = "where mi.company = '{0}' ".format(filters.get("vlcc_company"))

	elif filters.get('camp_office'):
		cond = "where mi.camp_office = '{0}' ".format(filters.get("camp_office"))	

	elif filters.get('camp_office') and filters.get('vlcc_company'):
		cond = "where mi.camp_office = '{0}' and mi.company = '{1}'".format(filters.get('camp_office'),filters.get('vlcc_company'))

	elif filters.get('camp_office') and filters.get('to_date') and filters.get('vlcc_company'):
		cond = "where mi.camp_office = '{0}' and mi.transaction_date < '{1}' and mi.company = '{2}'".format(filters.get('camp_office'),filters.get('to_date'),filters.get('vlcc_company'))

	elif filters.get('camp_office') and filters.get('from_date') and filters.get('vlcc_company'):
		cond = "where mi.camp_office = '{0}' and mi.transaction_date > '{1}' and mi.company = '{2}'".format(filters.get('camp_office'),filters.get('from_date'),filters.get('vlcc_company'))

	elif filters.get('from_date') and filters.get('to_date') and filters.get('vlcc_company') :
		cond = "where (mi.transaction_date BETWEEN '{0}' AND '{1}') and mi.company = '{2}' ".format(filters.get('from_date'),filters.get('to_date'),filters.get('vlcc_company'))

	elif filters.get('from_date'):
		cond = "where mi.transaction_date >= '{0}'".format(filters.get('from_date'))

	elif filters.get('to_date'):
		cond = "where mi.transaction_date <= '{0}'".format(filters.get("to_date"))	

	else:
		cond = "where 1=1"	

	return cond

def get_colums():
	columns = [("Name") + ":Link/Material Request:100",
				("Type") + ":Data:100",
				("Camp Office") + ":Data/Address:200",
				("VLCC Company") + ":Data/Company:150",
				("Transation Date") + ":Date:100",
				("Status") + ":Data:100",
				("Required Date") + ":Date:100",
				("Item Code") + ":Data/Item:100",
				("Qty") + ":Data:100",	
				]	
	return columns
