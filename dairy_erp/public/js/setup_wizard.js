frappe.provide("dairy_erp.setup");

frappe.pages['setup-wizard'].on_page_load = function(wrapper) {
	if(frappe.sys_defaults.company) {
		frappe.set_route("desk");
		return;
	}
};

frappe.setup.on("before_load", function () {
	console.log("inside before_load dairy_erp")
	dairy_erp.setup.slides_settings.map(frappe.setup.add_slide);
});

dairy_erp.setup.slides_settings = [
	{
		// Domain
		name: 'dairy_erp_configuration',
		domains: ["all"],
		title: __('Dairy configuration'),
		fields: [
			{
					fieldtype: 'Check',
					fieldname: 'is_dropship',
					label: __('Dropship Only'),
					default: 0
			},
			{
					fieldtype: 'Check',
					fieldname: 'is_material_request_item_editable',
					label: __('Is Material Request Item Editable'),
					default: 0,
					description:__('After Enabling CheckBox, VLCC and Camp Office user cannot edit quantity and cannot delete a row in item table having a reference of Material Indent.')
			}
		]
	}

];

console.log("dairy_erp.setup.slides_settings",dairy_erp.setup.slides_settings)
