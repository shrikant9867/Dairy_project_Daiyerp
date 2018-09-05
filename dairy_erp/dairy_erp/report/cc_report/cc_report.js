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
		},
		{
			"fieldname":"address",
			"label": __("Address"),
			"fieldtype": "Data",
			"hidden": 1
		}
	],
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
					frappe.query_report_filters_by_name.address.set_input(r.message.address);
					frappe.query_report_filters_by_name.vlcc_id.set_input(r.message.vlcc_id);
                }
                query_report.trigger_refresh();
            }
        })
		/*frappe.call({
			method: "frappe.client.get_value",
			async : false,
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
		var branch_office = frappe.query_report_filters_by_name.branch_office.get_value();
		console.log(branch_office,"branch_office")
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Address",
				filters: {"name": branch_office},
				fieldname: ["address_line1","address_line1","city","country","state","pincode"]
			},
			callback: function(r) {
				console.log("inside console address",r.message)
				if(!r.exc && r.message && !in_list(["Administrator", "Guest"], frappe.session.user)){
					var address = ""
					address += r.message.address_line1 ? r.message.address_line1:""
					address += r.message.address_line2 ? r.message.address_line2:""
					address += r.message.city ? r.message.city:""
					address += r.message.country ? r.message.country:""
					address += r.message.state ? r.message.state:""
					address += r.message.pincode ? r.message.pincode:""
					console.log(address,"address___________________")
					//query_report.trigger_refresh();
				}
			}
		})*/
	}
}
