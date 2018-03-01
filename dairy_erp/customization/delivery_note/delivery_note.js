
frappe.ui.form.on("Delivery Note", {
	onload:function(frm){
	}
});
$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));