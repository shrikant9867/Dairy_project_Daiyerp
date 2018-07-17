frappe.ui.form.on("Purchase Receipt Item", {
	qty: function(doc, cdt, cdn) {
		var item = frappe.get_doc(cdt, cdn);
		frappe.model.round_floats_in(item, ["qty", "received_qty"]);
		if(item.delivery_note || item.purchase_order || item.material_request) {
			if(item.qty > item.received_qty) {
				frappe.model.set_value(cdt, cdn, "qty", 0)
				frappe.throw("Accepted Quantity should not be greater than Delivered/Requested Quantity")
			}
			frappe.model.round_floats_in(item, ["qty", "received_qty"]);
			item.rejected_qty = flt(item.received_qty - item.qty, precision("rejected_qty", item));
		 }
	},
	items_add: function(frm, cdt, cdn) {
		if(frm.doc.is_delivery) {	
			frappe.msgprint("You can not add items manually")
			frm.reload_doc();
		}
	},
	items_remove: function(frm, cdt, cdn) {
		if(frm.doc.is_delivery) {
			frappe.msgprint("You can not remove items manually, set accepted qty as Zero instead")
			frm.reload_doc();
		}
	}
})

frappe.ui.form.on("Purchase Receipt", {
	refresh: function(frm) {
		dairy.price_list.trigger_price_list();
	},
	supplier: function(frm) {
		if(get_session_user_type().operator_type == 'Camp Office' && 
		get_supplier_type(frm.doc.supplier) == "Vlcc Type") {
			frm.set_value("supplier","")
			frappe.throw(__("Supplier Type Cannot be <b>Vlcc Type</b>"))
		}
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