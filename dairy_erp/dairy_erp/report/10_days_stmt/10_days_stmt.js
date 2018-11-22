// Copyright (c) 2018, Stellapps Technologies Private Ltd.
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["10 Days STMT"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("Form Date"),
			"fieldtype": "Date",
			"reqd":1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd":1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"branch_office",
			"label": __("Chilling Center"),
			"fieldtype": "Link",
			"options":"Address",
			"hidden":1
		}
	],
	onload: function(query_report) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Address",
				filters: {"manager_email": frappe.boot.user.email},
				fieldname: ["name"]
			},
			callback: function(r) {
				if(!r.exc && r.message && !in_list(["Administrator", "Guest"], frappe.session.user)){
					if(has_common(frappe.user_roles, ["Chilling Center Manager", "Chilling Center Operator"])){
						// $('body').find("[data-fieldname=vlcc]").val(r.message.company)
						frappe.query_report_filters_by_name.branch_office.set_input(r.message.name);
					}
					query_report.trigger_refresh();
				}
			}
		})
	}
}
