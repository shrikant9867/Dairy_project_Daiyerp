// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		var user_company = get_session_user_type()
		frm.set_value("vlcc_name",user_company)
		frm.set_query("vlcc_name", function () {
			return {
				"filters": {
					"name": user_company,
				}
			};
		});
		frm.set_query("address", function () {
			return {
				"filters": {
					"address_type": "Farmer",
				}
			};
		});
	},
	/*onload: function(frm) {
		var user_company = get_session_user_type()
		frm.set_query("address", function () {
			return {
				"filters": {
					"address_type": "Farmer",
				}
			};
		});
	},*/
	address: function(frm) {
		erpnext.utils.get_address_display(frm, "address", "address_details");
	},
	percent_effective_credit: function(frm) {
		if(frm.doc.percent_effective_credit < 0 || frm.doc.percent_effective_credit > 99) {
			frm.set_value("percent_effective_credit", 0)
			refresh_field("percent_effective_credit")
			frappe.msgprint(__("Percent Of Effective Credit must be between 0 to 99"))
		}
	}
});


get_session_user_type = function() {
	var user;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "User",
			filters: {"name": frappe.session.user},
			fieldname: "company"
		},
		async:false,
		callback: function(r){
			if(r.message){
			user = r.message.company			
			}
		}
	});

	return user
}