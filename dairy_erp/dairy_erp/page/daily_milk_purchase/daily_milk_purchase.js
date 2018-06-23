frappe.pages['daily-milk-purchase'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Daily Milk Purchase Report',
		single_column: true
	});
 	new frappe.daily_milk_purchase(wrapper);
    frappe.breadcrumbs.add("Dairy Erp");
}

frappe.daily_milk_purchase = Class.extend({
    init : function(wrapper){
    	var me = this;
		this.wrapper_page = wrapper.page;
		this.page = $(wrapper).find('.layout-main-section');
		this.wrapper = $(wrapper).find('.page-content');
        this.render_layout();
    },
    render_layout: function() {
    	var me = this;
    	frappe.call({
    		method: "dairy_erp.dairy_erp.page.daily_milk_purchase.daily_milk_purchase.get_data",
    		callback: function(r){
    			if(r.message){
    				console.log(r.message.count)
    				me.page.html(frappe.render_template("daily_milk_purchase",{"data":r.message.fmcr_data,"count_data":r.message.count}))
    			}
    		}
    	})
    }
})