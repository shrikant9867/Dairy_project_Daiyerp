// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt

{% include 'erpnext/selling/sales_common.js' %}

cur_frm.add_fetch('item_code','item_name','item_name');
cur_frm.add_fetch('item_code','description','description');
cur_frm.add_fetch('item_code','stock_uom','stock_uom');
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
	},

	taxes_and_charges: function(frm) {
		if (frm.doc.taxes_and_charges) {
			frappe.call({
				method: "dairy_erp.dairy_erp.doctype.local_sale.local_sale.fetch_taxes",
				args: {
					"tax": frm.doc.taxes_and_charges
				},
				callback: function(r) {
					// console.log(r.message)
					frm.set_value("taxe_charge_template" ,"");
					if (r.message) {
						$.each(r.message, function(i, d) {
							// console.log(d)
							var row = frappe.model.add_child(cur_frm.doc, "Sales Taxes and Charges Template", "taxe_charge_template");
							row.charge_type = d.charge_type;
							row.account_head = d.account_head;
							row.cost_center = d.cost_center;
							row.description = d.description;
							row.rate = d.rate;
							row.tax_amount = d.tax_amount;
							// row.total = row.rate * row.tax_amount;
						});
					}
					refresh_field("taxe_charge_template");
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

	farmer: function(frm){
		if (cur_frm.doc.farmer) {
			frappe.call({
				method:"dairy_erp.dairy_erp.doctype.service_note.service_note.get_effective_credit",
				args:{
					"customer": cur_frm.doc.farmer_name
				},
				callback: function(r) {
					frm.set_value("effective_credit" ,0);
					if(r.message) {
						frm.set_value("effective_credit", r.message);			
					}
					else
						frappe.msgprint(__("Cannot create <b>'Local Sale'</b> if <b>'Effective Credit'</b> is 0.0")); 
				}
			});
		}
	},
	get_total_on_qty:function(frm) {
		total_amt = 0
		$.each(frm.doc.items, function(idx, row){
			total_amt += row.amount
		})
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
		frm.set_value("rounded_total", rounded_total);
		frm.set_value("outstanding_amount", grand_total);
		frm.refresh_field("grand_total")
		frm.refresh_field("rounded_total")
		frm.refresh_field("outstanding_amount")
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
							 		// frm.set_value("total", amount);			
								}
							}
						});
						frappe.call({
							method:"dairy_erp.dairy_erp.doctype.local_sale.local_sale.get_vlcc_warehouse",
							callback: function(r) {
								if(r.message) {
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
				cur_frm.refresh_fields('item_code');
			}
			else{
				frappe.throw('Please specify: Customer or Farmer. It is needed to fetch Item Details');
				cur_frm.reload_doc()
			}

			var d = locals[cdt][cdn];
			var total = 0

			refresh_field("items");
		},
		qty:function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.item_code){
			var amount = parseFloat(child.rate) * parseFloat(child.qty);
			frappe.model.set_value(cdt, cdn, "amount",amount);
			frm.events.get_total_on_qty(frm)
			if (cur_frm.doc.effective_credit < cur_frm.doc.total) {
				frappe.msgprint(__("Cannot create <b>'Local Sale'</b> if <b>'Effective Credit'</b> is less than <b>Total</b>")); 
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
				frappe.msgprint(__("Cannot create <b>'Local Sale'</b> if <b>'Effective Credit'</b> is less than <b>Total</b>")); 
			};
		}
		
		refresh_field("items");
	}

	
});
