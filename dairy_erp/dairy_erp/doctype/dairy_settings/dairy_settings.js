// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dairy Settings', {
	refresh: function(frm) {

	},
	hours: function(frm) {
		if (frm.doc.hours > 48) {
			frappe.msgprint("Hours can not be more than 48")
			frm.reload_doc();
		}
	}
});
