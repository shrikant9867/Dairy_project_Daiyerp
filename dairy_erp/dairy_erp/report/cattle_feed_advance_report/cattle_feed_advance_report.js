// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cattle Feed Advance Report"] = {
	"filters": [
		{
			"fieldname":"vlcc",
			"label": __("VLCC"),
			"fieldtype": "Link",
			"options":"Company",
			"hidden": 1
		},
		{
			"fieldname":"farmer",
			"label": __("Farmer"),
			"fieldtype": "Link",
			"options":"Farmer",
			"get_query": function (query_report) {
				var vlcc_name = frappe.query_report_filters_by_name.vlcc.get_value();
				if(vlcc_name){
					return {
						"filters": {
							"vlcc_name": vlcc_name					
							}
						}
				}
			},
			"reqd":1
		},
		{
			"fieldname":"start_date",
			"label": __("Start Date"),
			"fieldtype": "Date",
			"reqd":1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"end_date",
			"label": __("End Date"),
			"fieldtype": "Date",
			"reqd":1,
			"default": frappe.datetime.get_today()
		}	
	],
	onload: function(query_report) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "User",
				filters: {"name": frappe.session.user},
				fieldname: ["company"]
			},
			callback: function(r) {
				if(!r.exc && r.message && !in_list(["Administrator", "Guest"], frappe.session.user)){
					if(has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager"])){
						// $('body').find("[data-fieldname=vlcc]").val(r.message.company)
						frappe.query_report_filters_by_name.vlcc.set_input(r.message.company);
					}
					query_report.trigger_refresh();
				}
			}
		})
	}
}
