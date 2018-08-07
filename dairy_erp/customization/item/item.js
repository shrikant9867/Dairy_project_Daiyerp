frappe.ui.form.on("Item", {
	onload: function(frm) {
		console.log("------------------")
		frm.trigger("make_read_only");
	},

	refresh: function(frm) {
		frm.trigger("make_read_only");
	},

	make_read_only: function(frm) {
		// Dairy supplier
		not_allowed_user = ["Dairy Supplier"]
		user_ = frappe.session.user
		if(user_ != "Administrator" && !frm.doc.__islocal && has_common(frappe.user_roles, not_allowed_user)) {
			frm.set_read_only()
			frm.refresh_fields()
		}
	}
})