
frappe.ui.form.on("Purchase Receipt Item", {
	qty: function(doc, cdt, cdn) {
		var item = frappe.get_doc(cdt, cdn);
		frappe.model.round_floats_in(item, ["qty", "received_qty"]);

		// if(!doc.is_return && this.validate_negative_quantity(cdt, cdn, item, ["qty", "received_qty"])){ return }

		
		if(item.received_qty) {
			if(item.qty > item.received_qty){
				frappe.model.set_value(cdt,cdn,"qty","")
				frappe.model.set_value(cdt,cdn,"rejected_qty","")
				frappe.throw("Accepted Qty cannot be greater than Received Qty")
			}
			frappe.model.round_floats_in(item, ["qty", "received_qty"]);
			item.rejected_qty = flt(item.received_qty - item.qty, precision("rejected_qty", item));
		}


		// this._super(doc, cdt, cdn);
	}

})
$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));