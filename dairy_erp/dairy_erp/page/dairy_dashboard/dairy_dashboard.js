frappe.pages['dairy-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dairy Dashboard',
		single_column: true
	});

	$(frappe.render_template("dairy_dashboard")).appendTo(page.main);

}