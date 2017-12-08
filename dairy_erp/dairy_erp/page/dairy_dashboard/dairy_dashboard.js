frappe.pages['dairy-dashboard'].on_page_load = function(wrapper) {
	new frappe.dairy({
		$wrapper: $(wrapper)
	});
	frappe.breadcrumbs.add("Dairy Erp");
}

frappe.dairy = Class.extend({
	
	init: function(opts){
		this.$wrapper = opts.$wrapper
		this.render_layout();
	},
	render_layout: function(){
		this.$wrapper.empty();
		this.$wrapper.append(frappe.render_template("dairy_dashboard"));
	}
})
