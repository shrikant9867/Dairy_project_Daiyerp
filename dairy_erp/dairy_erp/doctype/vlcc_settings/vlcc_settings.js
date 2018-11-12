// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('VLCC Settings', {
	refresh: function(frm) {
		frm.events.set_vlcc(frm)
		frm.events.set_vlcc_setting(frm)
		frm.events.set_farmer_id(frm)
		if(frm.doc.flag_negative_effective_credit){
			frm.set_df_property("allow_negative_effective_credit","read_only",1)
		}
		// frm.set_df_property("farmer_id1", "read_only", frm.doc.__islocal ? 0:1);
		// frm.set_df_property("farmer_id2", "read_only", frm.doc.__islocal ? 0:1);
	},
	onload_post_render: function(frm){
		frm.get_field("delete_fmcr_transactions").$input.addClass("btn-danger");
	},
	enable: function(frm) {
		frappe.call({
			method: "dairy_erp.dairy_erp.doctype.vlcc_settings.vlcc_settings.get_ag_rupay_url",
			callback: function(r){
					console.log(r.message)
				if(r.message){
					frm.set_value("url",r.message)
				}
			}
		});
	},
	delete_fmcr_transactions: function(frm) {
		if(frm.doc.upload_file){
		return new Promise(function(resolve, reject) {
			frappe.confirm("Are you sure, you want to delete FMCR Records?" ,function() {
				var negative = 'frappe.validated = false';
				frm.events.get_csv(frm)
				resolve(negative);
			},
				function() {
					reject();
				})
			})
		}else{
			frappe.throw("Please upload file first")
		}
	},
	hours: function(frm) {
		if (frm.doc.hours > 48) {
			frappe.msgprint("Hours can not be more than 48")
			frm.set_value("hours",24)
			frm.reload_doc();
		}
		else if(frm.doc.hours < 0) {
			frappe.msgprint("Hours can not negative")
			frm.set_value("hours",24)
			frm.reload_doc();
		} else if(frm.doc.cycle_hours && frm.doc.hours > frm.doc.cycle_hours){
			frappe.msgprint("FMCR Edition Hours must be less than Farmer Payment Settlement Hours")
		}
	},
	cycle_hours: function(frm) {
		frm.events.validate_cycle_hours(frm)	
	},
	months_to_member: function(frm){
		if(frm.doc.months_to_member >999) {
			frappe.msgprint("Months can not be greater than 999")
			frm.set_value("months_to_member",0)
			frm.reload_doc();
		}
	},
	validate: function(frm) {
		frm.events.validate_cycle_hours(frm)
		frm.events.validate_item_table(frm)
		// SG-16-10
		if(frm.doc.no_of_cycles <= 0 || frm.doc.no_of_interval <= 0) {
			frappe.throw("Number of Cycles/Number of days in a Payment Cycle must be between <b>1-31</b>")
		}
		// SG-17-10
		if(frm.doc.no_of_cycles * frm.doc.no_of_interval > 31) {
			frappe.throw("Combination of <b>Number of Cycles & Number of days in a Payment Cycle</b> is incorrect")
		}
	},
	validate_item_table:function(frm){
		var c_type_wise_item = {}
		if(frm.doc.vlcc_item.length > 0){
			$.each(frm.doc.vlcc_item,function(i,d){
				if(d.customer_type){
					c_type_wise_item[d.customer_type] = d.item
				}
			})
		}
		if(!in_list(Object.keys(c_type_wise_item),'Farmer')) {
			frappe.throw(__("Please Add Item For Farmer"))
		}
		else if(!in_list(Object.keys(c_type_wise_item),'Vlcc Local Customer')) {
			frappe.throw(__("Please Add Item For Vlcc Local Customer"))
		}
	},
	get_csv: function(frm) {
		frappe.call({
				method:"dairy_erp.dairy_erp.doctype.vlcc_settings.vlcc_settings.get_csv",
				args: {"doc":frm.doc},
				callback: function(r){
					if(r.message) {

					}
				}
			})
	},
	set_vlcc: function(frm){
		frappe.call({
				method: "frappe.client.get_value",
				async : false,
				args: {
					doctype: "User",
					filters: {"name": frappe.session.user},
					fieldname: ["company"]
				},
				callback: function(r){
					if(r.message){
						if(!frm.doc.vlcc){
							frm.set_value("vlcc",r.message.company)
						}
						frm.events.check_record_exist(frm)
					}
				}
			});
	},
	set_farmer_id: function(frm) {
		console.log("setting Farmer ids >>>>")
		frappe.call({
				method: "frappe.client.get_value",
				async : false,
				args: {
					doctype: "Village Level Collection Centre",
					filters: {"name": frm.doc.vlcc},
					fieldname: ["longformatfarmerid"]
				},
				callback: function(r){
					if(r.message){
						if(frm.doc.vlcc){
							frm.set_value("farmer_id1",r.message.longformatfarmerid+"_9994")
							frm.set_value("farmer_id2",r.message.longformatfarmerid+"_0999")
						}
						else{
							frm.set_value("farmer_id1","0999")
							frm.set_value("farmer_id2","9994")
						}
					}
				}
			});
	},
	set_vlcc_setting: function(frm){
		console.log("inside my cond")
		frappe.call({
			method: "dairy_erp.dairy_erp.doctype.vlcc_settings.vlcc_settings.get_eff_credit",
			async : false,
			callback: function(r){
				if(r.message){
					if(!frm.doc.flag_negative_effective_credit){
						frm.set_value("allow_negative_effective_credit",r.message)
						frm.set_df_property("allow_negative_effective_credit","read_only",1)
					}
				}
				else{
					if(!frm.doc.flag_negative_effective_credit){
						frm.set_value("allow_negative_effective_credit",0)
						frm.set_df_property("allow_negative_effective_credit","read_only",1)						
					}
				}	
			}
		});
	},
	check_record_exist: function(frm){
		if(frm.doc.__islocal){	
			frappe.call({	
				method:"dairy_erp.dairy_erp.doctype.vlcc_settings.vlcc_settings.check_record_exist",	
				callback:function(r){
					if(r.message){
						frappe.msgprint("Please add configurations in the existing settings")
						frappe.set_route("List","VLCC Settings")
					}
				}
			})
		}
	},
	validate_cycle_hours: function(frm) {
		if(frm.doc.cycle_hours % 24 != 0){
			frappe.msgprint("Please add Hours in multiples of 24")
			frm.set_value("cycle_hours",24)
			frm.reload_doc();
		} else if(frm.doc.cycle_hours == 0){
			frappe.msgprint("Hours can not be zero")
			frm.set_value("cycle_hours",24)
			frm.reload_doc();
		} else if(frm.doc.hours && (frm.doc.cycle_hours < frm.doc.hours)){
			frappe.msgprint("Configurable Hours for Farmer Payment Settlement must be greater than FMCR Edition Hours")
			frm.set_value("cycle_hours",24)
			frm.reload_doc();
		}
	},
	enable_negative_effective_credit: function(frm){
		frm.set_value("allow_negative_effective_credit",1)
		frm.set_value("flag_negative_effective_credit",1)
		frm.set_df_property("allow_negative_effective_credit","read_only",1)
	},
	disable_negative_effective_credit: function(frm){
		frm.set_value("allow_negative_effective_credit",0)
		frm.set_value("flag_negative_effective_credit",1)
		frm.set_df_property("allow_negative_effective_credit","read_only",1)
	},
		// SG-16-10
	no_of_cycles: function(frm) {
		if(frm.doc.no_of_cycles > 31){
			frm.set_value("no_of_cycles",1)
			frappe.throw("Number of Cycles must be between <b>1-31</b>")
		}
		else if(frm.doc.no_of_cycles <= 0){
			frm.set_value("no_of_cycles",1)
			frappe.throw("Number of Cycles can not be less than <b>1</b>")
		}
	},
		// SG-16-10
	no_of_interval: function(frm) {
		if(frm.doc.no_of_interval > 31){
			frm.set_value("no_of_interval",1)
			frappe.throw("Number of days in a Payment Cycle must be between <b>1-31</b>")
		}
		else if(frm.doc.no_of_interval <= 0){
			frm.set_value("no_of_interval",1)
			frappe.throw("Number of days in a Payment Cycle can not be less than <b>1</b>")
		}
	}

});


cur_frm.fields_dict['vlcc_item'].grid.get_field("item").get_query = function(doc, cdt, cdn) {
		var child = locals[cdt][cdn];
		return {
			query:"dairy_erp.dairy_erp.doctype.vlcc_settings.vlcc_settings.get_item_by_customer_type",
			filters: {'customer_type': child.customer_type,
						'items_dict':cur_frm.doc.vlcc_item
					}
		}
}
