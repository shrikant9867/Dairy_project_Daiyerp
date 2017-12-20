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
		this.render_address()
	},
	render_address : function(){
		var me = this;
		frappe.call({
			method:"dairy_erp.dairy_erp.page.dairy_dashboard.dairy_dashboard.get_data",
			callback : function(r){
				me.data = r.message
				me.render_view()
			}
		})
	},
	render_view : function(){
		var me = this;
		$(frappe.render_template("dairy_dashboard",{"data":me.data || {}})).appendTo(me.page.main);
		$.each(me.data.addr,function(i,d){
				if(d && d.address_type == "Head Office"){
					$('#head-office').hide()
				}
		})
		$(me.page.main).find("#head-office").on("click",function(){
			frappe.route_options = {
				"address_type": "Head Office"
			};
			frappe.new_doc("Address")
		})
		$(me.page.main).find("#camp-office").on("click",function(){
			frappe.route_options = {
				"address_type": "Camp Office"
			};
			frappe.new_doc("Address")
		})
		$(me.page.main).find("#chilling-centre").on("click",function(){
			frappe.route_options = {
				"address_type": "Chilling Centre"
			};
			frappe.new_doc("Address")
		})
		$(me.page.main).find("#plant").on("click",function(){
			frappe.route_options = {
				"address_type": "Plant"
			};
			frappe.new_doc("Address")
		})
		$(me.page.main).find("#new_vlcc").on("click",function(){
			frappe.new_doc("Village Level Collection Centre")
		})
		$(me.page.main).find("#new_supp").on("click",function(){
			frappe.route_options = {
				"supplier_type": "Dairy Local"
			};
			frappe.new_doc("Supplier")
		})
		$(me.page.main).find(".camp-office").on("click",function(){
			frappe.set_route("List", "Address", {'address_type': "Camp Office"});
		})
		$(me.page.main).find(".head-office-list").on("click",function(){
			frappe.set_route("List", "Address", {'address_type': "Head Office"});
		})
		$(me.page.main).find(".chilling-centre").on("click",function(){
			frappe.set_route("List", "Address", {'address_type': "Chilling Centre"});
		})	
		$(me.page.main).find(".plant").on("click",function(){
			frappe.set_route("List", "Address", {'address_type': "Plant"});
		})
		$(me.page.main).find(".supplier-list").on("click",function(){
			frappe.set_route("List", "Supplier", {'supplier_type': "Dairy Local"});
		})	
		
	}
})