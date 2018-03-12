frappe.ui.form.on("Sales Invoice", {

	onload: function(frm) {	
		if (get_session_user_type().operator_type == "Vet AI Technician")
		{
			frm.set_value("service_note",1)
		}
		frm.set_query("farmer", function () {
			return {
				"filters": {
					"vlcc_name": frm.doc.company,
				}
			};
		})

		frm.set_value("effective_credit","")
		user_ = get_session_user_type()
		if(user_.operator_type != "VLCC"){
			cur_frm.set_df_property('local_sale', 'hidden', 1);
			// cur_frm.set_df_property('due_date', 'hidden', 1);

		}
		if(user_.operator_type != "Vet AI Technician"){
			cur_frm.set_df_property('service_note', 'hidden', 1);
			// cur_frm.set_df_property('due_date', 'hidden', 1);

		}
	},

	local_sale: function(frm) {
		
		if (frm.doc.local_sale){
			frm.set_df_property("customer", "read_only", 1);
			frm.set_df_property("due_date", "read_only", 1);
			frm.set_value("update_stock",1)
			local_sale_operations(frm)
			frm.set_value("due_date",frappe.datetime.nowdate())

		}
		else{
			frm.set_value("customer_or_farmer","Vlcc Local Customer")
			frm.set_df_property("customer", "read_only", 0);
			frm.set_df_property("due_date", "read_only", 0);
			frm.set_value("update_stock",0)
			frm.set_value("due_date","")
		}
	},
	service_note: function(frm) {
		if (frm.doc.service_note){
			// frm.events.refresh(frm)
			frm.set_df_property("farmer", "hidden", 0);
			frm.set_value("customer_or_farmer","Farmer")
			frm.set_df_property("customer_or_farmer", "hidden", 1);
			frm.set_df_property("customer", "read_only", 1);
			frm.set_df_property("cash_payment", "hidden", 1);
			refresh_field("customer_or_farmer");
			refresh_field("farmer");
		}
		else{

			frm.set_df_property("customer", "read_only", 0);
			frm.set_value("customer","")
			frm.set_df_property("farmer", "hidden", 1);
			frm.set_df_property("effective_credit", "hidden", 1);
			frm.set_df_property("cash_payment", "hidden", 1);
		}
	},

	farmer: function(frm){
		if(frm.doc.farmer){
			set_farmer_config(frm)
		}
	},

	customer_or_farmer: function(frm) {
		if(frm.doc.customer_or_farmer == "Vlcc Local Customer"){
			frm.set_value("effective_credit","")
			local_sale_operations(frm)
			frm.set_value("multimode_payment", 0);
			frm.trigger("multimode_payment")
			refresh_many(["multimode_payment", "effective_credit"])
		}else if (frm.doc.customer_or_farmer == "Farmer"){
			set_farmer_config(frm)
		}
	},

	cash_payment: function(frm) {
		if(frm.doc.cash_payment) {
			frm.set_value("multimode_payment", 0);
			refresh_field("multimode_payment")
			frm.trigger("multimode_payment");
		}
	},

	multimode_payment: function(frm) {
		if(!frm.doc.multimode_payment) {
			frm.set_value("by_cash", 0.00);
			frm.set_value("by_credit", 0.00);
			refresh_many(["by_cash", "by_credit"])
		}
		else {
			frm.set_value("cash_payment", 0);
			refresh_field("cash_payment")
		}
	},

	by_cash: function(frm) {
		frm.events.calculate_cash_or_credit(frm, "by_cash");
	},

	by_credit: function(frm) {
		frm.events.calculate_cash_or_credit(frm, "by_credit");
	},

	calculate_cash_or_credit: function(frm, field) {
		trigger_map = {"by_cash": "by_credit", "by_credit": "by_cash"}
		if(frm.doc[field] > frm.doc.grand_total) {
			frm.set_value(field, 0.00);
			refresh_field(field)
			frappe.msgprint(__("<b>{0}</b> must be less than or equal to Grand Total", [frappe.model.unscrub(field)]))
		}
		else {
			frm.set_value(trigger_map[field], frm.doc.grand_total - frm.doc[field])
			refresh_field(trigger_map[field])
		}
	},

	validate: function(frm) {
		frm.events.validate_multimode_payment(frm);
	},

	validate_multimode_payment: function(frm) {
		multimode_amt = frm.doc.by_cash + frm.doc.by_credit
		if(frm.doc.multimode_payment && (frm.doc.grand_total != multimode_amt)) {
			frappe.throw("Sum of By Cash and By credit must be equal to Grand Total")
		}
	}
})

local_sale_operations = function(frm){
	if(frm.doc.customer_or_farmer == "Vlcc Local Customer"){
		frappe.call({
			args: { "company": frm.doc.company },
			method: "dairy_erp.customization.sales_invoice.sales_invoice.get_local_customer",
			callback: function(r) {
				if(r.message) {
					frm.set_value("customer",r.message.customer)
					frm.set_value("total_cow_milk_qty",r.message.cow_milk)
					frm.set_value("total_buffalo_milk_qty",r.message.buff_milk)
				}
			}
		})
	}
}

set_farmer_config = function(frm) {
	if(frm.doc.farmer){
		frappe.call({
			args: { "farmer": frm.doc.farmer, "invoice": frm.doc.name },
			method: "dairy_erp.customization.sales_invoice.sales_invoice.get_farmer_config",
			callback: function(r) {
				if(r.message){
					frm.set_value("customer",r.message.customer)
					frm.set_value("total_cow_milk_qty",r.message.cow_milk)
					frm.set_value("total_buffalo_milk_qty",r.message.buff_milk)
					frm.set_value("effective_credit",r.message.eff_credit)
				}
			}
		})
	}
}
	
set_warehouse= function() {
	frappe.call({
		method:"dairy_erp.customization.sales_invoice.sales_invoice.get_wrhous",
		callback: function(r) {
			if(r.message) {
				$.each(cur_frm.doc.items,function(i,d){
					frappe.model.set_value(d.doctype, d.name, "warehouse",r.message)
				})
			}
		}
	});
}

get_session_user_type = function() {
	var user;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "User",
			filters: {"name": frappe.session.user},
			fieldname: ["operator_type","company"]
		},
		async:false,
		callback: function(r){
			if(r.message){	
				user = {
					"operator_type": r.message.operator_type,
					"company": r.message.company
				}		
			}
		}
	});

	return user
}

get_session_user_type = function() {
	var user;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "User",
			filters: {"name": frappe.session.user},
			fieldname: ["operator_type","company"]
		},
		async:false,
		callback: function(r){
			if(r.message){	
	
				user = {
					"operator_type": r.message.operator_type,
					"company": r.message.company
				}		
			}
		}
	});

	return user
}

$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));
