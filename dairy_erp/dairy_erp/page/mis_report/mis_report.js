{% include "dairy_erp/public/js/openpdf.js" %}

frappe.pages['mis_report'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'MIS Report',
		single_column: true
	});
	new frappe.mis_report(wrapper);
    frappe.breadcrumbs.add("Dairy Erp");
}

frappe.mis_report = Class.extend({
    init : function(wrapper){
        var me = this;
        this.wrapper_page = wrapper.page;
        this.page = $(wrapper).find('.layout-main-section');
        this.wrapper = $(wrapper).find('.page-content');
        this.set_filters();
    },
    render_layout: function(month_,fiscal_year_) {
        var me = this;
        frappe.call({
            method: "dairy_erp.dairy_erp.page.mis_report.mis_report.get_mis_data",
            args: {
                "month":month_,
                "fiscal_year":fiscal_year_
            },
            async:false,
            callback: function(r){
                if(r.message){
                	console.log("inside callback",r.message)
                    me.mis_data = r.message.milk_purchase_dict
                    me.member_data = r.message.member_data
                    me.milk_quality = r.message.milk_quality
                    $(me.page).find(".render-table").empty();
                    me.print = frappe.render_template("mis_report",{
                            "mis_data":me.mis_data,
                            "member_data":me.member_data,
                            "milk_quality":me.milk_quality
                            })
                    $(me.page).find(".render-table").append(me.print)
                    me.update_total_milk()
                }
            }
        })
    },
    update_total_milk:function() {
        var me = this;
        console.log($(me.page).find(".good_milk").html(),"total milk___________")
        console.log("insdie update_total_milk",$(me.page).find('[data-fieldname="update_total_milk"]'))
        $(me.page).find('[data-fieldname="update_total_milk"]').click(function(){
            if($(me.page).find('[data-fieldname="formated_milk"]').val()){
                console.log($(me.page).find('[data-fieldname="formated_milk"]').val())
                var milk_data =  {"formated_milk":$(me.page).find('[data-fieldname="formated_milk"]').val(),
                             "good_milk":$(me.page).find(".good_milk").html(),
                             "bad_milk":$(me.page).find(".bad_milk").html(),
                             "total_milk":$(me.page).find(".total_milk").html()
                            }
                me.add_formated_milk(milk_data);
            }
            else{
                frappe.throw(__("Please Add Formated Milk Qty"))
            }
        })
    },
    add_formated_milk:function(milk_data){
        var me = this;
        console.log("inside add_formated_milk",milk_data)
        frappe.call({
            method: "dairy_erp.dairy_erp.page.mis_report.mis_report.add_formated_milk",
            args: {
                "filters": {
                    "milk_data":milk_data,
                    "vlcc":frappe.sys_defaults.company,
                    "month":me.month.get_value(),
                    "fiscal_year":me.fiscal_year.get_value()   
                }
            },
            callback: function(r){
                if(r.message){  
                    console.log(r.message)       
                }
            }
        });
    },
    set_filters:function(){
        var me = this;
        html = `<div class='row'>
                    <div class='col-xs-3 month-field' style='padding-left: 48px;'></div>\
                    <div class='col-xs-3 fiscal-year-field' style='padding-left: 48px;'></div>\
                </div>
                <div class='row'>
                    <div class='col-xs-12 render-table'></div>
                </div>`
        me.page.html(html)
    	me.month = frappe.ui.form.make_control({
            parent: me.page.find(".month-field"),
            df: {
	            fieldtype: "Select",
	            label:__("Month"),
	            fieldname: "month",
	            options:["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"],
	            placeholder: __("Month"),
	                onchange: function(){
	                    $(me.page).find(".render-table").empty();
	                    if(me.month.get_value()) {
	                        me.month_change(me.month.get_value())
	                    }
	                }
            },
            render_input: true
        });
        me.month.set_value("Apr")
        me.fiscal_year = frappe.ui.form.make_control({
            parent: me.page.find(".fiscal-year-field"),
            df: {
            fieldtype: "Link",
            label:__("Fiscal Year"),
            fieldname: "fiscal_year",
            options:"Fiscal Year",
            placeholder: __("End Date"),
                onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.fiscal_year.get_value()) {
                        me.fiscal_year_change(me.fiscal_year.get_value())
                    }
                }
            },
            render_input: true
        });
        me.fiscal_year.set_value(frappe.sys_defaults.fiscal_year)
        me.wrapper_page.set_primary_action(__("Print"), function () {
            me.create_pdf()
        })
        me.wrapper_page.set_secondary_action(__("Refresh"),function() { 
            window.location.reload();
        })
    },
    month_change: function(date_){
        var me =this;
        $(me.page).find(".render-table").empty();
        var month_ = me.month.get_value() ? me.month.get_value() : ""
        var fiscal_year_ = me.fiscal_year.get_value() ? me.fiscal_year.get_value() : ""
        me.render_layout(month_,fiscal_year_);
    },
    fiscal_year_change: function(date_){
        var me =this;
        $(me.page).find(".render-table").empty();
        var month_ = me.month.get_value() ? me.month.get_value() : ""
        var fiscal_year_ = me.fiscal_year.get_value() ? me.fiscal_year.get_value() : ""
        me.render_layout(month_,fiscal_year_);
    },
    create_pdf: function(){
        var me = this;
        var base_url = frappe.urllib.get_base_url();
        var print_css = frappe.boot.print_css;
        var html = frappe.render_template("mis_pdf",{
            content: frappe.render_template("mis_report",{
                                                        "mis_data":me.mis_data,
                                                        "member_data":me.member_data,
                                                        "milk_quality":me.milk_quality
                                                    }),
            title:__("dairy_register_two"+frappe.datetime.str_to_user(frappe.datetime.get_today())),
            base_url: base_url,
            print_css: print_css
        });
        open_pdf(html)
    }
})