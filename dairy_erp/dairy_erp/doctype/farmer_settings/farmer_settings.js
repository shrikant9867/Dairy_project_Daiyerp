// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Settings', {
	refresh: function(frm) {
		if (in_list(frappe.user_roles,"Vlcc Manager")) {
			frm.set_df_property("farmer_incentives", "read_only", 1);
			frm.set_df_property("per_litre", "read_only", 1);
		}
		else if(in_list(frappe.user_roles,"Dairy Manager")) {
			frm.set_df_property("enable_local_setting", 'hidden', 1)
		}
	}
});
