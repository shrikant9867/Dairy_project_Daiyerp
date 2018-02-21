console.log("jai hind")
frappe.ui.form.on("Sales Invoice", {
	validate: function(frm) {
		// if (frm.doc.local_sale && cint(frm.doc.effective_credit) == 0){
		// 	frappe.throw(_("Not permitted"))
		// }
	},

	refresh: function(frm) {
		// set_warehouse()

	},

	onload: function(frm) {
		frm.set_value("effective_credit","")
		user_ = get_session_user_type()
		console.log("#########",user_)
		if(user_.operator_type != "VLCC"){
			cur_frm.set_df_property('local_sale', 'hidden', 1);
			// cur_frm.set_df_property('due_date', 'hidden', 1);

		}
		//Prashant Code
		if(user_.operator_type != "Vet AI Technician" ){
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
			frm.set_df_property("customer", "read_only", 0);
			frm.set_df_property("due_date", "read_only", 0);
			frm.set_value("update_stock",0)
			frm.set_value("due_date","")
		}
	},

	service_note: function(frm) {
		if (frm.doc.service_note){
			console.log("######service_note")
			// frm.set_df_property("customer", "read_only", 1);
			
		}
		
	},

	farmer: function(frm){
		if(frm.doc.farmer){
			set_farmer_config(frm)
		}
	},
	customer_or_farmer: function(frm) {
		if(frm.doc.customer_or_farmer == "Vlcc Local Customer"){
			console.log("#######")
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
					console.log("###",r.message)
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
	console.log("$$")
	frappe.call({
			args: {
				"farmer": frm.doc.farmer
			},
			method: "dairy_erp.customization.sales_invoice.sales_invoice.get_farmer_config",
			callback: function(r) {
				if(r.message){
					console.log("###ff",r.message)
					frm.set_value("customer",r.message.customer)
					frm.set_value("total_cow_milk_qty",r.message.cow_milk)
					frm.set_value("total_buffalo_milk_qty",r.message.buff_milk)
					frm.set_value("effective_credit",r.message.eff_credit)
				}
				// cur_frm.reload_doc();
			}
		})
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

cur_frm.fields_dict.customer.get_query = function(doc) {
	return {filters: {company: doc.company}}
}