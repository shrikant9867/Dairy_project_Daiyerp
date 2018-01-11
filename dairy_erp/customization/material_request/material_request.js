frappe.ui.form.on('Material Request', {
	refresh: function(frm) {
		var operator_type
		frappe.call({
			method: "frappe.client.get_value",
			async : false,
			args: {
				doctype: "User",
				filters: {"name": frappe.session.user},
				fieldname: ["operator_type","company"]
			},
			callback: function(r){
				if(r.message){
					operator_type = r.message.operator_type
					get_co(r.message.company)
				}
			}
		});
		/*if(!frm.doc.__islocal && frm.doc.docstatus == 1 && operator_type == 'Camp Office'){
			frm.add_custom_button(__("Make PO"), function() {
				make_dialog(frm)
			})
		}*/

	},
	onload : function (frm) {
		frm.set_query("camp_office", function () {
			return {
				"filters": {
					"address_type": "Camp Office",
				}
			};
		});

	}


})

get_co = function(company){
	frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Village Level Collection Centre",
				filters: {"name": company},
				fieldname: ["camp_office","warehouse"]
			},
			callback: function(r){
				if(r.message){
					cur_frm.set_value("camp_office",r.message.camp_office)
					$.each(cur_frm.doc.items,function(i,d){
						frappe.model.set_value(d.doctype, d.name, "warehouse", r.message.warehouse);
					})
				}
			}
	});
}

make_dialog = function(frm){
	var dialog = new frappe.ui.Dialog({
	title: __("PO Details"),
	fields: [
		{
			"label": __("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"reqd": 1
		},
		{
			"label": __("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"label": __("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"reqd": 1
		},
		{
			"label": __("Taxes and Charges"),
			"fieldname": "taxes_and_charges",
			"fieldtype": "Link",
			"options": "Purchase Taxes and Charges Template"
		},
	]
});
	dialog.set_primary_action(__("Submit"), function() {
		frappe.call({
			method:"dairy_erp.customization.material_request.material_request.make_po",
			args:{
				"data":dialog.get_values(),
				"doc":frm.doc
			},
			callback:function(r){
			}
		})

	})
	dialog.hide()
	dialog.show()

}