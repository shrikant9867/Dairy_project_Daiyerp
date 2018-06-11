// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Payment Cycle Report', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		if(!frm.doc.date) {
			frm.set_value("date",frappe.datetime.get_today())
		}
	},
	vlcc_name: function(frm) {
		frm.events.add_cycle_child(frm)		
	},
	cycle: function(frm) {
		frm.fields_dict['cycle'].get_query = function(doc) {
			console.log(doc.vlcc_name)
			return {
				"query": "dairy_erp.dairy_erp.doctype.farmer_payment_cycle_report.farmer_payment_cycle_report.get_cycle",
				filters: {'vlcc': doc.vlcc_name}
			}
		}
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
		frm.events.add_cycle_child(frm)		
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
						console.log(r.message)
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

						});
						$.each(r.message.child_advance, function(i, d) {
							var row = frappe.model.add_child(cur_frm.doc, "Advance Child", "advance_child");
							console.log(d)
							row.adv_id = d.name
							row.principle = d.advance_amount
							row.emi_amount = d.emi_amount
							row.outstanding = d.outstanding_amount
							row.extension = d.extension
							row.paid_instalment = d.paid_instalment
							row.no_of_instalment = d.no_of_instalment
						})
						frm.set_value("total_amount", total)
						frm.set_value("incentives", r.message.incentive)
						frm.set_value("advance_outstanding", r.message.advance)
						frm.set_value("loan_outstanding", r.message.loan)
						frm.set_value("total_bill",flt(frm.doc.total_amount) + flt(frm.doc.incentives))
						frm.set_value("feed_and_fodder",r.message.fodder)
						frm.set_value("veterinary_services", r.message.vet)
						frm.refresh_fields();
					}
					else{
						console.log("######")
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
		}
	}
});


