
frappe.ui.form.on("Purchase Receipt Item", {
	qty: function(doc, cdt, cdn) {
		var item = frappe.get_doc(cdt, cdn);
		//original_qty, received_qty, qty, rejected_qty
		if(item.original_qty && item.purchase_order) {
			if(item.qty > item.original_qty) {
				frappe.msgprint("Accepted Quantity should not be greater than Ordered/Requested Quantity")
				frappe.model.set_value(cdt, cdn, "qty", 0)
			}
			frappe.model.round_floats_in(item, ["qty", "received_qty", "rejected_qty"]);
			rejected_qty = flt(item.original_qty - item.qty, precision("rejected_qty", item));
			frappe.model.set_value(cdt, cdn, "rejected_qty", rejected_qty)
		}

		if(!item.rejected_qty && item.qty) {
			frappe.model.set_value(cdt, cdn, "received_qty", item.qty)
		}

		frappe.model.round_floats_in(item, ["qty", "received_qty", "rejected_qty"]);
	}
})

frappe.ui.form.on("Purchase Receipt", {
	refresh: function(frm) {
		dairy.price_list.trigger_price_list();
	}
})
$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));