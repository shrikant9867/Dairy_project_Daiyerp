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
        this.set_fields()
    },
    render_layout: function(date) {
    	var me = this;
        frappe.call({
            method: "dairy_erp.dairy_erp.page.daily_milk_purchase.daily_milk_purchase.get_data",
            args: {
                "curr_date":date
            },
            callback: function(r){
                if(r.message){
                    $(me.page).find(".render-table").empty();
    				$(me.page).find(".render-table").append(frappe.render_template("daily_milk_purchase",{
                            "data":r.message.fmcr_data,
                            "count_data":r.message.data,
                            "local_sale":r.message.local_sale
                            })
                        )
    			}
                else{
                    $(me.page).find(".render-table").empty();
                    __html = "<h1 class='render-table' style='padding-left: 25px;'>Record Not Found</h1>"
                    me.page.find(".render-table").append(__html)
                }
    		}
    	})
    },
    set_fields:function(){
        var me = this;
        html = `<div class='row'>
                    <div class='col-xs-3 date-field' style='padding-left: 48px;'></div>\
                </div>
                <div class='row'>
                    <div class='col-xs-12 render-table'></div>
                </div>`
        me.page.html(html)
        me.curr_date = frappe.ui.form.make_control({
            parent: me.page.find(".date-field"),
            df: {
            fieldtype: "Date",
            label:__("Date"),
            fieldname: "curr_date",
            placeholder: __("Date"),
                onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.curr_date.get_value()) {
                        me.curr_date_change(me.curr_date.get_value())
                    }
                }
            },
            render_input: true
        });
        me.curr_date.set_value(frappe.datetime.str_to_obj(frappe.datetime.get_today()))
        me.wrapper_page.set_primary_action(__("Refresh"),function() { 
            window.location.reload();
        })
    },
    curr_date_change: function(date){
        var me =this;
            $(me.page).find(".render-table").empty();
            me.render_layout(date);
    }
})