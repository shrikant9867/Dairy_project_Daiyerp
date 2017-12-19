frappe.ui.form.on('Supplier', {
	refresh: function(frm) {
		if(!frm.doc.__islocal && in_list(['Dairy Local'], frm.doc.supplier_type)){
					frm.add_custom_button(__("Dairy Dashboard"), function() {
						frappe.set_route("dairy-dashboard");
					})
				}
			}
})