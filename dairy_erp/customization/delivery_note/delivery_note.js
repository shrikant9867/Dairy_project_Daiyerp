
frappe.ui.form.on("Delivery Note", {
	onload:function(frm){
		frm.set_query("customer",erpnext.queries.customer(frm.doc));
	}
});