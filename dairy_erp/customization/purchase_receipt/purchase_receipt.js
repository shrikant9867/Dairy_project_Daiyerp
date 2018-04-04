
frappe.ui.form.on("Purchase Receipt Item", {
	qty: function(doc, cdt, cdn) {
		var item = frappe.get_doc(cdt, cdn);
		frappe.model.round_floats_in(item, ["qty", "received_qty"]);
		if(item.delivery_note || item.purchase_order || item.material_request) {
			if(item.qty > item.received_qty) {
				frappe.model.set_value(cdt, cdn, "qty", 0)
				frappe.throw("Accepted Quantity should not be greater than Ordered/Requested Quantity")
			}
			frappe.model.round_floats_in(item, ["qty", "received_qty"]);
			item.rejected_qty = flt(item.received_qty - item.qty, precision("rejected_qty", item));
		 }
	}
})

frappe.ui.form.on("Purchase Receipt", {
	refresh: function(frm) {
		dairy.price_list.trigger_price_list();
	}
})
$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));