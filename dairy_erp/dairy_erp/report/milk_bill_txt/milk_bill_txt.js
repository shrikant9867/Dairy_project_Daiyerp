// Copyright (c) 2018, Stellapps Technologies Private Ltd.
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Milk Bill txt"] = {
	"filters": [
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
		},
		{
			"fieldname":"download",
			"label": __("Download"),
			"fieldtype": "Button",
			click: () => {
				console.log("button")
				frappe.call({
					method: "dairy_erp.dairy_erp.report.milk_bill_txt.milk_bill_txt.add_txt_in_file",
					args: {
						filters : {
							start_date: frappe.query_report_filters_by_name.start_date.get_value(),
							end_date: frappe.query_report_filters_by_name.end_date.get_value()
						}
					},
					callback: function(r) {
						console.log("insdie",r.message)
						if (r.message && r.message.file_name && r.message.file_url) {
							file_url = r.message.file_url.replace(/#/g, '%23');
							window.open(file_url);
						}
					}
				})
			}
		}
	]
}

/*on_click_of_download = function(){
	console.log("insdie download")
}*/