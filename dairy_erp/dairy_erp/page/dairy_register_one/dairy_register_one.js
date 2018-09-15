{% include "dairy_erp/public/js/openpdf.js" %}

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
            freeze: true,
            freeze_message: __("Loading... Please Wait"),
            callback: function(r){
                if(r.message){
                	console.log("inside callback",r.message)
                    me.table_data = r.message.final_dict
                    me.vlcc_addr = r.message.vlcc_details.vlcc_addr
                    me.vlcc = r.message.vlcc_details.vlcc
                    $(me.page).find(".render-table").empty();
                    me.print = frappe.render_template("dairy_register_one",{
                            "fmcr_data":me.table_data
                            })
                    $(me.page).find(".render-table").append(me.print)
                    me.update_diff();
                }
            }
        })
    },
    update_diff:function(){
        var me = this;
        /*console.log($(me.page).find('[data-fieldname="g_fat"]'),"g_fatttttttt")
        var regExp = /[a-z]/i;
        $(me.page).find('[data-fieldname="g_fat"]').change(function(){
            console.log("insdie my conde",$(me.page).find('[data-fieldname="g_fat"]').val())
            value = $(me.page).find('[data-fieldname="g_fat"]').val()
            if (regExp.test(value)) {
                $(me.page).find('[data-fieldname="g_fat"]').val("")
            }
        })*/
        $(me.page).find('#update_diff').click(function(){
            var g_fat = $(me.page).find('.g_fat')
            var g_snf = $(me.page).find('.g_snf')
            $.each(g_fat,function(i,d){
                var f_id = $(d).attr('row_id').split('@')[0]
                var g_fat_val = $(d).find('[data-fieldname="g_fat"]').val()
                if(in_list(Object.keys(me.table_data),f_id) && g_fat_val){
                    var diff_fat = flt(g_fat_val - me.table_data[f_id].vmcr_fat,2)
                    me.table_data[f_id].diff_fat = isNaN(diff_fat) ? 0 : diff_fat
                    me.table_data[f_id].g_fat = g_fat_val
                }
            })
            $.each(g_snf,function(i,d){
                var s_id = $(d).attr('row_id').split('@')[0]
                var g_snf_val = $(d).find('[data-fieldname="g_snf"]').val()
                if(in_list(Object.keys(me.table_data),s_id) && g_snf_val){
                    diff_snf = flt(g_snf_val - me.table_data[s_id].vmcr_snf,2)
                    me.table_data[s_id].diff_snf = isNaN(diff_snf) ? 0 : diff_snf
                    me.table_data[s_id].g_snf = g_snf_val
                }
            })
            $(me.page).find(".render-table").empty();
            me.print = frappe.render_template("dairy_register_one",{
                    "fmcr_data":me.table_data
                    })
            $(me.page).find(".render-table").append(me.print)
            me.update_diff();
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
        me.wrapper_page.set_primary_action(__("Print"), function () {
            me.create_pdf()
        })
        me.wrapper_page.set_secondary_action(__("Refresh"),function() { 
            window.location.reload();
        })
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
    },
    create_pdf: function(){
        var me = this;
        var base_url = frappe.urllib.get_base_url();
        var print_css = frappe.boot.print_css;
        var html = frappe.render_template("dr_one",{
            content: frappe.render_template("dairy_register_one_print",{
                                                        'fmcr_data':me.table_data,
                                                        'start_date':me.start_date.get_value(),
                                                        'end_date':me.end_date.get_value(),
                                                        'vlcc_addr':me.vlcc_addr,
                                                        'vlcc':me.vlcc
                                                    }),
            title:__("dairy_register_one_"+frappe.datetime.str_to_user(frappe.datetime.get_today())),
            base_url: base_url,
            print_css: print_css
        });
        open_pdf(html)
    }
})