// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier Item Price', {
	refresh: function(frm) {

	},
	party_type: function(frm) {
		if(cur_frm.doc.party_type == "Vlcc"){
			frm.set_value("selling",1)
			frm.set_value("buying",0)
		}
		if(cur_frm.doc.party_type == "Local Supplier"){
			frm.set_value("buying",1)
			frm.set_value("selling",0)
		}
	},
	party_type_vlcc: function(frm){
		if(frm.doc.party_type_vlcc == "Local Supplier"){
			frm.set_value("buying",1)
		}
	}
});
