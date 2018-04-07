frappe.provide("dairy.stock_entry");

frappe.ui.form.on('Stock Entry', {
	onload:function(frm){
		frm.set_query("camp_office", function () {
			return {
				"filters": {
					"address_type": "Camp Office",
				}
			};
		});
		frm.set_df_property("from_warehouse", "read_only",1);
	},
	refresh: function(frm){
		if (get_session_user_type().operator_type == "Chilling Centre"){
			camp = address_attr(get_session_user_type().branch_office)
			if(frm.doc.camp_office != camp.camp_office){
				frm.set_value("camp_office",camp.camp_office)
				frm.refresh_field('camp_office')
			}
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
				camp = {
					"camp_office": r.message.associated_camp_office,
					"warehouse": r.message.warehouse
				}		
			}
		}
	});

	return camp
}

frappe.ui.form.on("Stock Entry Detail", {
	accepted_qty: function(frm, cdt, cdn) {
		dairy.stock_entry.calculate_accept_reject(frm,cdt, cdn, "rejected_qty")
	},

	rejected_qty: function(frm, cdt, cdn) {
		dairy.stock_entry.calculate_accept_reject(frm,cdt, cdn, "accepted_qty")
	}
})

$.extend(dairy.stock_entry, {
	calculate_accept_reject: function(frm, cdt, cdn, field) {
		row = locals[cdt][cdn]
		// validation for cc
		is_cc = has_common(["Chilling Center Operator", "Chilling Center Manager"], frappe.user_roles)
		if(is_cc && row.material_request) {
			if (row.accepted_qty > row.camp_qty || (row.original_qty - row.rejected_qty) > row.camp_qty) {
				frappe.model.set_value(cdt, cdn, "accepted_qty", row.qty)
				frappe.model.set_value(cdt, cdn, "rejected_qty", row.original_qty-row.accepted_qty)
				frappe.throw("Accepted Quantity can not be greater than transferred quantity")
			}
		}
		if (row.original_qty) {
			if(row.accepted_qty > row.original_qty || row.rejected_qty > row.original_qty) {
				frappe.msgprint("Accepted Qty and Rejected Qty must be less than original qty")
				frappe.model.set_value(cdt, cdn, "accepted_qty", 0)
				frappe.model.set_value(cdt, cdn, "rejected_qty", 0)
			}
			else {
				if (field == "rejected_qty") {
					frappe.model.set_value(cdt, cdn, "rejected_qty", row.original_qty - row.accepted_qty);
					frappe.model.set_value(cdt, cdn, "qty", row.accepted_qty);
				}
				else {
					frappe.model.set_value(cdt, cdn, "accepted_qty", row.original_qty - row.rejected_qty);
					frappe.model.set_value(cdt, cdn, "qty", row.accepted_qty);
				}
			}
		}
		else if(row.accepted_qty) {
			frappe.model.set_value(cdt, cdn, "qty", row.accepted_qty);
			frappe.model.set_value(cdt, cdn, "rejected_qty", 0);
		}
		else if(row.rejected_qty) {
			frappe.model.set_value(cdt, cdn, "rejected_qty", 0);
		}
		refresh_field("items")
	}
})