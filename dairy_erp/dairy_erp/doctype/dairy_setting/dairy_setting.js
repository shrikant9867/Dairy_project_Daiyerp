// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dairy Setting', {
	refresh: function(frm) {

	},
	onload_post_render: function(frm){
		frm.get_field("add_multi_vlcc").$input.addClass("btn-primary");
	},
	add_multi_vlcc:function(frm){
		if(frm.doc.upload_vlcc){
		return new Promise(function(resolve, reject) {
			frappe.confirm("Are you sure, you want to import Multiple Society Records? It will take a Time as number of Records" ,function() {
				var negative = 'frappe.validated = false';
				frm.events.get_csv(frm)
				resolve(negative);
			},
				function() {
					reject();
				})
			})
		}else{
			frappe.throw("Please upload file first")
		}
	},
	get_csv: function(frm) {
		frappe.call({
				method:"dairy_erp.dairy_erp.doctype.dairy_setting.dairy_setting.get_csv",
				args: {"doc":frm.doc},
				freeze: true,
            	freeze_message: __("Loading... Please Wait"),
				callback: function(r){
					window.reload();
					if(r.message) {

					}
				}
			})
	},
	
});
