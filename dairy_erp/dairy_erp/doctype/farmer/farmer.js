// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		var user_company = get_session_user_type()
		frm.set_query("vlcc_name", function () {
			return {
				"filters": {
					"name": user_company,
				}
			};
		});
	},
	address: function(frm) {
		erpnext.utils.get_address_display(frm, "address", "address_details");
	},
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