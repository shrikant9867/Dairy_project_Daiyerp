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
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd":1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd":1,
			"on_change":function(){
				var to_date = frappe.query_report_filters_by_name.to_date.get_value()
				var from_date = frappe.query_report_filters_by_name.from_date.get_value()
				if (frappe.datetime.str_to_obj(to_date) < frappe.datetime.str_to_obj(from_date)){
					frappe.throw("To date cannot be less than from date")
				}
			}
		}

	]
}
