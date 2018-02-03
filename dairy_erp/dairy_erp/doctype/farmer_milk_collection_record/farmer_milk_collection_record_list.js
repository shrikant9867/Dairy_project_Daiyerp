frappe.listview_settings['Farmer Milk Collection Record'] = {
	onload:function(){
		var a = get_session_user_type()
	}
}

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