// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Payment Cycle Report', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		if(frm.doc.__islocal){	
			frappe.call({	
				method:"dairy_erp.dairy_erp.doctype.farmer_payment_cycle_report.farmer_payment_cycle_report.get_fpcr_flag",
				callback:function(r){
					if(!r.message){
						frappe.msgprint("Please enable <b>IS FPCR</b> flag in farmer settings to generate FPCR")
						frappe.set_route("List","Farmer Payment Cycle Report")
					}
				}
			})
		}
		if(!frm.doc.date) {
			frm.set_value("date",frappe.datetime.get_today())
		}
		if(!frm.doc.vlcc_name){
			get_vlcc(frm)
		}
		if(!frm.doc.address) {
			get_address(frm)
		}
	},
	vlcc_name: function(frm) {
		frm.events.add_cycle_child(frm)		
	},
	cycle: function(frm) {
		
		if(frm.doc.cycle) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Farmer Date Computation",
					filters: {"name": frm.doc.cycle},
					fieldname: ["start_date","end_date"]
				},
				callback: function(r){
					if(r.message){	
						frm.set_value("collection_from",r.message.start_date)
						frm.set_value("collection_to",r.message.end_date)
						frm.events.add_cycle_child(frm)		
					}
				}
			});
		}
	},
	farmer_id: function(frm) {
		if(frm.doc.farmer_id){
			frm.events.add_cycle_child(frm)
			frm.events.calculate_total_ami(frm)
			frm.events.calculate_total_outstanding(frm)
			frm.events.calculate_advance_emi(frm)
			frm.events.calculate_advance_outstanding(frm)
			frm.events.calculate_net_pay(frm)
		}
	},
	add_cycle_child: function(frm) {
		if(frm.doc.collection_from && frm.doc.collection_to && frm.doc.vlcc_name && frm.doc.farmer_id) {
			frappe.call({	
				method:"dairy_erp.dairy_erp.doctype.farmer_payment_cycle_report.farmer_payment_cycle_report.get_fmcr",	
				args: {
					"start_date": frm.doc.collection_from,
					"end_date": frm.doc.collection_to,
					"vlcc": frm.doc.vlcc_name,
					"farmer_id": frm.doc.farmer_id,
					"cycle": frm.doc.cycle,
				},
				callback:function(r){
					if(r.message){
						frm.set_value("fmcr_details", "")
						frm.set_value("loan_child", "")
						frm.set_value("advance_child","")
						total = 0
						$.each(r.message.fmcr, function(i, d) {
							var row = frappe.model.add_child(cur_frm.doc, "FMCR Table", "fmcr_details");
							total += d.amount
							row.date = d.rcvdtime;
							row.shift = d.shift;
							row.litres = d.milkquantity;
							row.fat = d.fat
							row.snf = d.snf
							row.amount = d.amount
							row.rate = d.rate
						});
						$.each(r.message.child_loan, function(i, d) {
							var row = frappe.model.add_child(cur_frm.doc, "Loan Child", "loan_child");
							row.loan_id = d.name
							row.principle = d.advance_amount
							row.emi_amount = d.emi_amount
							row.outstanding = d.outstanding_amount
							row.extension = d.extension
							row.paid_instalment = d.paid_instalment
							row.no_of_instalment = d.no_of_instalments
							row.amount = d.emi_amount

						});
						$.each(r.message.child_advance, function(i, d) {
							var row = frappe.model.add_child(cur_frm.doc, "Advance Child", "advance_child");
							row.adv_id = d.name
							row.principle = d.advance_amount
							row.emi_amount = d.emi_amount
							row.outstanding = d.outstanding_amount
							row.extension = d.extension
							row.paid_instalment = d.paid_instalment
							row.no_of_instalment = d.no_of_instalment
							row.amount = d.emi_amount
						})
						frm.set_value("total_amount", total)
						frm.set_value("incentives", r.message.incentive)
						frm.set_value("total_bill",flt(frm.doc.total_amount) + flt(frm.doc.incentives))
						frm.set_value("feed_and_fodder",r.message.fodder.toFixed(2))
						frm.set_value("veterinary_services", r.message.vet.toFixed(2))
						frm.refresh_fields();
						frm.events.calculate_total_ami(frm)
						frm.events.calculate_total_outstanding(frm)
						frm.events.calculate_advance_emi(frm)
						frm.events.calculate_advance_outstanding(frm)
						frm.events.calculate_net_pay(frm)	

					}
					else{
						frm.set_value("fmcr_details","")
						frm.set_value("total_amount",0)
						frm.set_value("loan_child","")
						frm.set_value("advance_child","")
					}
				}
			})
		}
		else{
			frm.set_value("fmcr_details","")
			frm.set_value("total_amount",0)
			frm.set_value("loan_child","")
			frm.set_value("advance_child","")
			frm.set_value("incentives",0)
			frm.set_value("total_bill",0)
		}
	},
	calculate_total_ami: function(frm) {
		emi = 0
		$.each(frm.doc.loan_child, function(i, d) {
			emi += flt(d.amount)				
		});
		frm.set_value("loan_emi", emi.toFixed(2))
	},
	calculate_total_outstanding: function(frm) {
		
	},
	calculate_advance_emi: function(frm) {
		emi = 0
		$.each(frm.doc.advance_child, function(i, d) {
			emi += flt(d.amount)				
		});
		frm.set_value("advance_emi", emi.toFixed(2))
	},
	calculate_advance_outstanding: function(frm) {
	
	},
	address: function(frm) {
		erpnext.utils.get_address_display(frm, "address", "address_display");
		frm.refresh_field("address_display")
	},
	calculate_net_pay: function(frm){
		net_pay = flt(frm.doc.total_bill) - (flt(frm.doc.loan_emi) + 
		flt(frm.doc.advance_emi) + flt(frm.doc.feed_and_fodder) +
		flt(frm.doc.veterinary_services))
		frm.set_value("net_pay",net_pay)
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
				frm.set_value("vlcc_name",r.message.company)
				get_address(frm)

			}
		})
}

