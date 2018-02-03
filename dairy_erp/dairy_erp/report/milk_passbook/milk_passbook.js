// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Milk Passbook"] = {
	"filters": [
		{
			"fieldname":"farmer_id",
			"label": __("Farmer ID"),
			"fieldtype": "Link",
			"options": "Farmer"
		},
		{
			"fieldname":"shift",
			"label": __("Shift"),
			"fieldtype": "Select",
			"options": '\nMORNING\nEVENING',
			"default": " "
		}
		/*{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		}*/

	]
}
