// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vlcc Advance', {
	refresh: function(frm) {
		frm.set_df_property("no_of_instalment", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("advance_amount", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("extension", "hidden", 1);
		frm.events.get_vpcr_flag(frm)
	},
	emi_deduction_start_cycle: function(frm) {
		if(cint(frm.doc.emi_deduction_start_cycle) > 6) {
			frm.set_value("emi_deduction_start_cycle",0)
			frappe.throw("Emi deduction start cycle must be less than 6")
		}
	},
	no_of_instalment: function(frm) {
		emi_amount = frm.doc.advance_amount / frm.doc.no_of_instalment
		if(emi_amount > 0 && emi_amount != 'Infinity') {
			frm.set_value('emi_amount', emi_amount.toFixed(2))		
		}
		else{
			frm.set_value('emi_amount',0)
			frm.events.calculate_updated_ami(frm)
		}
	},
	advance_amount: function(frm) {
		frm.events.no_of_instalment(frm)
		frm.events.calculate_updated_ami(frm)
	},
	calculate_updated_ami(frm) {
		if(frm.doc.docstatus == 1){
		frappe.call({
				method:"dairy_erp.dairy_erp.doctype.vlcc_advance.vlcc_advance.get_emi",
				args : {
						"name": frm.doc.name,
						"total": frm.doc.advance_amount,
						"no_of_instalments": frm.doc.no_of_instalment,
						"extension": frm.doc.extension,
						"paid_instalment": frm.doc.paid_instalment
						},
				callback : function(r){			
					frm.set_value('emi_amount',r.message)
					frm.refresh_field('emi_amount')
				}
			})
		}
	},
	extension: function(frm) {
		frm.events.calculate_updated_ami(frm)
	},
	get_vpcr_flag :function(frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Dairy Setting",
				fieldname: ["is_vpcr"]
			},
			callback: function(r){
				is_vpcr = r.message.is_vpcr
				if(cint(frm.doc.no_of_instalment) + cint(frm.doc.extension) - cint(frm.doc.paid_instalment) == 1 && is_vpcr){
					frm.set_df_property("extension", "hidden", 0);
				}
			}
		})
	}
});
