// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Price List', {
	refresh: function(frm) {
		var template = ['GTVLCCB','GTFS','GTCS','GTCOVLCCB','GTCOB','GTCOS','LCOVLCCB']
		// var local_template = ['LVLCCB','LFS','LCS','LCOB','LCOS']
		if (!in_list(frappe.user_roles,"Dairy Manager") && !frm.doc.__islocal){
			if (in_list(template,frm.doc.price_list)){
				frm.set_df_property("price_template_type", "read_only",1);
				frm.set_df_property("operator_name", "read_only",1);
				frm.set_df_property("items", "read_only",1);
				frm.set_df_property("price_list_template", "hidden",1);	
			}
		}
		else if(in_list(frappe.user_roles,"Dairy Manager") && !frm.doc.__islocal){
			if (frm.doc.price_list == 'GTCOVLCCB'){
				frm.set_df_property("price_template_type", "read_only",1);
				frm.set_df_property("operator_name", "read_only",1);
				frm.set_df_property("items", "read_only",1);
				frm.set_df_property("price_list_template", "hidden",1);	
			}
		}
	/*	if(!in_list(frappe.user_roles,"Dairy Operator") && !frm.doc.__islocal){
			console.log("kjdgfhdj")
			if (in_list(template,frm.doc.price_list)){
				frm.set_df_property("price_template_type", "read_only",1);
				frm.set_df_property("operator_name", "read_only",1);
				frm.set_df_property("items", "read_only",1);
				frm.set_df_property("price_list_template", "hidden",1);	
			}

		}*/
		if(frm.doc.__islocal && (in_list(frappe.user_roles,"Dairy Manager") || in_list(frappe.user_roles,"Dairy Operator"))){
			frm.set_df_property("price_list_template", "hidden",1);	
		}
		if(has_common(frappe.user_roles, ["Camp Operator", "Camp Manager"])) {
			frm.set_df_property("price_template_type", "options", [' ','Dairy Supplier','CO to VLCC']);
		}
		else if(has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager"])) {
			frm.set_df_property("price_template_type", "options", [' ','VLCC Local Supplier','VLCC Local Farmer','VLCC Local Customer']);
		}

	},
	price_template_type: function(frm) {
		if(cur_frm.doc.price_template_type == "CO to VLCC"){
			frm.set_value("selling",1)
			frm.set_value("buying",0)
		}
		else if(cur_frm.doc.price_template_type == "Dairy Supplier"){
			frm.set_value("buying",1)
			frm.set_value("selling",0)
		}
		else if(cur_frm.doc.price_template_type == "VLCC Local Supplier"){
			frm.set_value("buying",1)
			frm.set_value("selling",0)
		}
		else if(cur_frm.doc.price_template_type == "VLCC Local Farmer"){
			frm.set_value("buying",0)
			frm.set_value("selling",1)
		}
		else if(cur_frm.doc.price_template_type == "VLCC Local Customer"){
			frm.set_value("buying",0)
			frm.set_value("selling",1)
		}
	},
	price_list_template: function(frm){
		if (frm.doc.price_list_template) {
			frappe.call({
				method: "dairy_erp.dairy_erp.doctype.material_price_list.material_price_list.get_template",
				args: {
					"template": frm.doc.price_list_template
				},
				callback: function(r) {
					frm.set_value("items" ,"");
					if (r.message) {
						$.each(r.message.items, function(i, d) {
							var row = frappe.model.add_child(cur_frm.doc, "Material Price", "items");
							row.item = d.item;
							row.item_name = d.item_name;
							row.price = d.price;
						});
					}
					refresh_field("items");
				}
			});
		};
		// frm.set_value("items" ,"");

	},
	onload: function(frm){
		if(has_common(frappe.user_roles, ["Camp Operator", "Camp Manager"])) {
			frm.set_query("price_list_template", function () {
				return {
					"filters": {
						"price_list": ["in",["GTCOB","GTCOS"]],
					}
				};
			});
		}
		else if (has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager"])) {
			frm.set_query("price_list_template", function () {
				return {
					"filters": {
						"price_list": ["in",["GTVLCCB","GTCS","GTFS"]],
					}
				};
			});
		}
	}
});


cur_frm.fields_dict['items'].grid.get_field("item").get_query = function(doc, cdt, cdn) {

	var item_list = []
	for(var i = 0 ; i < cur_frm.doc.items.length ; i++){
		if(cur_frm.doc.items[i].item){
			item_list.push(cur_frm.doc.items[i].item);
		}
	}
	return {
	filters: [
			['Item', 'name', 'not in', item_list]
		]
	}
}

