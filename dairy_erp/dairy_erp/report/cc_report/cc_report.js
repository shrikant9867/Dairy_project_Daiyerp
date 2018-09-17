// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */
var field_list = [
		{
			"fieldname":"start_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"shift",
			"label": __("Shift"),
			"fieldtype": "Select",
			"options":["MORNING","EVENING"],
			"default": "MORNING"
		},
		{
			"fieldname":"vlcc",
			"label": __("VLCC"),
			"fieldtype": "Link",
			"options":"Village Level Collection Centre",
			"get_query": function (query_report) {
				return {
					"filters": {
						"chilling_centre": frappe.query_report_filters_by_name.branch_office.get_value()
					}
				}
			},
			"on_change": function(query_report) {
				frappe.query_report_filters_by_name.all_vlcc.set_input(0);
				query_report.trigger_refresh();
			}
		},
		{
			"fieldname":"all_vlcc",
			"label": __("All Vlcc"),
			"fieldtype": "Check",
			"on_change": function(query_report) {
				frappe.query_report_filters_by_name.vlcc.set_input("");
				query_report.trigger_refresh();
			}
		},
		{
			"fieldname":"route",
			"label": __("Route"),
			"fieldtype": "Data"
		},
		{
			"fieldname":"rate_effective_date",
			"label": __("Rate Effective from"),
			"fieldtype": "Date",
			"hidden":1
		},
		{
			"fieldname":"vlcc_id",
			"label": __("VLCC Id"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"operator_type",
			"label": __("Operator Type"),
			"fieldtype": "Data",
			"hidden": 1
		}
	]

var cc_field = {
	"fieldname":"branch_office",
	"label": __("Branch Office"),
	"fieldtype": "Link",
	"options":"Address",
	"get_query": function (query_report) {
		return {
			"filters": {
				"address_type": "Chilling Centre"					
			}
		}
	}
}

if(has_common(frappe.user_roles, ["Chilling Center Manager", "Chilling Center Operator"])){
	cc_field["hidden"] = 1
	field_list.splice(0, 0, cc_field);
}

if(has_common(frappe.user_roles, ["Dairy Manager"])){
	field_list.splice(2, 0, cc_field);
}

frappe.query_reports["CC Report"] = {
	"filters": field_list,
	onload: function(query_report) {
		frappe.call({
            method: "dairy_erp.dairy_erp.report.cc_report.cc_report.get_other_data",
            args:{
            	'role':frappe.user_roles
            },
            callback: function(r){
                if(r.message){
                	console.log("inside callback",r.message)
                	frappe.query_report_filters_by_name.vlcc.set_input(r.message.vlcc);
					frappe.query_report_filters_by_name.operator_type.set_input(r.message.operator_type);
					frappe.query_report_filters_by_name.branch_office.set_input(r.message.branch_office);
					frappe.query_report_filters_by_name.vlcc_id.set_input(r.message.vlcc_id);
                	frappe.query_report_filters_by_name.rate_effective_date.set_input(r.message.effective_date);
                }
                query_report.trigger_refresh();
            }
        })
	}
}
