// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Village Level Collection Centre', {
	refresh: function(frm) {
		if(!frm.doc.__islocal){
			frm.add_custom_button(__("Dairy Dashboard"), function() {
				frappe.set_route("dairy-dashboard");
			})
		}
		frm.set_df_property("email_id", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("abbr", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("name1", "read_only", frm.doc.__islocal ? 0:1);
	},
	onload: function(frm) {
		frm.set_query("chilling_centre", function () {
			return {
				"filters": {
					"address_type": "Chilling Centre",
				}
			};
		});
		frm.set_query("plant_office", function () {
			return {
				"filters": {
					"address_type": "Plant",
				}
			};
		});
		frm.set_query("camp_office", function () {
			return {
				"filters": {
					"address_type": "Camp Office",
				}
			};
		});
		frm.set_query("address", function () {
			return {
				"filters": {
					"address_type" :  ["not in",["Camp Office", "Chilling Centre", "Head Office", "Plant"]]
				}
			};
		});
	},
	address: function(frm) {
		erpnext.utils.get_address_display(frm, "address", "address_display");
	},
	vlcc_name: function(frm) {
		if(frm.doc.__islocal) {
			let parts = frm.doc.vlcc_name.split();
			let abbr = $.map(parts, function (p) {
				return p? p.substr(0, 1) : null;
			}).join("");
			frm.set_value("abbr", abbr);
		}
	}
});