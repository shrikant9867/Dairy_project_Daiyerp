// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Advance', {
	refresh: function(frm) {
		frm.set_df_property("no_of_instalment", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("advance_amount", "read_only", frm.doc.__islocal ? 0:1);
	},
	no_of_instalment: function(frm) {
		emi_amount = frm.doc.advance_amount / frm.doc.no_of_instalment
		if(emi_amount > 0 && emi_amount != 'Infinity') {
			frm.set_value('emi_amount', emi_amount.toFixed(2))		
		}
		else{
			frm.set_value('emi_amount',0)
		}
		frm.events.calculate_updated_ami(frm)
	},
	advance_amount: function(frm) {
		frm.events.no_of_instalment(frm)
		frm.events.calculate_updated_ami(frm)
	},
	calculate_updated_ami(frm) {
		if(frm.doc.docstatus == 1){
		frappe.call({
				method:"dairy_erp.dairy_erp.doctype.farmer_advance.farmer_advance.get_emi",
				args : {
						"name": frm.doc.name,
						"total": frm.doc.advance_amount,
						"no_of_instalments": frm.doc.no_of_instalment
						},
				callback : function(r){			
					frm.set_value('emi_amount',r.message)
					frm.refresh_field('emi_amount')
				}
			})
		}
	}
});
