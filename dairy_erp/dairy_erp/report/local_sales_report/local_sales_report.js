// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Local Sales Report"] = {
	"filters": [
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options":"Customer",
			"get_query": function (query_report) {
				return{
					query:"dairy_erp.dairy_erp.report.local_sales_report.local_sales_report.get_customer"
				}
			}
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"on_change": function(query_report) {
				var to_date = frappe.query_report_filters_by_name.to_date.get_value()
				var from_date = frappe.query_report_filters_by_name.from_date.get_value()
				if (frappe.datetime.str_to_obj(to_date) < frappe.datetime.str_to_obj(from_date)){
					frappe.throw("To date cannot be less than from date")
				}
				query_report.trigger_refresh();
			}
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"on_change": function(query_report) {
				var to_date = frappe.query_report_filters_by_name.to_date.get_value()
				var from_date = frappe.query_report_filters_by_name.from_date.get_value()
				if (frappe.datetime.str_to_obj(to_date) < frappe.datetime.str_to_obj(from_date)){
					frappe.throw("To date cannot be less than from date")
				}
				query_report.trigger_refresh();
			}
		},
		{
			"fieldname":"vlcc",
			"label": __("VLCC"),
			"fieldtype": "Link",
			"options":"Company",
			"read_only": 1
		}
	],
	onload: function(query_report) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "User",
				filters: {"name": frappe.session.user},
				fieldname: ["operator_type","company", "branch_office"]
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