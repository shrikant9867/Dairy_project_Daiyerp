frappe.listview_settings['Material Request'] = {
	onload: function(me) {
		user_type = get_session_user_type()
		console.log(user_type)
		if ((frappe.session.user != "Administrator")) {
			if (user_type.operator_type == "Camp Office") {
				frappe.route_options = {
					"camp_office" : user_type.branch_office
				};
			}
			if (user_type.operator_type == "VLCC"){
				console.log("inside")
				frappe.route_options = {
					"company" : user_type.company
				};
			}
		}
		me.page.set_title(__("To Do"));

	},
};

get_session_user_type = function() {
var user;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "User",
			filters: {"name": frappe.session.user},
			fieldname: ["operator_type","branch_office","company"]
		},
		async:false,
		callback: function(r){
			if(r.message){	
				user = {
					"operator_type": r.message.operator_type,
					"branch_office": r.message.branch_office,
					"company": r.message.company
				}			
			}
		}
	});

	return user
}