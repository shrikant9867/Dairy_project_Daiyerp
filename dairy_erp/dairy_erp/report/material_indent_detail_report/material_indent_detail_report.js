// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Material Indent Detail Report"] = {
	"filters": [
		{
			"fieldname":"camp_office",
			"label": __("Camp Office"),
			"fieldtype": "Link",
			"options": "Address",
			"get_query": function (query_report) {
				return {
					"filters": {
						"address_type": "Camp Office"
						}
					}
			},
			"width": "150"
		},
		{
			"fieldname":"vlcc_company",
			"label": __("VLCC"),
			"fieldtype": "Link",
			"options": "Village Level Collection Centre",
			"get_query": function (query_report) {
				var camp_office = frappe.query_report_filters_by_name.camp_office.get_value();
				if(camp_office){
					return {
						"filters": {
							"camp_office": camp_office					}
						}
				}
			},
			"width": "150"
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
		}
	]
}
