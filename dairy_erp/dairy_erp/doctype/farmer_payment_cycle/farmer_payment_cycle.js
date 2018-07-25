// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Payment Cycle', {
	refresh: function(frm) {
		frappe.call({
				method: "frappe.client.get_value",
				async : false,
				args: {
					doctype: "User",
					filters: {"name": frappe.session.user},
					fieldname: ["company"]
				},
				callback: function(r){
					if(r.message){
						frm.set_value("vlcc",r.message.company)
					}
				}
			});
		frm.events.check_record_exist(frm)

	},
	no_of_cycles: function(frm){

		frm.events.check_record_exist(frm)
		if(frm.doc.no_of_cycles > 31){
			frm.set_value("no_of_cycles",0)
			frappe.throw("Number of cycles must be between 1-31")
		}
		else if(frm.doc.no_of_cycles < 0){
			frm.set_value("no_of_cycles",0)
			frappe.throw("Number of cycles can not be negative")
		}

		frm.set_value("cycles" ,"");
		for(i=1;i<= frm.doc.no_of_cycles;i++){
			var row = frappe.model.add_child(frm.doc,"Farmer Payment Child","cycles");
		 	i == 1 ? row.start_day = 1 : ""
			row.cycle = "Cycle " + i
		}
		var cycle = frappe.meta.get_docfield('Farmer Payment Child', "cycle", frm.doc.name);
		cycle.read_only = 1;
		frm.refresh_field("cycles");

		frm.events.set_cycle_values(frm)	
	},
	min_set_per: function(frm){
		frm.events.check_record_exist(frm)
		if (frm.doc.min_set_per > 100){
			frm.set_value("min_set_per","")
			frappe.throw("Percentage can not be greater than 100")
		}else if(frm.doc.min_set_per === 0){
			frm.set_value("min_set_per","")
			frappe.throw("Please Enter Percentage more than Zero")
		}
	},
	validate: function(frm) {
		frm.events.check_record_exist(frm)
	},
	check_record_exist: function(frm){
		if(frm.doc.__islocal){	
			frappe.call({	
				method:"dairy_erp.dairy_erp.doctype.farmer_payment_cycle.farmer_payment_cycle.check_record_exist",	
				callback:function(r){
					if(r.message){
						frappe.msgprint("Please add cycles in the existing defination of cycle")
						frappe.set_route("List","Farmer Payment Cycle")
					}
				}
			})
		}
	},
	month: function(frm){
		frm.events.set_cycle_values(frm)
	},
	set_cycle_values: function(frm){
		if(frm.doc.no_of_cycles == 3) {
			frappe.call({
				method:"dairy_erp.dairy_erp.doctype.vlcc_payment_cycle.vlcc_payment_cycle.set_cycle_values",
				args : {"doc":frm.doc},
				callback: function(r){
					var day = 0
					frm.set_value("cycles","")
					for(i=1;i<= frm.doc.no_of_cycles;i++){
						var row = frappe.model.add_child(frm.doc, "VLCC Payment Child", "cycles");
						var s_day = day + 1
						var e_day = s_day + 9
							day = e_day
						row.cycle = "Cycle " + i
						row.start_day = s_day 
						row.end_day = e_day
						if(i == 3) {
							row.end_day = r.message 
						}
					}
					refresh_field("cycles");
				}
			})
		}
	}
});


frappe.ui.form.on('Farmer Payment Child', {

	cycles_add: function(frm,cdt,cdn) {
		frappe.msgprint("You can not add cycles manually")
		frm.reload_doc();
	},
	cycles_remove: function(frm,cdt,cdn) {
		frappe.msgprint("You can not remove cycles manually")
		frm.reload_doc();
	}
});

