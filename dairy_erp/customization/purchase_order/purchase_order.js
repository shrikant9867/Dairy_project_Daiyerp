cur_frm.add_fetch("supplier", "supplier_type", "supplier_type")

frappe.ui.form.on('Purchase Order', {
	onload: function(frm) {
		if(frm.doc.__islocal){
			frm.set_value("supplier_address","")
			frm.set_value("shipping_address","")
		}
		if (has_common(frappe.user_roles, ["Camp Operator", "Camp Manager"])){
			cur_frm.cscript.make_is_dropship(frm);
		} 
	},

	refresh: function(frm) {
		dairy.price_list.trigger_price_list();
		if (has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager"])){
			frm.set_df_property("is_dropship", "hidden", 1);
			frm.set_df_property("chilling_centre", "hidden", 1);
		}
	},
	
	supplier: function(frm) {
		if(get_session_user_type().operator_type == 'VLCC' && 
		(get_supplier_type(frm.doc.supplier) == "Farmer" ||
		get_supplier_type(frm.doc.supplier) == "General")) {
			frm.set_value("supplier","")
			frappe.throw(__("Supplier Type Cannot be Farmer/General"))
		}
		else if(get_session_user_type().operator_type == 'Camp Office' && 
		get_supplier_type(frm.doc.supplier) == "Vlcc Type") {
			frm.set_value("supplier","")
			frappe.throw(__("Supplier Type Cannot be <b>Vlcc Type</b>"))
		}

		erpnext.utils.get_party_details(frm);
	}
})
$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));


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

get_supplier_type = function(supplier) {
	var type = ''
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "Supplier",
			filters: {"name": supplier},
			fieldname: "supplier_type"
		},
		async:false,
		callback: function(r){
			if(r.message){	
				type = r.message.supplier_type
			}
		}
	});
	return type
}

frappe.ui.form.on("Purchase Order Item", {

	qty: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (["COW Milk","BUFFALO Milk"].indexOf(child.item_code) <= -1){
			child.qty = Math.floor(child.qty)
			frappe.model.set_value(cdt, cdn, "new_dn_qty",parseFloat(child.qty));			
			cur_frm.refresh_fields('items');
		}
	}
});


cur_frm.cscript.make_is_dropship = function(frm){
	frappe.call({
		method: "dairy_erp.customization.purchase_order.purchase_order.make_is_dropship",
		callback: function(r){
			if(r.message && r.message == "True"){
				frm.set_value("is_dropship",1)
				frm.set_df_property("is_dropship", "read_only", 1);
			}
		}
	});
}