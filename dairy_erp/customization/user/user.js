frappe.ui.form.on('User', {
	refresh: function (frm) {
		frm.set_df_property("operator_type", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("branch_office", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("company", "read_only", frm.doc.__islocal ? 0:1);

	}/*,
	onload: function(frm){
		frm.set_df_property("language", "read_only",1);
	}*/
})