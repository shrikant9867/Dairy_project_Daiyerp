// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Loan', {
	refresh: function(frm) {
		frm.set_df_property("no_of_instalments", "read_only", frm.doc.__islocal ? 0:1);
	},
	onload: function(frm) {
		// frm.set_value('date_of_disbursement', frappe.datetime.get_today())
	},
	no_of_instalments: function(frm) {
		emi_amount = (cint(frm.doc.principle) + cint(frm.doc.interest)) / frm.doc.no_of_instalments
		if(emi_amount > 0 && emi_amount != 'Infinity') {
			frm.set_value('emi_amount', emi_amount.toFixed(2))		
		}
		else{
			frm.set_value('emi_amount',0)
		}
		if(frm.doc.docstatus == 1) {
			frm.events.calculate_updated_ami(frm)
		}
	},
	principle: function(frm) {
		frm.events.no_of_instalments(frm)
		frm.events.calculate_total(frm)
		frm.events.calculate_updated_ami(frm)
	},
	interest: function(frm) {
		frm.events.no_of_instalments(frm)
		frm.events.calculate_total(frm)
		frm.events.calculate_updated_ami(frm)
	},
	calculate_total: function(frm) {
		frm.set_value('advance_amount',cint(frm.doc.principle) + cint(frm.doc.interest))
	},
	calculate_updated_ami(frm) {
		if(frm.doc.docstatus == 1){
		frappe.call({
				method:"dairy_erp.dairy_erp.doctype.farmer_loan.farmer_loan.get_emi",
				args : {
						"name": frm.doc.name,
						"total": frm.doc.advance_amount,
						"no_of_instalments": frm.doc.no_of_instalments
						},
				callback : function(r){			
					frm.set_value('emi_amount',r.message)
					frm.refresh_field('emi_amount')
				}
			})
		}
	}

});
