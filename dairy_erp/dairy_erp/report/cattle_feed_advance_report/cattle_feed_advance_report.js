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
			"hidden": 1,
			"default":frappe.boot.user.first_name
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
			"on_change": function(query_report) {
				console.log("insdie on_change")
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Farmer",
						filters: {"name": frappe.query_report_filters_by_name.farmer.get_value()},
						fieldname: ["full_name"]
					},
					callback: function(r) {
						console.log("insidr e",r.message)
						if(!r.exc && r.message && !in_list(["Administrator", "Guest"], frappe.session.user)){
							if(has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager"])){
								frappe.query_report_filters_by_name.farmer_name.set_input(r.message.full_name);
							}
							query_report.trigger_refresh();
						}
					}
				})
			}
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
		},
		{
			"fieldname":"vlcc_addr",
			"label": __("VLCC Address"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"farmer_name",
			"label": __("Farmer Name"),
			"fieldtype": "Data",
			"hidden": 0
		}	
	],
	onload: function(query_report) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Village Level Collection Centre",
				filters: {"name": frappe.boot.user.first_name},
				fieldname: ["address_display"]
			},
			callback: function(r) {
				console.log("insidr e",r.message.address_display,r.message.address_display.split("<br>"))
				if(!r.exc && r.message && !in_list(["Administrator", "Guest"], frappe.session.user)){
					if(has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager"])){
						// $('body').find("[data-fieldname=vlcc]").val(r.message.company)
						//r.message.address_display = r.message.address_display.split("<br>")
						frappe.query_report_filters_by_name.vlcc_addr.set_input(r.message.address_display);
					}
					query_report.trigger_refresh();
				}
			}
		})
	}
}