frappe.ui.form.on('Loan Child',  {
	pay_full_loan: function(frm) {
		var row = locals[cdt][cdn]
		frappe.call({
			method: "dairy_erp.dairy_erp.doctype.farmer_payment_cycle_report.farmer_payment_cycle_report.update_full_loan",
			args: {
				"loan": row.loan_id
			},
			callback: function(r){
				if(r.message){	
				
				}
			}
		});
	},
	amount: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn]
		if(frm.doc.cycle && row.loan_id && row.amount) {
			frappe.call({
				method: "dairy_erp.dairy_erp.doctype.farmer_payment_cycle_report.farmer_payment_cycle_report.get_updated_loan",
				args: {"cycle": frm.doc.cycle, "loan_id": row.loan_id, "amount": row.amount, "total": row.principle},
				callback: function(r) {
					if (r.message){
						frm.set_value("loan_outstanding",r.message)
					}
					else if(row.amount == row.outstanding){
						frm.set_value("loan_outstanding",0)
					}
				}
			});
		}
		frm.events.calculate_total_ami(frm)
		frm.events.calculate_net_pay(frm)	
	}

});

frappe.ui.form.on('Advance Child', 'amount', function(frm, cdt, cdn){
	var row = locals[cdt][cdn]
	if(frm.doc.cycle && row.adv_id && row.amount) {
		frappe.call({
			method: "dairy_erp.dairy_erp.doctype.farmer_payment_cycle_report.farmer_payment_cycle_report.get_updated_advance",
			args: {"cycle": frm.doc.cycle, "adv_id": row.adv_id, "amount": row.amount, "total": row.principle},
			callback: function(r) {
				console.log(r.message)
				if (r.message){
					frm.set_value("advance_outstanding",r.message)
				}
				else if(row.amount == row.outstanding){
					frm.set_value("advance_outstanding",0)
				}
			}
		});
	}
	frm.events.calculate_advance_emi(frm)
	frm.events.calculate_net_pay(frm)
})

get_address =  function(frm) {
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "Village Level Collection Centre",
			filters: {"name": frm.doc.vlcc_name},
			fieldname: "address"
		},
		callback: function(r){
			if(r.message){
				frm.set_value("address",r.message.address)
			}
		}
	})
}

cur_frm.fields_dict['cycle'].get_query = function(doc) {
	return {
		"query": "dairy_erp.dairy_erp.doctype.farmer_payment_cycle_report.farmer_payment_cycle_report.get_cycle",
		filters: {'vlcc': doc.vlcc_name}
	}
}