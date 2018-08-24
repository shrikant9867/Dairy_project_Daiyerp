frappe.pages['dairy_register_one'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dairy Register - 1',
		single_column: true
	});
	new frappe.dairy_register_one(wrapper);
    frappe.breadcrumbs.add("Dairy Erp");
}

frappe.dairy_register_one = Class.extend({
    init : function(wrapper){
        var me = this;
        this.wrapper_page = wrapper.page;
        this.page = $(wrapper).find('.layout-main-section');
        this.wrapper = $(wrapper).find('.page-content');
        this.set_filters();
    },
    render_layout: function(_start_date,_end_date) {
        var me = this;
        frappe.call({
            method: "dairy_erp.dairy_erp.page.dairy_register_one.dairy_register_one.get_fmcr_data",
            args: {
                "start_date":_start_date,
                "end_date":_end_date
            },
            callback: function(r){
                if(r.message){
                	console.log("inside callback",r.message)
                    me.table_data = r.message
                    $(me.page).find(".render-table").empty();
                    me.print = frappe.render_template("dairy_register_one",{
                            "fmcr_data":me.table_data
                            })
                    $(me.page).find(".render-table").append(me.print)
                }
            }
        })
    },
    set_filters:function(){
        var me = this;
        html = `<div class='row'>
                    <div class='col-xs-3 start-date-field' style='padding-left: 48px;'></div>\
                    <div class='col-xs-3 end-date-field' style='padding-left: 48px;'></div>\
                </div>
                <div class='row'>
                    <div class='col-xs-12 render-table'></div>
                </div>`
        me.page.html(html)
    	me.start_date = frappe.ui.form.make_control({
            parent: me.page.find(".start-date-field"),
            df: {
            fieldtype: "Date",
            label:__("Start Date"),
            fieldname: "start_date",
            placeholder: __("Start Date"),
                onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.start_date.get_value()) {
                        me.start_date_change(me.start_date.get_value())
                    }
                }
            },
            render_input: true
        });
        me.start_date.set_value(frappe.datetime.str_to_obj(frappe.datetime.get_today()))
        me.end_date = frappe.ui.form.make_control({
            parent: me.page.find(".end-date-field"),
            df: {
            fieldtype: "Date",
            label:__("End Date"),
            fieldname: "end_date",
            placeholder: __("End Date"),
                onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.end_date.get_value()) {
                        me.end_date_change(me.end_date.get_value())
                    }
                }
            },
            render_input: true
        });
        me.end_date.set_value(frappe.datetime.str_to_obj(frappe.datetime.get_today()))
    },
    start_date_change: function(date_){
        var me =this;
        $(me.page).find(".render-table").empty();
        var _start_date = me.start_date.get_value() ? me.start_date.get_value() : ""
        var _end_date = me.end_date.get_value() ? me.end_date.get_value() : ""
        me.render_layout(_start_date,_end_date);
    },
    end_date_change: function(date_){
        var me =this;
        $(me.page).find(".render-table").empty();
        var _start_date = me.start_date.get_value() ? me.start_date.get_value() : ""
        var _end_date = me.end_date.get_value() ? me.end_date.get_value() : ""
        me.render_layout(_start_date,_end_date);
    }
})        


