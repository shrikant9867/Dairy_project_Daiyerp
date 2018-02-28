
frappe.ui.form.on("Delivery Note", {
	onload:function(frm){
		frm.set_query("customer",erpnext.queries.customer(frm.doc));
	}
});
$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));