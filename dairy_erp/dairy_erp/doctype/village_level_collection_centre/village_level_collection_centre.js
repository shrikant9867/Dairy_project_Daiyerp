// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Village Level Collection Centre', {
	refresh: function(frm) {

			if(in_list(frappe.user_roles,"Dairy Manager") || in_list(frappe.user_roles,"Dairy Operator")){
				frm.add_custom_button(__("Dairy Dashboard"), function() {
					frappe.set_route("dairy-dashboard");
				})
			}	
		frm.set_df_property("email_id", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("abbr", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("amcu_id", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("name1", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("camp_office", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("section_break_5","hidden", frm.doc.__islocal ? 1:0)

		frm.set_df_property("operator_email_id", "read_only", frm.doc.__islocal || !frm.doc.operator_email_id ? 0:1);
		frm.set_df_property("operator_name", "read_only", frm.doc.__islocal || !frm.doc.operator_name ? 0:1);
		frm.set_df_property("vlcc_type","read_only", frm.doc.__islocal ? 0:1)
		// address mandatory after save
		frm.toggle_reqd("address", frm.doc.__islocal ? 0:1)
		frm.events.set_dynamic_cc(frm)
	},
	
	onload: function(frm) {
		if(frm.doc.__islocal){
			frm.set_value("address","")
			frm.set_value("chilling_centre","")
			frm.set_value("camp_office","")
			frm.set_value("plant_office","")
		}
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
					"vlcc" : frm.doc.name  
				}
			};
		});
		frm.set_query("contact", function () {
			return {
				"filters": {
					"vlcc" : frm.doc.name
				}
			}
		});
	},
	
	address: function(frm) {
		erpnext.utils.get_address_display(frm, "address", "address_display");
	},
	vlcc_type: function(frm) {
		frm.events.set_dynamic_cc(frm)
		frm.events.bmc_set_query(frm)
	},
	vlcc_name: function(frm) {
		if(frm.doc.__islocal) {
			let parts = frm.doc.vlcc_name.split();
			let abbr = $.map(parts, function (p) {
				return p? p.substr(0, 1) : null;
			}).join("");
			frm.set_value("abbr", abbr);
		}
	},
	
	chilling_centre: function(frm) {
		frappe.route_options = {
			"address_type": "Chilling Centre"
		}
	},
	
	camp_office: function(frm) {
		frappe.route_options = {
			"address_type": "Camp Office"
		}
	},

	plant_office: function(frm) {
		frappe.route_options = {
			"address_type": "Plant"
		}
	},
	global_percent_effective_credit: function(frm) {
		if(frm.doc.global_percent_effective_credit < 0 || frm.doc.global_percent_effective_credit > 99) {
			frm.set_value("global_percent_effective_credit", 0)
			refresh_field("global_percent_effective_credit")
			frappe.msgprint(__("Global Percent Effective Credit must be between 0 to 99"))
		}
	},
	set_dynamic_cc: function(frm) {
		if(frm.doc.vlcc_type == 'Traditional'){
			frm.set_df_property("chilling_centre", "reqd", 1);
			frm.set_df_property("bmc_chilling_centre", "hidden", 1);
			frm.set_df_property("chilling_centre", "hidden", 0);
			frm.set_df_property("sec_brek_77", "hidden", 1);
		}else if(frm.doc.vlcc_type == 'Hybrid'){
			frm.set_df_property("chilling_centre", "reqd", 0);
			frm.set_df_property("bmc_chilling_centre", "read_only", 1);
			frm.set_df_property("bmc_chilling_centre", "hidden", 0);
			frm.set_df_property("chilling_centre", "hidden", 1);
			frm.set_df_property("sec_brek_77", "hidden", 1);
		}else if(frm.doc.vlcc_type == 'Clustered Society'){
			frm.set_df_property("chilling_centre", "reqd", 0);
			frm.set_df_property("bmc_chilling_centre", "read_only", 0);
			frm.set_df_property("bmc_chilling_centre", "hidden", 0);
			frm.set_df_property("bmc_chilling_centre", "reqd", 1);
			frm.set_df_property("chilling_centre", "hidden", 1);
			frm.set_df_property("sec_brek_77", "hidden", 0);
		}
	},
	bmc_set_query: function(frm) {
		if(frm.doc.vlcc_type == 'Clustered Society'){
			frm.set_query("bmc_chilling_centre", function () {
				return {
					"filters": {
						"vlcc_type" : "Hybrid"
					}
				}
			});
		}
	}
});