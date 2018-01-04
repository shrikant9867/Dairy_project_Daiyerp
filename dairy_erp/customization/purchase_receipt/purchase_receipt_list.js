frappe.listview_settings['Purchase Receipt'] = {
	onload: function(me) {
		user_type = get_session_user_type()
		if ((frappe.session.user != "Administrator")) {
			if (user_type == "VLCC") {
				frappe.route_options = {
					"company" : "asdas"
				};
			}
			
			// if (in_list(frappe.user_roles,"IT User")) {
			// 	frappe.route_options = {
			// 		"workflow_state" : "Open(IT User)"
			// 	};
			// }

			// if (in_list(frappe.user_roles,"Admin User")) {
			// 	frappe.route_options = {
			// 		"workflow_state" : "Open(Admin User)"
			// 	};
			// }

			// if (in_list(frappe.user_roles,"indentor")) {
			// 		frappe.route_options = {
			// 		"workflow_state" :  ["in",["Approved by Finance Manager", "Send for Approval to Indentor"]]
			// 	};
					

			// }
			// if (in_list(frappe.user_roles,"Finance Manager")) {
			// 		frappe.route_options = {
			// 		"workflow_state" : "Approved By Indentor"
			// 	};
			// }

		}
		me.page.set_title(__("To Do"));

	},
};

get_session_user_type = function() {
//added custom khushal
var user;
	frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "User",
					filters: {"name": frappe.session.user},
					fieldname: "operator_type"
				},
				async:false,
				callback: function(r){
					if(r.message){	
					user = r.message.operator_type			
					}
				}
	});

	return user
}