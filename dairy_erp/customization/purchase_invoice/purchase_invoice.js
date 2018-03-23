$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));

frappe.ui.form.on("Purchase Invoice", {
	onload: function(frm) {
		abbr = frappe.get_abbr(frm.doc.company);
		frm.set_value("credit_to", "Creditors - "+abbr)
	}
})