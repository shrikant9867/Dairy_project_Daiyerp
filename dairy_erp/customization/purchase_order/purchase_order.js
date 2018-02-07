
frappe.ui.form.on('Purchase Order', {

	onload: function(frm) {
		if(frm.doc.__islocal){
			frm.set_value("supplier_address","")
			frm.set_value("shipping_address","")
		}
	}
})