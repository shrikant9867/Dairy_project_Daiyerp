// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Farmer Payment Cycle', {
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
			var row = frappe.model.add_child(frm.doc,"Farmer Payment Child","cycles");
		 	i == 1 ? row.start_day = 1 : ""
			row.cycle = "Cycle " + i
		}
		var cycle = frappe.meta.get_docfield('Farmer Payment Child', "cycle", frm.doc.name);
		cycle.read_only = 1;
		frm.refresh_field("cycles");	
	}
});


frappe.ui.form.on('Farmer Payment Child', {

	cycles_add:function(frm,cdt,cdn){
		$.each(frm.doc.cycles,function(i,d){
			cur_frm.get_field("cycles").grid.grid_rows[frm.doc.cycles.length-1].remove();
		})
		frappe.throw("You can not add cycles manually")
	}
});
