// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Advance', {
	refresh: function(frm) {

	},
	no_of_instalment: function(frm) {
		emi_amount = frm.doc.advance_amount / frm.doc.no_of_instalment
		if(emi_amount > 0 && emi_amount != 'Infinity') {
			frm.set_value('emi_amount', emi_amount.toFixed(2))		
		}
		else{
			frm.set_value('emi_amount',0)
		}
	},
	advance_amount: function(frm) {
		frm.events.no_of_instalment(frm)
	}
});
