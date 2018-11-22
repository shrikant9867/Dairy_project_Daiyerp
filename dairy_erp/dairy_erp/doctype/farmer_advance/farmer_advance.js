// Copyright (c) 2018, Stellapps Technologies Private Ltd.
// For license information, please see license.txt

frappe.ui.form.on('Farmer Advance', {
	refresh: function(frm) {
		frm.set_df_property("no_of_instalment", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("advance_amount", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("extension", "hidden", 1);
		if(cint(frm.doc.no_of_instalment)+cint(frm.doc.extension) - cint(frm.doc.paid_instalment) == 1){
			console.log(frm.doc.no_of_instalments,frm.doc.extension,frm.doc.paid_instalment,cint(frm.doc.no_of_instalments)+cint(frm.doc.extension) - cint(frm.doc.paid_instalment))
			frm.set_df_property("extension", "hidden", 0);
		}
	},
	emi_deduction_start_cycle: function(frm) {
		if(cint(frm.doc.emi_deduction_start_cycle) > 6) {
			frm.set_value("emi_deduction_start_cycle",0)
			frappe.throw("Emi deduction start cycle must be less than or equal to <b>6</b>")
		}
		else if (cint(frm.doc.emi_deduction_start_cycle) < 0){
			var emi_deduction_start_cycle = frm.doc.emi_deduction_start_cycle
			frm.set_value("emi_deduction_start_cycle",0)
			frappe.throw("Emi deduction start cycle can not be <b>"+emi_deduction_start_cycle+"</b>")
		}
	},
	onload: function(frm) {
		if(!frm.doc.vlcc){
			get_vlcc(frm)
		}
	},
	no_of_instalment: function(frm) {
		if(frm.doc.no_of_instalment <= 0){
			frm.set_value("no_of_instalment",1)
			frappe.msgprint("No Of Instalment should be greater than zero")
		}
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
		if (frm.doc.advance_amount && frm.doc.advance_amount < 0) {
			frm.set_value("advance_amount","")
			frappe.throw(__("Advance Amount cannot be negative"))
		}else if(frm.doc.advance_amount === 0) {
			frm.set_value("advance_amount","")
			frappe.throw(__("Advance Amount cannot be zero"))
		}
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
						"no_of_instalments": frm.doc.no_of_instalment,
						"extension": frm.doc.extension,
						"paid_instalment": frm.doc.paid_instalment
						},
				callback : function(r){			
					frm.set_value('emi_amount',r.message)
					frm.refresh_field('emi_amount')
				}
			})
		}
	},
	extension: function(frm) {
		frm.events.calculate_updated_ami(frm)
	},
	advance_type: function(frm){
		if(frm.doc.advance_type == "Feed And Fodder Advance"){
			frm.set_value("advance_type","")
			frappe.throw("Please create Advance Feed and Fodder at Sales Invoice")
		}
	}
});

get_vlcc =  function(frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "User",
				filters: {"name": frappe.session.user},
				fieldname: ["company"]
			},
			callback: function(r){
				frm.set_value("vlcc",r.message.company)
			}
		})
}