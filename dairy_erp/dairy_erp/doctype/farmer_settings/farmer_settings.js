// Copyright (c) 2018, Stellapps Technologies Private Ltd.
// For license information, please see license.txt

frappe.ui.form.on('Farmer Settings', {
	onload: function(frm) {
		if(!frm.doc.vlcc) {
			frm.events.set_vlcc(frm)
		}
		frm.events.set_global_setting(frm)
	},
	refresh: function(frm) {
		if (in_list(frappe.user_roles,"Vlcc Manager")) {
			frm.set_df_property("farmer_incentives", "read_only", 1);
			frm.set_df_property("enable_per_litre", 'hidden', 1)
			frm.set_df_property("per_litre", "read_only", 1);
		}
		else if(in_list(frappe.user_roles,"Dairy Manager")) {
			frm.set_df_property("enable_local_setting", 'hidden', 1)
			frm.set_df_property("enable_local_setting", 'hidden', 1)
			frm.set_df_property("is_fpcr", 'hidden', 1)
			frm.set_df_property("enable_local_per_litre", "hidden", 1)
			frm.events.check_setting_exist(frm)
		}
	},
	check_setting_exist: function(frm) {
		if(frm.doc.__islocal){	
			frappe.call({	
				method:"dairy_erp.dairy_erp.doctype.farmer_settings.farmer_settings.check_record_exist",	
				callback:function(r){
					if(r.message){
						frappe.msgprint("Please add in existing settings")
						frappe.set_route("List","Farmer Settings")
					}
				}
			})
		}
	},
	set_vlcc: function(frm) {
		if (has_common(frappe.user_roles, ["Vlcc Manager"])){
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "User",
					filters: {"name": frappe.session.user},
					fieldname: ["company"]
				},
				callback: function(r){
					frm.set_value("vlcc",r.message.company)
				}
			})
		}
	},
	set_global_setting: function(frm) {
		if (has_common(frappe.user_roles, ["Vlcc Manager"])){
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Farmer Settings",
					filters: {"is_global": 1},
					fieldname: ["farmer_incentives","enable_per_litre","per_litre"]
				},
				callback: function(r){
					if(r.message){
						if(r.message.farmer_incentives &&  !frm.doc.farmer_incentives) {
							frm.set_value("farmer_incentives", r.message.farmer_incentives)
						}
						if(r.message.enable_per_litre) {
							frm.set_value("enable_per_litre", r.message.enable_per_litre)
						}
						if(r.message.per_litre) {
							frm.set_value("per_litre", r.message.per_litre)
						}
					}
				}
			})
		}
	}
});
