// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Milk Collection Record', {
	setup: function(frm) {
		frm.add_fetch("farmerid", "full_name", "farmer")
	},

	onload: function(frm) {
		// set user's company as associated vlcc
		if(frm.doc.__islocal) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "User",
					filters: {"name": frappe.session.user},
					fieldname: ["company"]
				},
				async:false,
				callback: function(r){
					if(r.message){
						frm.set_value("associated_vlcc", r.message.company)
						frm.events.get_societyid(frm,r.message.company)
					}
				}
			});
		}
	},

	get_societyid: function(frm,company){
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Village Level Collection Centre",
					filters: {"name": company},
					fieldname: ["amcu_id"]
				},
				callback: function(r){
					if(r.message){
						frm.set_value("societyid", r.message.amcu_id)
					}
				}
			});
	},

	milkquantity: function(frm) {
		if(frm.doc.milkquantity > 0){
			frm.trigger("calculate_amount");
		}
		else{
			frm.set_value("milkquantity",1)
			frappe.throw("Milk Quantity Can not be less or equal to zero")	
		}
	},

	rate: function(frm) {
		if(frm.doc.rate > 0){
			frm.trigger("calculate_amount");
		}
		else{
			frm.set_value("rate",1)
			frappe.throw("Rate Can not be less or equal to zero")	
		}
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
