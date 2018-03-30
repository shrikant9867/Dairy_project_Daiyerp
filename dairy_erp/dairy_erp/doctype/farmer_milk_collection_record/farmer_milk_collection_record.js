// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Milk Collection Record', {
	setup: function(frm) {
		frm.add_fetch("farmerid", "full_name", "farmer")
	},

	milkquantity: function(frm) {
		frm.trigger("calculate_amount");
	},

	rate: function(frm) {
		frm.trigger("calculate_amount");
	},

	validate: function(frm) {
		frm.trigger("calculate_amount");
	},

	calculate_amount: function(frm) {
		if(frm.doc.milkquantity && frm.doc.rate) {
			frm.set_value("amount", flt(frm.doc.rate * frm.doc.milkquantity))
		}
		else {
			frm.set_value("amount", 0)
		}
	}
});
