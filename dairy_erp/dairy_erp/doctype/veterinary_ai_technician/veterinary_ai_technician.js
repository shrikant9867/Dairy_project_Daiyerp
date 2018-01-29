// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Veterinary AI Technician', {
	refresh: function(frm) {

	},
	address: function(frm) {
		erpnext.utils.get_address_display(frm, "address", "address_details");
	},
	onload: function(frm) {
		var user_company = get_session_user_company()
		frm.set_query("vlcc", function () {
			return {
				"filters": {
					"name": user_company,
				}
			};
		});

		frm.set_query("address", function () {
			return {
				"filters": {
					"address_type": "Veterinary AI Tech"
				}
			};
		});
	}
});

get_session_user_company = function() {
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

// cur_frm.fields_dict.address.get_query = function(doc) {
// 	return {filters: { vlcc_name: doc.company}}

