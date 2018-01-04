frappe.pages['vlcc-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'VLCC Dashboard',
		single_column: true
	});
	wrapper.vlcc_dashboard = new vlcc_dashboard(wrapper)
}

vlcc_dashboard =  Class.extend({
	init: function(wrapper){
		console.log("**")
		var me= this;
		this.wrapper = wrapper;
		this.page = wrapper.page
		this.render_view();
	},
	render_view: function(){
		var me = this;
		$(frappe.render_template("vlcc_dashboard")).appendTo(me.page.main);
 	},
})