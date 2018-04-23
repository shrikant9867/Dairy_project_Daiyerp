

frappe.ui.form.on("Contact", {
	//contact filtering on vlcc form
	refresh: function(frm) {
		if(frm.doc.__islocal){
			var last_route = frappe.route_history.slice(-2, -1)[0];
			if(last_route && last_route[1] == "Village Level Collection Centre"){
				frm.set_value("vlcc", last_route[2])
			}
		}
	}
})