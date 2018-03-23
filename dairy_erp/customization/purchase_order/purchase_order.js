frappe.ui.form.on('Purchase Order', {
	onload: function(frm) {
		if(frm.doc.__islocal){
			frm.set_value("supplier_address","")
			frm.set_value("shipping_address","")
		}
	},

	refresh: function(frm) {
		dairy.price_list.trigger_price_list();
	}
})
$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));