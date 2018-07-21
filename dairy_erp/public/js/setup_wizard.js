frappe.provide("dairy_erp.setup");

frappe.pages['setup-wizard'].on_page_load = function(wrapper) {
	if(frappe.sys_defaults.company) {
		frappe.set_route("desk");
		return;
	}
};

frappe.setup.on("before_load", function () {
	dairy_erp.setup.slides_settings.map(frappe.setup.add_slide);
});

dairy_erp.setup.slides_settings = [
	{
		// Domain
		name: 'dairy_erp_configration',
		domains: ["all"],
		title: __('Select your Configration'),
		fields: [
			{
				fieldname: 'domain', label: __('Domain'), fieldtype: 'Select',
				options: [
					{ "label": __("Distribution"), "value": "Distribution" },
					{ "label": __("Manufacturing"), "value": "Manufacturing" },
					{ "label": __("Retail"), "value": "Retail" },
					{ "label": __("Services"), "value": "Services" },
					{ "label": __("Education (beta)"), "value": "Education" },
					{"label": __("Healthcare (beta)"), "value": "Healthcare"}
				], reqd: 1
			},
		],
		// help: __('Select the nature of your business.'),
		onload: function (slide) {
			slide.get_input("domain").on("change", function () {
				frappe.setup.domain = $(this).val();
				frappe.wizard.refresh_slides();
			});
		},
	}
];
