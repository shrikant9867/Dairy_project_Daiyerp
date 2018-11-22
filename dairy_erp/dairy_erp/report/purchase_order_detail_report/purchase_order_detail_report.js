// Copyright (c) 2018, Stellapps Technologies Private Ltd.
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchase Order Detail Report"] = {
	"filters": [
		{
			"fieldname":"camp_office",
			"label": __("P&I"),
			"fieldtype": "Link",
			"options": "Address",
			"get_query": function (query_report) {
				return {
				"filters": {
					"address_type": "Camp Office"
					}
				}
			},
			"width": "80"
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname":"vlcc_company",
			"label": __("VLCC Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": "80"
		}
	]
}
