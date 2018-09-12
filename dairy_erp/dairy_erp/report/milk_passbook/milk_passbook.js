// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Milk Passbook"] = {
	"filters": [
		{
			"fieldname":"farmer_id",
			"label": __("Farmer ID"),
			"fieldtype": "Link",
			"options": "Farmer",
			"on_change": function(query_report) {
				var farmer_id = frappe.query_report_filters_by_name.farmer_id.get_value()
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Farmer",
						filters: {"name": farmer_id},
						fieldname: ["full_name"]
					},
					callback: function(r) {
						console.log("insidr e",r.message)
						if(!r.exc && r.message){
							frappe.query_report_filters_by_name.farmer_name.set_input(r.message.full_name);
							query_report.trigger_refresh();
						}
					}
				})
			}
			/*"get_query": function (query_report) {
				return {
					query:"dairy_erp.dairy_erp.report.milk_passbook.milk_passbook.trim_farmer_id_and_name"
				}
			}*/
		},
		{
			"fieldname":"shift",
			"label": __("Shift"),
			"fieldtype": "Select",
			"options": ['MORNING','EVENING'],
			"default": " "
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd":1,
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
			"reqd":1,
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
			"fieldname":"vlcc_addr",
			"label": __("VLCC Address"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"farmer_name",
			"label": __("Farmer Name"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"vlcc",
			"label": __("VLCC"),
			"fieldtype": "Link",
			"options":"Company",
			"hidden": 1,
			"default":frappe.boot.user.first_name
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
						frappe.query_report_filters_by_name.vlcc_addr.set_input(r.message.address_display);
					}
					query_report.trigger_refresh();
				}
			}
		})
	}
}