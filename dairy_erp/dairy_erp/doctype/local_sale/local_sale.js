// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

{% include 'erpnext/selling/sales_common.js' %}

cur_frm.add_fetch('item_code','item_name','item_name');
cur_frm.add_fetch('item_code','description','description');
cur_frm.add_fetch('item_code','stock_uom','stock_uom');
cur_frm.add_fetch('item_code','default_warehouse','warehouse');
cur_frm.add_fetch('item_code','item_group','item_group');
cur_frm.add_fetch('item_code','stock_uom','uom');
cur_frm.add_fetch('item_code','image','image');

frappe.ui.form.on('Local Sale', {
	refresh: function(frm) {

	},

	onload: function(frm) {
		frappe.call({
			method: "dairy_erp.dairy_erp.doctype.local_sale.local_sale.fetch_balance_qty",
			callback: function(r) {
				if(r.message){
					frm.set_value("cow_milk_qty_local",r.message.cow_milk)
					frm.set_value("buffalo_milk_qty_local",r.message.buff_milk)
					frm.set_value("cow_milk_quantity_farmer",r.message.cow_milk)
					frm.set_value("buffalo_milk_qty_farmer",r.message.buff_milk)
				}
				// frm.set_value("buffalo_milk_qty_local", r.message.BUFFALO Milk)
			}
		})
	},

	local_customer_or_farmer: function(frm){
		if (cur_frm.doc.local_customer_or_farmer == "Vlcc Local Customer") {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Customer",
					fieldname: "name",
					filters: { name: "Vlcc Local Cust" },
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("customer", r.message.name);
					}
				}
			});
		}
	} 
});



frappe.ui.form.on('Sales Order Item', {
	item_code: function(frm, cdt, cdn) {
			if (cur_frm.doc.local_customer_or_farmer){
				var child = locals[cdt][cdn];
				if(child){
					if (child.item_code){
						frappe.call({
							method:"dairy_erp.dairy_erp.doctype.local_sale.local_sale.get_price_list_rate",
							args:{
								"item": child.item_code
							},
							callback: function(r) {
								if(r.message) {
									// console.log(r.message)
									frappe.model.set_value(cdt, cdn, "qty",1);
					 				frappe.model.set_value(cdt, cdn, "price_list_rate",parseFloat(r.message));
							 		frappe.model.set_value(cdt, cdn, "rate",child.price_list_rate);
							 		var amount = parseFloat(child.rate) * parseFloat(child.qty)
							 		frappe.model.set_value(cdt, cdn, "amount",amount);
							 		frappe.model.set_value(cdt, cdn, "net_amount",amount);
							 		frappe.model.set_value(cdt, cdn, "base_rate",amount);
							 		frappe.model.set_value(cdt, cdn, "base_net_rate",amount);
							 		frappe.model.set_value(cdt, cdn, "base_amount",amount);
							 		frappe.model.set_value(cdt, cdn, "base_net_amount",amount);			
								}
							}
						})
					}
				}	
				cur_frm.refresh_fields('item_code');
			}
			else{
				frappe.throw('Please specify: Customer or Farmer. It is needed to fetch Item Details');
				cur_frm.reload_doc()
			}

			var d = locals[cdt][cdn];
			var total = 0
			
			// if(!frm.doc.delivery_date) {
			// 	erpnext.utils.copy_value_in_all_row(frm.doc, cdt, cdn, "items", "delivery_date");
			// }


			refresh_field("items");
		},
		qty:function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.item_code){
			var amount = parseFloat(child.rate) * parseFloat(child.qty);
			frappe.model.set_value(cdt, cdn, "amount",amount);
		}
		
		refresh_field("items");
	},
	rate:function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.item_code){
			var amount = parseFloat(child.rate) * parseFloat(child.qty);
			frappe.model.set_value(cdt, cdn, "amount",amount);
		}
		
		refresh_field("items");
	},
	});
