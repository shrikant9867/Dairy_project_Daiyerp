frappe.pages['dairy-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dairy Dashboard',
		single_column: true
	});

	wrapper.dashboard = new dashboard(wrapper)

}

dashboard = Class.extend({
	init : function(wrapper){
		var me = this;
		this.wrapper = wrapper;
		this.page = wrapper.page
		this.render_view()
	},
	render_view : function(){
		var me = this;
		$(frappe.render_template("dairy_dashboard")).appendTo(me.page.main);
		$(me.page.main).find(".new_add").on("click",function(){
			frappe.new_doc("Address")
		})
		$(me.page.main).find("#new_vlcc").on("click",function(){
			frappe.new_doc("Vlcc")
		})
		$(me.page.main).find("#new_supp").on("click",function(){
			frappe.new_doc("Supplier")
		})
		me.render_address()
	},
	render_address : function(){
		var me = this;
		frappe.call({
			method:"dairy_erp.dairy_erp.page.dairy_dashboard.dairy_dashboard.get_address"
		})
	}
})