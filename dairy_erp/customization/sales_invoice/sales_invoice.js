console.log("jai hind")
frappe.ui.form.on("Sales Invoice", {
	setup: function(frm){


	},
	validate: function(frm) {
		// if (frm.doc.local_sale && cint(frm.doc.effective_credit) == 0){
		// 	frappe.throw(_("Not permitted"))
		// }
	},

	refresh: function(frm) {
		// Service Note
		
		
	},

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
			console.log("****")
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

			// Tring Item-code filter  for service note using set_query
			// item_names = []
			// frappe.call({
			// 		method:"dairy_erp.customization.sales_invoice.sales_invoice.get_servicenote_item",
			// 		callback: function(r) {
			// 			if(r.message) {
			// 				for (i = 0;i < r.message.length ;i++){
			// 					item_names.push(r.message[i][0])
			// 				}
			// 				console.log("item_names",item_names);
			// 				cur_frm.fields_dict['items'].grid.get_field("item_code").set_query = function(){
			// 					return {
			// 							filters: [
			// 									['Item', 'item_code', 'in', item_names],
			// 							]
			// 					}
			// 				}

			// 			}
			// 		}		
			// })

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
		}else if (frm.doc.customer_or_farmer == "Farmer"){
			set_farmer_config(frm)
			
			
		}
	}
})

local_sale_operations = function(frm){
	if(frm.doc.customer_or_farmer == "Vlcc Local Customer"){
		frappe.call({
			args: {
				"company": frm.doc.company
			},
			method: "dairy_erp.customization.sales_invoice.sales_invoice.get_local_customer",
			callback: function(r) {
				if(r.message){
					frm.set_value("customer",r.message.customer)
					frm.set_value("total_cow_milk_qty",r.message.cow_milk)
					frm.set_value("total_buffalo_milk_qty",r.message.buff_milk)
				}
				// cur_frm.reload_doc();
			}
		})
	}

}

set_farmer_config = function(frm) {
	if(frm.doc.farmer){
		frappe.call({
				args: {
					"farmer": frm.doc.farmer
				},
				method: "dairy_erp.customization.sales_invoice.sales_invoice.get_farmer_config",
				callback: function(r) {
					if(r.message){
						frm.set_value("customer",r.message.customer)
						frm.set_value("total_cow_milk_qty",r.message.cow_milk)
						frm.set_value("total_buffalo_milk_qty",r.message.buff_milk)
						frm.set_value("effective_credit",r.message.eff_credit)
					}
					// cur_frm.reload_doc();
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


// // Tring Item-code filter  for service note using get_query
// cur_frm.fields_dict['items'].grid.get_field("item_code").get_query = function(doc, cdt, cdn) {
// 	return {
// 		query: "dairy_erp.customization.sales_invoice.sales_invoice.get_service_note_item",
// 		filters:{
// 				"service_note": cur_frm.doc.service_note,
// 		}
// 	}

// }

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
