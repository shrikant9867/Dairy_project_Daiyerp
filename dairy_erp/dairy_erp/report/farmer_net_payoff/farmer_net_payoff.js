// Copyright (c) 2018, Stellapps Technologies Private Ltd.
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Farmer Net Payoff"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"get_query": function (query_report) {
				return {
					query:"dairy_erp.dairy_erp.report.farmer_net_payoff.farmer_net_payoff.get_filtered_company"
					
				}
			}
		},
		{
			"fieldname":"farmer",
			"label": __("Farmer"),
			"fieldtype": "Link",
			"options": "Farmer"
			/*"get_query": function (query_report) {
				return {
					query:"dairy_erp.dairy_erp.report.farmer_net_payoff.farmer_net_payoff.get_filtered_farmers"
					
				}
			}*/
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
	]
}

