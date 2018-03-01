frappe.provide("dairy.price_list");

STANDARD_USERS = ["Guest", "Administrator"]
dairy.price_list.PriceListController = Class.extend({
	onload: function() {
		if(! in_list(STANDARD_USERS, frappe.session.user))
			dairy.price_list.set_price_list_(this.frm.doc);
	},
	supplier:function(){
		if(! in_list(STANDARD_USERS, frappe.session.user))
			dairy.price_list.set_price_list_(this.frm.doc);
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
				console.log(r.message,"rrrrr")
				cur_frm.set_value(price_list_field, r.message)
				cur_frm.refresh_field(price_list_field)
			}
			/*else {
				frappe.msgprint(__("Local or Global {0} not found", [frappe.model.unscrub(price_list_field)]))
			}*/
		}
	})
}