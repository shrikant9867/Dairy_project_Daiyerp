frappe.pages['vlcc-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'VLCC Dashboard',
		single_column: true
	});
	wrapper.dashboard = new dashboard(wrapper)
}

dashboard = Class.extend({
	init:function(wrapper){
		var me = this;
		this.wrapper_page = wrapper.page;
		this.page = $(wrapper)
		this.wrapper = $(wrapper).find('.page-content');
		this.render_view()
	},
	render_view:function(){
		var me = this;
		html = `<div class='pie-chart'></div></div>`
		me.page.html(html)
		var __html = frappe.render_template("vlcc_dashboard")
		$(me.page).find(".pie-chart").empty();
		me.page.find(".pie-chart").append(__html)
	},
})