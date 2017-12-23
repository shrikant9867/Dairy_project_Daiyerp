frappe.ui.form.on('Material Request', {
	refresh: function(frm) {
		if(!frm.doc.__islocal && frm.doc.docstatus == 1){
			frm.add_custom_button(__("Make PO"), function() {
				make_dialog(frm)
			})
		}

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