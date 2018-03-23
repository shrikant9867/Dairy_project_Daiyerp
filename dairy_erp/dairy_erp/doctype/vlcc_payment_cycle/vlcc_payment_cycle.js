// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('VLCC Payment Cycle', {
	refresh: function(frm) {

	},
	no_of_cycles: function(frm){

		frm.set_value("cycles" ,"");
		for(i=1;i<= frm.doc.no_of_cycles;i++){
			var row = frappe.model.add_child(frm.doc,"VLCC Payment Child","cycles");
		 	i == 1 ? row.start_day = 1 : ""
			row.cycle = "Cycle " + i
		}
		var cycle = frappe.meta.get_docfield('VLCC Payment Child', "cycle", frm.doc.name);
		cycle.read_only = 1;
		frm.refresh_field("cycles");
		
	}
});

frappe.ui.form.on('VLCC Payment Child', {
	start_day:function(frm,cdt,cdn){

	}
});




