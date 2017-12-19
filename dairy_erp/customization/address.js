frappe.ui.form.on("Address", {
	refresh: function(frm) {
		if(!frm.doc.__islocal && in_list(['Head Office','Camp Office','Chilling Centre','Plant'], frm.doc.address_type)){
			frm.add_custom_button(__("Dairy Dashboard"), function() {
				frappe.set_route("dairy-dashboard");
			})
		}
	}

})