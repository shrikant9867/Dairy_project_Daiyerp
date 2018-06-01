// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Payment Cycle Report', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		frm.set_value("date",frappe.datetime.get_today())
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
					"farmer_id": frm.doc.farmer_id
				},
				callback:function(r){
					if(r.message){
						frm.set_value("fmcr_details", "")
						total = 0
						$.each(r.message, function(i, d) {
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
						refresh_field("fmcr_details");
						frm.set_value("total_amount",total)
					
					}
				}
			})
		}
		else{
			frm.set_value("fmcr_details","")
			frm.set_value("total_amount",0)
		}
	}
});


