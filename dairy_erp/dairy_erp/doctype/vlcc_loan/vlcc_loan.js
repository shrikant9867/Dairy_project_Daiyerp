// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vlcc Loan', {
	refresh: function(frm) {
		frm.set_df_property("no_of_instalments", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("principle", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("interest", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("extension", "hidden", 1);
		frm.events.get_vpcr_flag(frm)
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
	principle: function(frm) {
		frm.events.no_of_instalments(frm)
		frm.events.calculate_total(frm)
		frm.events.calculate_updated_emi(frm)
		if (frm.doc.principle && frm.doc.principle < 0) {
			frm.set_value("principle","")
			frappe.throw(__("Amount cannot be negative"))
		} else if(frm.doc.principle === 0) {
			frm.set_value("principle","")
			frappe.throw(__("Amount cannot be zero"))
		}
	},
	interest: function(frm) {
		frm.events.no_of_instalments(frm)
		frm.events.calculate_total(frm)
		frm.events.calculate_updated_emi(frm)
		if (frm.doc.interest && frm.doc.interest < 0){
			frm.set_value("interest","")
			frappe.throw(__("Interest cannot be negative"))
		}
	},
	calculate_total: function(frm) {
		frm.set_value('advance_amount',flt(frm.doc.principle) + flt(frm.doc.interest))
	},
	no_of_instalments: function(frm) {
		if(frm.doc.no_of_instalments <= 0){
			frm.set_value("no_of_instalments",1)
			frappe.msgprint("No Of Instalment should be greater than zero")
		}
		emi_amount = (flt(frm.doc.principle) + flt(frm.doc.interest)) / frm.doc.no_of_instalments
		if(emi_amount > 0 && emi_amount != 'Infinity') {
			frm.set_value('emi_amount', emi_amount.toFixed(2))		
		}
		else{
			frm.set_value('emi_amount',0)
		}
		if(frm.doc.docstatus == 1) {
			frm.events.calculate_updated_emi(frm)
		}
	},
	calculate_updated_emi(frm) {
		if(frm.doc.docstatus == 1){
			frappe.call({
					method:"dairy_erp.dairy_erp.doctype.vlcc_loan.vlcc_loan.get_emi",
					args : {
							"name": frm.doc.name,
							"total": frm.doc.advance_amount,
							"no_of_instalments": frm.doc.no_of_instalments,
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
	get_vpcr_flag :function(frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Dairy Setting",
				fieldname: ["is_vpcr"]
			},
			callback: function(r){
				is_vpcr = r.message.is_vpcr
				if(cint(frm.doc.no_of_instalments)+cint(frm.doc.extension) - cint(frm.doc.paid_instalment) == 1 && is_vpcr){
					frm.set_df_property("extension", "hidden", 0);
				}
			}
		})
	},
	extension: function(frm) {
		if(frm.doc.docstatus == 1){
			frappe.call({
					method:"dairy_erp.dairy_erp.doctype.vlcc_loan.vlcc_loan.calculate_interest",
					args : {
							"name": frm.doc.name,
							"principle": frm.doc.principle,
							"no_of_instalments": frm.doc.no_of_instalments,
							"extension": frm.doc.extension,
							"paid_instalment": frm.doc.paid_instalment,
							"interest": frm.doc.interest,
							"last_extension": frm.doc.last_extension_used,
							"per_cyc_interest": frm.doc.per_cycle_interest
							},
					callback : function(r){
						frm.set_value('advance_amount',r.message.total)
						frm.set_value('emi_amount',r.message.emi)
						frm.set_value('outstanding_amount',r.message.outstanding)
						frm.set_value('extension_interest',r.message.extension_interest)
					}
				})
			frm.refresh_fields();
		}
	}
});

