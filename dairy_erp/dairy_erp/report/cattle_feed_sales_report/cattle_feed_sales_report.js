// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cattle Feed Sales Report"] = {
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
			"reqd":1,
			"on_change":function(query_report){
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Farmer",
						filters: {"name": frappe.query_report_filters_by_name.farmer.get_value()},
						fieldname: ["farmer_id","full_name"]
					},
					callback:function(r){
						if(r.message){
							frappe.query_report_filters_by_name.farmer_id.set_input(r.message['farmer_id']);
							frappe.query_report_filters_by_name.full_name.set_input(r.message['full_name']);
							query_report.trigger_refresh();		
						}
						else{
							frappe.query_report_filters_by_name.farmer_id.set_input("sas");
							frappe.query_report_filters_by_name.full_name.set_input("asa");
							query_report.trigger_refresh();
						}		
					}
				})
			}
		},
		{
			"fieldname":"farmer_id",
			"label": __("Farmer id"),
			"fieldtype": "Data",
			"read_only":1
		},
		{
			"fieldname":"full_name",
			"label": __("Full Name"),
			"fieldtype": "Data",
			"read_only":1
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
	},
	"formatter":function (row, cell, value, columnDef, dataContext, default_formatter) {
		value = default_formatter(row, cell, value, columnDef, dataContext);
        //console.log("concad", dataContext)
	    if(columnDef.id == "Explanation") {
	    	//console.log(dataContext,"customer customer")
            value = "<input type='text' name='fname'>";
	    }
	    return value;
	}
}
