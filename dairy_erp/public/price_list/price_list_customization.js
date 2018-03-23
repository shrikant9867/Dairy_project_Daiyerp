frappe.provide("dairy.price_list");

STANDARD_USERS = ["Guest", "Administrator"]
dairy.price_list.PriceListController = Class.extend({
	onload: function() {
		if(!in_list(STANDARD_USERS, frappe.session.user))
			dairy.price_list.set_price_list_(this.frm.doc);
	},

	supplier:function(){
		if(!in_list(STANDARD_USERS, frappe.session.user))
			dairy.price_list.set_price_list_(this.frm.doc);
	},
	customer:function(){
		if(!in_list(STANDARD_USERS, frappe.session.user))
			dairy.price_list.set_price_list_(this.frm.doc);
	},
	farmer:function(){
		if(!in_list(STANDARD_USERS, frappe.session.user))
			dairy.price_list.set_price_list_(this.frm.doc);
	},

	validate: function(){
		$.each(cur_frm.doc.items, function(idx, row) {
			console.log(row.rate)
			if(!row.rate || row.rate == 0) {
				frappe.throw(__("The item price for selected <b>{0}</b> is zero, do set the Material Price list for that Item", [row.item_code]))
			}
		})
	}
})

dairy.price_list.set_price_list_= function(doc) {
	if (cur_frm.doc.__islocal && (!in_list([1,2], cur_frm.doc.docstatus))) {
		selling = ["Sales Invoice", "Delivery Note"]
		buying = ["Purchase Order", "Purchase Invoice", "Purchase Receipt"]
		if (in_list(selling, doc.doctype)) {
			dairy.price_list.guess_price_list("Selling", doc);
		}
		else if(in_list(buying, doc.doctype)) {
			dairy.price_list.guess_price_list("Buying", doc);
		}
	}
}

dairy.price_list.guess_price_list = function(transaction_type,doc) {
	frappe.call({
		method: "dairy_erp.customization.price_list.price_list_customization.guess_price_list",
		args: {"transaction_type": transaction_type, "doc": doc},
		callback: function(r) {
			price_list_field = transaction_type == "Selling" ? "selling_price_list" : "buying_price_list"
			if(!r.exc && r.message){
				cur_frm.set_value(price_list_field, r.message)
				cur_frm.refresh_field(price_list_field)
				dairy.price_list.trigger_price_list();
			}
			dairy.price_list.trigger_price_list();
		}
	})
}

dairy.price_list.trigger_price_list = function() {
	// trigger price list rate
	$.each(cur_frm.doc.items, function(idx, row) {
		cur_frm.script_manager.trigger("price_list_rate", row.doctype, row.name);
	})
	cur_frm.refresh_field("items")
}