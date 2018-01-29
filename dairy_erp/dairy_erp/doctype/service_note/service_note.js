// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

cur_frm.add_fetch('item_code','item_name','item_name');
cur_frm.add_fetch('item_code','description','description');
cur_frm.add_fetch('item_code','stock_uom','stock_uom');
cur_frm.add_fetch('item_code','default_warehouse','warehouse');
cur_frm.add_fetch('item_code','item_group','item_group');
cur_frm.add_fetch('item_code','stock_uom','uom');
cur_frm.add_fetch('item_code','image','image');
cur_frm.add_fetch('customer','full_name','customer_name');

frappe.ui.form.on('Service Note', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		frappe.call({
			method:"dairy_erp.dairy_erp.doctype.service_note.service_note.get_vet_ai_company",
			args:{
				"user": frappe.session.user
			},
			callback: function(r) {
				if(r.message) {
					frm.set_value("company",r.message.company);
					frm.set_value("vet_ai_tech",r.message.first_name);
					frm.set_value("ai_contact",r.message.mobile_no);
					frm.set_value("ai_address",r.message.address);
					frm.set_value("ai_address_details",r.message.address_details);
				}
			}
		});
	},
	customer: function(frm) {
		// frm.set_query("farmer_address", function () {
		// 	return {
		// 		"filters": {
		// 			"address_type": "Farmer",
		// 			"name": frm.doc.customer_name + "-Farmer"
		// 		}
		// 	};
		// });
		// erpnext.utils.get_address_display(cur_frm, "farmer_address");

		frappe.call({
			method:"dairy_erp.dairy_erp.doctype.service_note.service_note.get_farmer_details",
			args:{
				"customer": frm.doc.customer
			},
			callback: function(r) {
				if(r.message) {
					console.log(r.message)
					frm.set_value("customer_address",r.message.address);
					frm.set_value("address_details",r.message.address_details);
				}
			}
		});
	}
	// farmer_address: function(frm) {
	// 	erpnext.utils.get_address_display(frm, "farmer_address", "address_details");
	// }
});

frappe.ui.form.on('Delivery Note Item', {
	item_code: function(frm, cdt, cdn) {
			if (cur_frm.doc.customer){
				var child = locals[cdt][cdn];
				if(child){
					if (child.item_code){
						frappe.call({
							method:"dairy_erp.dairy_erp.doctype.service_note.service_note.get_price_list_rate",
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
						});

						frappe.call({
							method:"dairy_erp.dairy_erp.doctype.service_note.service_note.get_vlcc_warehouse",
							callback: function(r) {
								if(r.message) {
									// console.log(r.message)
									frappe.model.set_value(cdt, cdn, "warehouse",r.message)	
								}
							}
						});

						frappe.call({
							method: "frappe.client.get_value",
							args: {
								doctype: "UOM Conversion Detail",
								filters: {"parent": child.item_code},
								fieldname: "conversion_factor"
							},
							callback: function(r){
								if(r.message){
									// console.log(r.message.conversion_factor)
									frappe.model.set_value(cdt, cdn, "conversion_factor",r.message.conversion_factor)
								}
							}
						});
					}
				}	
				cur_frm.refresh_fields('items');
			}
			else{
				frappe.throw('Please specify: Customer. It is needed to fetch Item Details');
				cur_frm.reload_doc()
			}

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
cur_frm.fields_dict.customer.get_query = function(doc) {
	return {filters: { vlcc_name: doc.company}}
}

// get_query for items
cur_frm.fields_dict['items'].grid.get_field("item_code").get_query = function(doc, cdt, cdn) {
	return {
		query: "dairy_erp.dairy_erp.doctype.service_note.service_note.get_custom_item"
	}
}