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
		title: __('Select your Configration'),
		fields: [
			{
				fieldname: 'dairy_type', label: __('Dairy Type'), fieldtype: 'Select',
				options: [
					{ "label": __("Distribution"), "value": "Distribution" },
					{ "label": __("Manufacturing"), "value": "Manufacturing" },
					{ "label": __("Retail"), "value": "Retail" },
					{ "label": __("Services"), "value": "Services" },
					{ "label": __("Education (beta)"), "value": "Education" },
					{"label": __("Healthcare (beta)"), "value": "Healthcare"}
				], reqd: 1
			},
			{
					fieldtype: 'Check',
					fieldname: 'custom_column1',
					label: __('Advance And Loan'),
					default: 0
			},
			{
					fieldtype: 'Check',
					fieldname: 'custom_column2',
					label: __('BMC'),
					default: 0
			},
			{
					fieldtype: 'Check',
					fieldname: 'custom_column3',
					label: __('Net Off Report'),
					default: 0
			}
		],
		// help: __('Select the nature of your business.'),
		onload: function (slide) {
			console.log("inside slides_settings dairy_erp",slide)
			slide.get_input("dairy_type").on("change", function () {
				frappe.setup.dairy_type = $(this).val();
				frappe.wizard.refresh_slides();
			});
		}
	}

];

console.log("dairy_erp.setup.slides_settings",dairy_erp.setup.slides_settings)
