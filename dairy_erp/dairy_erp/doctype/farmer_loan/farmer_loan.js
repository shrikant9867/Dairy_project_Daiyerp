// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Loan', {
	refresh: function(frm) {

	},
	no_of_instalments: function(frm) {
		emi_amount = (cint(frm.doc.principle) + cint(frm.doc.interest)) / frm.doc.no_of_instalments
		console.log(frm.doc.principle,frm.doc.interest,frm.doc.principle + frm.doc.interest)
		if(emi_amount > 0 && emi_amount != 'Infinity') {
			frm.set_value('emi_amount', emi_amount.toFixed(2))		
		}
		else{
			frm.set_value('emi_amount',0)
		}
	},
	principle: function(frm) {
		frm.events.no_of_instalments(frm)
	},
	interest: function(frm) {
		frm.events.no_of_instalments(frm)
	},onload: function(frm) {
		
	}
});
