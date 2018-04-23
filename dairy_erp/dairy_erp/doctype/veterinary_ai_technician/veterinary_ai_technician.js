// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Veterinary AI Technician', {
	refresh: function(frm) {
		frm.set_df_property("column_break_3","hidden", frm.doc.__islocal ? 1:0)
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
					"vet": frm.doc.name
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

