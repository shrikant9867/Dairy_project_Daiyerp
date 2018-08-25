// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CC Report"] = {
	"filters": [
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
			"options":"Company",
			"read_only": 1
		},
		{
			"fieldname":"operator_type",
			"label": __("Operator Type"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"branch_office",
			"label": __("Branch Office"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"route",
			"label": __("Route"),
			"fieldtype": "Data",
			"hidden": 0
		}
	],
	onload: function(query_report) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "User",
				filters: {"name": frappe.session.user},
				fieldname: ["company","operator_type","branch_office"]
			},
			callback: function(r) {
				console.log("inside console",r.message)
				if(!r.exc && r.message && !in_list(["Administrator", "Guest"], frappe.session.user)){
					if(has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager","Chilling Center Manager","Chilling Center Operator"])){
						// $('body').find("[data-fieldname=vlcc]").val(r.message.company)
						frappe.query_report_filters_by_name.vlcc.set_input(r.message.company);
						frappe.query_report_filters_by_name.operator_type.set_input(r.message.operator_type);
						frappe.query_report_filters_by_name.branch_office.set_input(r.message.branch_office);
					}
					query_report.trigger_refresh();
				}
			}
		})
	}
}
