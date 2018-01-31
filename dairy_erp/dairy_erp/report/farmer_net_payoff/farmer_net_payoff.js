// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Farmer Net Payoff"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company"
		},
		{
			"fieldname":"farmer",
			"label": __("Farmer"),
			"fieldtype": "Link",
			"options": "Farmer",
			"get_query": function (query_report) {
				return {
					query:"dairy_erp.dairy_erp.report.farmer_net_payoff.farmer_net_payoff.get_farmers"
					
				}
			}
		},
		{
			"fieldname":"report_date",
			"label": __("As on Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"ageing_based_on",
			"label": __("Ageing Based On"),
			"fieldtype": "Select",
			"options": 'Posting Date\nDue Date',
			"default": "Posting Date"
		}
	],
	/*onload: (report) => {
	frappe.call({
		method: "dairy_erp.dairy_erp.report.farmer_net_payoff.farmer_net_payoff.get_user_company",
		callback: function(r) {
			console.log("r", r.message)
			if(r.message) {
				$("[data-fieldname=company]").val(r.message[0][0]);
			}
		}
	});
},*/
}
