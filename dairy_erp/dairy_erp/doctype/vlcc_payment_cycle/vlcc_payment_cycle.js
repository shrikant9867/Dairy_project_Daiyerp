// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('VLCC Payment Cycle', {
	refresh: function(frm) {

	},
	no_of_cycles: function(frm){

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
			var row = frappe.model.add_child(frm.doc,"VLCC Payment Child","cycles");
		 	i == 1 ? row.start_day = 1 : ""
			row.cycle = "Cycle " + i
		}
		var cycle = frappe.meta.get_docfield('VLCC Payment Child', "cycle", frm.doc.name);
		cycle.read_only = 1;
		frm.refresh_field("cycles");	
	},
	min_set_per: function(frm){
		if (frm.doc.min_set_per > 100){
			frm.set_value("min_set_per","")
			frappe.throw("Percentage can not be greater than 100")
		}else if(frm.doc.min_set_per === 0){
			frm.set_value("min_set_per","")
			frappe.throw("Please Enter Percentage more than Zero")
		}
	}
});


frappe.ui.form.on('VLCC Payment Child', {

	cycles_add: function(frm,cdt,cdn) {
		frappe.msgprint("You can not add cycles manually")
		frm.reload_doc();
	},
	cycles_remove: function(frm,cdt,cdn) {
		frappe.msgprint("You can not remove cycles manually")
		frm.reload_doc();
	}
});



