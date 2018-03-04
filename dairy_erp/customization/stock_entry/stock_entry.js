frappe.ui.form.on('Stock Entry', {
	onload:function(frm){
		frm.set_df_property("from_warehouse", "read_only",1);
		if (get_session_user_type().operator_type == "Chilling Centre"){
			camp = address_attr(get_session_user_type().branch_office)
			console.log(camp.camp_office,"##")
			frm.set_value("camp_office",camp.camp_office)
		}
		/*if (get_session_user_type().operator_type == "Camp Office"){
			load_attr(frm)
		}*/
	},
	refresh: function(frm){
		// if (get_session_user_type().operator_type == "Chilling Centre"){
		// 	camp = address_attr(get_session_user_type().branch_office)
		// 	console.log(camp.camp_office,"##")
		// 	frm.set_value("camp_office",camp.camp_office)
		// 	frm.set_value("to_warehouse",)
		// }
		// if (get_session_user_type().operator_type == "Camp Office"){
		// 	load_attr(frm)
		// }
	}
})

get_session_user_type = function() {
	var user;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "User",
			filters: {"name": frappe.session.user},
			fieldname: ["operator_type","company","branch_office"]
		},
		async:false,
		callback: function(r){
			if(r.message){	
				user = {
					"operator_type": r.message.operator_type,
					"company": r.message.company,
					"branch_office":r.message.branch_office
				}		
			}
		}
	});

	return user
}


address_attr = function(branch_office) {
	var camp;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "Address",
			filters: {"name": branch_office},
			fieldname: ["associated_camp_office","warehouse"]
		},
		async:false,
		callback: function(r){
			if(r.message){
			console.log(r.message)	
				camp = {
					"camp_office": r.message.associated_camp_office,
					"warehouse": r.message.warehouse
				}		
			}
		}
	});

	return camp
}

/*load_attr = function(frm) {
	camp = address_attr(get_session_user_type().branch_office)
	frm.set_value('purpose','Material Transfer')
	frm.set_value('from_warehouse',camp.warehouse)
}*/

frappe.ui.form.on('Stock Entry Detail','qty', function(frm) {
	console.log(frm)
})