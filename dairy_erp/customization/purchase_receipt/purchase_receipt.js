
frappe.ui.form.on("Purchase Receipt Item", {
	qty: function(doc, cdt, cdn) {
		/*var item = frappe.get_doc(cdt, cdn);
		frappe.model.round_floats_in(item, ["qty", "received_qty"]);
		
		
		if(item.received_qty) {
			if(item.qty > item.received_qty){
				frappe.model.set_value(cdt,cdn,"qty","")
				frappe.model.set_value(cdt,cdn,"rejected_qty","")
				frappe.throw("<b>Accepted Quantity</b> should not be greater than <b>Dispatched Quantity</b>")
			}
			frappe.model.round_floats_in(item, ["qty", "received_qty"]);
		}*/
	}

})
$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));