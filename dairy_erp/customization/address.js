frappe.ui.form.on("Address", {
	refresh: function(frm) {
		frm.trigger("make_read_only");
		frm.events.set_route_vlcc(frm)
		if(!frm.doc.__islocal && in_list(['Head Office','Camp Office','Chilling Centre','Plant'], frm.doc.address_type)){
			frm.add_custom_button(__("Dairy Dashboard"), function() {
				frappe.set_route("dairy-dashboard");
			})
		}
		frm.set_df_property("user", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("operator_name", "read_only", frm.doc.__islocal ? 0:1);
		frm.set_df_property("centre_id", "read_only", frm.doc.__islocal ? 0:1);
		frm.trigger("different_operator");
	
	},
	onload: function(frm){
		frm.trigger("make_read_only");
		frm.trigger("set_address_type_option");
		frm.set_query("associated_camp_office", function () {
			return {
				"filters": {
					"address_type": "Camp Office",
				}
			};
		});

		operator = get_session_user_type()
		if (in_list(["Camp Office","VLCC"],operator.operator_type)){
			frm.set_df_property("linked_with", "hidden", 1);
		}

		frm.trigger("show_links_section");
	},
	validate: function(frm) {
		var user_ = get_session_user_type()
		if(user_.operator_type == "VLCC" && in_list(['Head Office','Camp Office','Chilling Centre','Plant'], frm.doc.address_type)){
		 	frappe.throw(__("Address Type must be vlcc"))
		}
	},

	address_type: function(frm) {
		manager_reqd = has_common([frm.doc.address_type], ['Camp Office','Chilling Centre','Plant'])
		frm.set_df_property("manager_email", "reqd", manager_reqd);
		frm.set_df_property("manager_name", "reqd", manager_reqd);
		frm.trigger("show_links_section");
	},

	show_links_section: function(frm) {
		// if address type vlcc show links table
		if(frm.doc.address_type == "Vlcc" && has_common(frappe.user_roles, ["Vlcc Manager"])) {
			frm.set_df_property("linked_with", "hidden", 0);
		}
	},

	different_operator: function(frm) {
		frm.toggle_enable("user", frm.doc.different_operator)
		frm.toggle_enable("operator_name", frm.doc.different_operator)
		frm.set_df_property("user", "reqd", frm.doc.different_operator);
		frm.set_df_property("operator_name", "reqd", frm.doc.different_operator);
		refresh_many(["operator_name", "user"])
	},

	set_route_vlcc: function(frm) {
		//address filtering on vlcc form
		if(frm.doc.__islocal){
			var last_route = frappe.route_history.slice(-2, -1)[0];
			if(last_route && last_route[1] == "Village Level Collection Centre"){
				frm.set_value("vlcc", last_route[2])
			}
			if(last_route && last_route[1] == "Veterinary AI Technician") {
				frm.set_value("vet", last_route[2])
			}
		}
	},

	make_read_only: function(frm) {
		// vlcc , camp, chilling user's can't modify saved form
		not_allowed_user = ["Vlcc Manager", "Chilling Center Manager", "Camp Manager", 
			"Camp Operator", "Vlcc Operator","Chilling Center Operator"]
		user_ = frappe.session.user
		if(user_ != "Administrator" && !frm.doc.__islocal && has_common(frappe.user_roles, not_allowed_user)) {
			frm.set_read_only()
			frm.set_df_property("links", "read_only", 1)
			frm.refresh_fields()
		}
	},

	set_address_type_option: function(frm) {
		// set specific address type for vlcc user's
		vlcc_roles = ["Vlcc Manager", "Vlcc Operator"]
		user_ = frappe.session.user
		if(user_ != "Administrator" && has_common(frappe.user_roles, vlcc_roles)) {
			addr_types = [ "","Vlcc", "Veterinary AI Tech", "Farmer", "Billing", "Shipping", "Other"]
			frm.set_df_property("address_type", "options", addr_types);
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