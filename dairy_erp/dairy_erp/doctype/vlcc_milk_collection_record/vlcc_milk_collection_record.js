// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vlcc Milk Collection Record', {
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

	collectionroute:function(frm){
		var route = String(frm.doc.collectionroute)
		if(route.length < 3 && frm.doc.collectionroute){
			frm.set_value("collectionroute","")
			frappe.throw("Collection Route contain atleast 3 Charaters")
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
	},
	onload: function(frm) {
		if (has_common(frappe.user_roles, ["Chilling Center Manager", "Chilling Center Operator"])){		
			frappe.db.get_value("User",frappe.session.user,"branch_office", function(v){
				frappe.db.get_value("Address",v['branch_office'],"centre_id", function(c){
					frm.set_value("societyid", c['centre_id'])	
				})
			})
		}
	}
});
