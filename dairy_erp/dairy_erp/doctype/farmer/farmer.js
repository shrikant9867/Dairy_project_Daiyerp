// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer', {
	refresh: function(frm) {
		frm.trigger("make_read_only");
	},

	validate: function(frm) {
		if(frm.doc.__islocal){
			return new Promise(function(resolve, reject) {
				frappe.confirm("Are you sure, you want to save farmer details ?" ,function() {
					var negative = 'frappe.validated = false';
					frm.set_value('registration_date',frappe.datetime.now_datetime())
					resolve(negative);
				},
				function() {
					reject();
				})
			})
		}
		else if(frm.doc.modified) {
			frm.set_value("update_date",frappe.datetime.now_datetime())
		}
	},
	onload: function(frm) {
		var user_company = get_session_user_type()
		if(!frm.doc.vlcc_name) {
			frm.set_value("vlcc_name",user_company)
		}
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

		frm.trigger("make_read_only")
	},

	percent_effective_credit: function(frm) {
		if(frm.doc.percent_effective_credit < 0 || frm.doc.percent_effective_credit > 99) {
			frm.set_value("percent_effective_credit", 0)
			refresh_field("percent_effective_credit")
			frappe.msgprint(__("Percent Of Effective Credit must be between 0 to 99"))
		}
	},

	make_read_only: function(frm) {
		frm.toggle_enable("full_name", frm.doc.__islocal ? 1:0);
		frm.toggle_enable("vlcc_name", frm.doc.__islocal ? 1:0);
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