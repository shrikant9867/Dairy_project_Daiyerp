// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Local Sales Report"] = {
	"filters": [
		{
			"fieldname":"customer_type",
			"label": __("VLCC Local Customer/Farmer"),
			"fieldtype": "Select",
			"options": 'Vlcc Local Customer\nFarmer\nVlcc Local Institution',
			"default": "Vlcc Local Customer",
			"on_change": function(query_report) {
				var customer = frappe.query_report_filters_by_name.customer.get_value()
				if (customer){
					frappe.query_report_filters_by_name.customer.set_input("");
				}
				query_report.trigger_refresh();
			}
		},
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options":"Customer",
			"get_query": function (query_report) {
				return{
					query:"dairy_erp.dairy_erp.report.local_sales_report.local_sales_report.get_customer",
					"filters": {
						"customer_type": frappe.query_report_filters_by_name.customer_type.get_value()
						}
					}
				},
			"on_change": function(query_report) {
				var customer_type = frappe.query_report_filters_by_name.customer_type.get_value()
				console.log("insdie on_change")
				if(customer_type == "Farmer"){
					console.log("insdie farmer cond")
					frappe.call({
						method: "frappe.client.get_value",
						args: {
							doctype: "Farmer",
							filters: {"full_name": frappe.query_report_filters_by_name.customer.get_value()},
							fieldname: ["name"]
						},
						callback: function(r) {
							console.log("insidr e",r.message)
							if(!r.exc && r.message && !in_list(["Administrator", "Guest"], frappe.session.user)){
								if(has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager"])){
									// $('body').find("[data-fieldname=vlcc]").val(r.message.company)
									frappe.query_report_filters_by_name.farmer_id.set_input(r.message.name);
								}
								query_report.trigger_refresh();
							}
						}
					})
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
		},
		{
			"fieldname":"vlcc_addr",
			"label": __("VLCC Address"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"farmer_id",
			"label": __("Farmer Id"),
			"fieldtype": "Data",
			"hidden": 1
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
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Village Level Collection Centre",
				filters: {"name": frappe.boot.user.first_name},
				fieldname: ["address_display"]
			},
			callback: function(r) {
				console.log("insidr e",r.message)
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