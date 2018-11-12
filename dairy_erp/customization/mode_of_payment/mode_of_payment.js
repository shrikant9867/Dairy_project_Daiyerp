frappe.ui.form.on("Mode of Payment", {
	onload: function(frm) {
		frm.trigger("make_read_only");
	},

	refresh: function(frm) {
		frm.trigger("make_read_only");
	},

	make_read_only: function(frm) {
		// vlcc , camp, chilling user's can't modify saved form
		not_allowed_user = ["Vlcc Manager","Vlcc Operator"]
		user_ = frappe.session.user
		if(user_ != "Administrator" && !frm.doc.__islocal && has_common(frappe.user_roles, not_allowed_user)) {
			frm.set_read_only()
			frm.refresh_fields()
		}
	}
})