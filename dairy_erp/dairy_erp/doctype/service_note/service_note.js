// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

cur_frm.add_fetch('item_code','item_name','item_name');
cur_frm.add_fetch('item_code','description','description');
cur_frm.add_fetch('item_code','stock_uom','stock_uom');
cur_frm.add_fetch('item_code','default_warehouse','warehouse');
cur_frm.add_fetch('item_code','item_group','item_group');
cur_frm.add_fetch('item_code','stock_uom','uom');
cur_frm.add_fetch('item_code','image','image');
cur_frm.add_fetch('farmer','full_name','farmer_name');

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
					frm.set_value("vlcc_name",r.message.company);
				}
			}
		});
	},

	taxes_and_charges: function(frm) {
		if (frm.doc.taxes_and_charges) {
			frappe.call({
				method: "dairy_erp.dairy_erp.doctype.local_sale.local_sale.fetch_taxes",
				args: {
					"tax": frm.doc.taxes_and_charges
				},
				callback: function(r) {
					frm.set_value("taxes" ,"");
					console.log("###",r.message)
					if (r.message) {
						$.each(r.message.taxes, function(i, d) {
							var row = frappe.model.add_child(cur_frm.doc, "Sales Taxes and Charges Template", "taxes");
							row.charge_type = d.charge_type;
							row.account_head = d.account_head;
							row.cost_center = d.cost_center;
							row.description = d.description;
							row.rate = d.rate;
							row.tax_amount = d.tax_amount;
							row.title = r.message.name
							row.company = r.message.company
						});
					}
					refresh_field("taxes");
				}
			});
		};
	},

	additional_discount_percentage: function(frm) {
		if (frm.doc.apply_discount_on == 'Grand Total') {
			if (frm.doc.additional_discount_percentage) {
				frm.events.get_discount_amt(frm)
				frm.events.get_grand_total(frm)
			};
		};
		if (frm.doc.apply_discount_on == 'Net Total') {
			if (frm.doc.additional_discount_percentage) {
				frm.events.get_discount_amt(frm)
				frm.events.get_grand_total(frm)
			};
		};
	},

	discount_amount: function(frm) {
		if (frm.doc.apply_discount_on == 'Grand Total') {
			if (frm.doc.discount_amount) {
				frm.events.get_discount_percent(frm)
				frm.events.get_grand_total(frm)
			};
		};
		if (frm.doc.apply_discount_on == 'Net Total') {
			if (frm.doc.discount_amount) {
				frm.events.get_discount_percent(frm)
				frm.events.get_grand_total(frm)
			};
		};
	},

	farmer_name: function(frm) {
		if (cur_frm.doc.farmer_name) {
			frappe.call({
				method:"dairy_erp.dairy_erp.doctype.service_note.service_note.get_effective_credit",
				args:{
					"farmer_name": cur_frm.doc.farmer_name
				},
				callback: function(r) {
					frm.set_value("effective_credit" ,0);
					if(r.message) {
						frm.set_value("effective_credit", r.message);			
					}
					else
						frappe.msgprint(__("Cannot create <b>'Service Note'</b> if <b>'Effective Credit'</b> is 0.0")); 
				}
			});
		}

		// frappe.call({
		// 	method:"dairy_erp.dairy_erp.doctype.service_note.service_note.get_farmer_details",
		// 	args:{
		// 		"customer": frm.doc.customer
		// 	},
		// 	callback: function(r) {
		// 		if(r.message) {
		// 			console.log(r.message)
		// 			frm.set_value("customer_address",r.message.address);
		// 			frm.set_value("address_details",r.message.address_details);
		// 		}
		// 	}
		// });
	},
	get_total_on_qty:function(frm) {
		total_amt = 0
		$.each(frm.doc.items, function(idx, row){
			total_amt += row.amount
		})
		console.log(total_amt)
		frm.set_value("total", total_amt);
		frm.refresh_field("total")
	},
	get_discount_amt:function(frm) {
		discount_amount = (frm.doc.total * frm.doc.additional_discount_percentage)/100
		frm.set_value("discount_amount", discount_amount);
		frm.refresh_field("discount_amount")
	},
	get_discount_percent:function(frm) {
		discount_percent = (100 * frm.doc.discount_amount)/frm.doc.total
		frm.set_value("additional_discount_percentage", discount_percent);
		frm.refresh_field("additional_discount_percentage")
	},
	get_grand_total:function(frm) {
		grand_total = frm.doc.total - frm.doc.discount_amount
		rounded_total = Math.round(frm.doc.grand_total);
		frm.set_value("grand_total", grand_total);
		frm.set_value("net_total", grand_total);
		frm.set_value("rounded_total", rounded_total);
		frm.set_value("outstanding_amount", grand_total);
		frm.refresh_field("grand_total")
		frm.refresh_field("net_total")
		frm.refresh_field("rounded_total")
		frm.refresh_field("outstanding_amount")
	}
});

frappe.ui.form.on('Service Note Item', {
	item_code: function(frm, cdt, cdn) {
			if (cur_frm.doc.farmer_name){
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
				frappe.throw('Please specify: Farmer. It is needed to fetch Item Details');
				cur_frm.reload_doc()
			}

			refresh_field("items");
		},
		qty:function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.item_code){
			var amount = parseFloat(child.rate) * parseFloat(child.qty);
			frappe.model.set_value(cdt, cdn, "amount",amount);
			frm.events.get_total_on_qty(frm)
			if (cur_frm.doc.effective_credit < cur_frm.doc.total) {
				frappe.throw(__("Cannot create <b>'Service Note'</b> if <b>'Effective Credit'</b> is less than <b>Total</b>")); 
			};
		}
		
		refresh_field("items");
	},
	rate:function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.item_code){
			var amount = parseFloat(child.rate) * parseFloat(child.qty);
			frappe.model.set_value(cdt, cdn, "amount",amount);
			frm.events.get_total_on_qty(frm)
			if (cur_frm.doc.effective_credit < cur_frm.doc.total) {
				frappe.throw(__("Cannot create <b>'Service Note'</b> if <b>'Effective Credit'</b> is less than <b>Total</b>")); 
			};
		}
		
		refresh_field("items");
	},
	});
cur_frm.fields_dict.farmer_name.get_query = function(doc) {
	return {filters: { vlcc_name: doc.vlcc_name}}
}

// get_query for items
cur_frm.fields_dict['items'].grid.get_field("item_code").get_query = function(doc, cdt, cdn) {
	return {
		query: "dairy_erp.dairy_erp.doctype.service_note.service_note.get_custom_item"
	}
}