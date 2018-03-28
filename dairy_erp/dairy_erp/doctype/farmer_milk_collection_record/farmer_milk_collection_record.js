// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Milk Collection Record', {
	setup: function(frm) {
		frm.add_fetch("farmerid", "full_name", "farmer")
	}
});
