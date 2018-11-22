// Copyright (c) 2018, Stellapps Technologies Private Ltd.
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Individual Farmer Payment Settlement"] = {
	"filters": [
		{
			"fieldname":"vlcc",
			"label": __("VLCC"),
			"fieldtype": "Data",
			"options":"Company",
			"default":frappe.boot.user.first_name,
			"read_only":1
			
		},
		{
			"fieldname":"cycle",
			"label": __("Cycle"),
			"fieldtype": "Link",
			"options": "Farmer Date Computation",
			"reqd":1,
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
			"reqd":0,
			"on_change":function(query_report){
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Farmer",
						filters: {"name": frappe.query_report_filters_by_name.farmer.get_value()},
						fieldname: ["full_name"]
					},
					callback:function(r){
						if(r.message){

							frappe.query_report_filters_by_name.full_name.set_input(r.message['full_name']);
							query_report.trigger_refresh();		
						}
						else{

							frappe.query_report_filters_by_name.full_name.set_input("");
							query_report.trigger_refresh();
						}		
					}
				})
			}
		},
		{
			"fieldname":"full_name",
			"label": __("Full Name"),
			"fieldtype": "Data",
			"read_only":1
		}
		
	]
}
