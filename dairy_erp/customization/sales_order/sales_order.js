
frappe.ui.form.on("Sales Order", {
	onload:function(frm){
		frm.set_query("customer",erpnext.queries.customer(frm.doc));
	}
});