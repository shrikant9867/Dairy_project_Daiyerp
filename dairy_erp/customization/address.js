frappe.ui.form.on("Address", {
	refresh: function(frm) {
		
		if(!frm.doc.__islocal && in_list(['Head Office','Camp Office','Chilling Centre','Plant'], frm.doc.address_type)){
			frm.add_custom_button(__("Dairy Dashboard"), function() {
				frappe.set_route("dairy-dashboard");
			})
		}
		frm.set_df_property("user", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("operator_name", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("centre_id", "read_only", frm.doc.__islocal ? 0:1);
	
	},
	onload: function(frm){
		frm.set_query("associated_camp_office", function () {
			return {
				"filters": {
					"address_type": "Camp Office",
				}
			};
		});

		operator = get_session_user_type()
		if (inList(["Camp Office","VLCC"],operator.operator_type)){
			frm.set_df_property("linked_with", "hidden", 1);
		}
	},
	validate: function(frm) {
		var user_ = get_session_user_type()
		if(user_.operator_type == "VLCC" && in_list(['Head Office','Camp Office','Chilling Centre','Plant'], frm.doc.address_type)){
		 	frappe.throw(__("Address Type must be vlcc"))
		}
	}

})

get_session_user_type = function() {
	var user;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "User",
			filters: {"name": frappe.session.user},
			fieldname: ["operator_type","company"]
		},
		async:false,
		callback: function(r){
			if(r.message){	
				user = {
					"operator_type": r.message.operator_type,
					"company": r.message.company
				}		
			}
		}
	});

	return user
}