$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));

frappe.ui.form.on("Delivery Note Item", {

	item_code: function(frm, cdt, cdn) {
		cur_frm.refresh_fields('item_code');
		if (cur_frm.doc.customer){
			var child = locals[cdt][cdn];
			if(child){ 
				if (child.item_code){
					frappe.model.set_value(cdt, cdn, "qty",parseFloat(child.new_dn_qty));							
				}
			}	
			cur_frm.refresh_fields('item_code');
		}
	}
});