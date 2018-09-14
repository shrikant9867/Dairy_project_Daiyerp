{% include "dairy_erp/public/js/openpdf.js" %}

frappe.pages['smarterp_comparison_report'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'SmartAMCU - SmartERP Comparison Report',
		single_column: true
	});
	new frappe.smarterp_comparison_report(wrapper);
    frappe.breadcrumbs.add("Dairy Erp");
}

frappe.smarterp_comparison_report = Class.extend({
    init : function(wrapper){
        var me = this;
        this.wrapper_page = wrapper.page;
        this.page = $(wrapper).find('.layout-main-section');
        this.wrapper = $(wrapper).find('.page-content');
        this.set_filters();
    },
    render_layout: function() {
        var me = this;
        if (me.from_date.get_value() && me.to_date.get_value() && me.vlcc.get_value() && me.chilling_centre.get_value()){
            frappe.call({
                method: "dairy_erp.dairy_erp.page.smarterp_comparison_report.smarterp_comparison_report.get_data",
                args: {
                    "filters":{
                        "from_date":me.from_date.get_value(),
                        "to_date":me.to_date.get_value(),
                        "vlcc":me.vlcc.get_value(),
                        "cc":me.chilling_centre.get_value()
                    }
                },
                async:false,
                callback: function(r){
                    if(r.message){
                        console.log("inside callback",r.message)
                        me.amcu_data = r.message.final_dict
                        me.cc_vlcc_details = r.message.cc_vlcc_details
                        me.print = frappe.render_template("smarterp_comparison_report",{
                                "amcu_data":me.amcu_data,
                                "cc_vlcc_details":me.cc_vlcc_details
                                })
                        $(me.page).find(".render-table").append(me.print)
                    }
                }
            })
        }
    },
    set_filters:function(){
        var me = this;
        html = `<div class='row'>
                    <div class='col-xs-3 cc-field' style='padding-left: 48px;'></div>\
                    <div class='col-xs-3 vlcc-field' style='padding-left: 48px;'></div>\
                    <div class='col-xs-3 form-field' style='padding-left: 48px;'></div>\
                    <div class='col-xs-3 to-field' style='padding-left: 48px;'></div>\
                </div>
                <div class='row'>
                    <div class='col-xs-12 render-table'></div>
                </div>`
        me.page.html(html)
    	me.chilling_centre = frappe.ui.form.make_control({
            parent: me.page.find(".cc-field"),
            df: {
	            fieldtype: "Link",
	            label:__("Chilling Centre"),
	            fieldname: "address",
	            options:"Address",
	            placeholder: __("Chilling Centre"),
	            reqd:1,
	                onchange: function(){
	                    $(me.page).find(".render-table").empty();
	                    if(me.chilling_centre.get_value()) {
	                        me.cc_change(me.chilling_centre.get_value())
	                    }
	                },
					get_query: function () {
						return {
							"filters": {
								"address_type": "Chilling Centre"
								}
							}
					},
            },
            render_input: true
        });
    	me.vlcc = frappe.ui.form.make_control({
            parent: me.page.find(".vlcc-field"),
            df: {
	            fieldtype: "Link",
	            label:__("VLCC"),
	            fieldname: "vlcc",
	            options:"Village Level Collection Centre",
	            placeholder: __("VLCC"),
                reqd:1,
	                onchange: function(){
	                    $(me.page).find(".render-table").empty();
	                    if(me.vlcc.get_value()) {
	                        me.vlcc_change(me.vlcc.get_value())
	                    }
	                },
	                get_query: function () {
						return {
							"filters": {
								"chilling_centre": me.chilling_centre.get_value()
								}
							}
					}
            },
            render_input: true
        });
        me.from_date = frappe.ui.form.make_control({
            parent: me.page.find(".form-field"),
            df: {
            fieldtype: "Date",
            label:__("From Date"),
            fieldname: "from_date",
            placeholder: __("From Date"),
                onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.from_date.get_value()) {
                        me.from_date_change(me.from_date.get_value())
                    }
                }
            },
            render_input: true
        });
        me.from_date.set_value(frappe.datetime.str_to_obj(frappe.datetime.get_today()))
        me.to_date = frappe.ui.form.make_control({
            parent: me.page.find(".to-field"),
            df: {
            fieldtype: "Date",
            label:__("To Date"),
            fieldname: "to_date",
            placeholder: __("To Date"),
                onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.to_date.get_value()) {
                        me.to_date_change(me.to_date.get_value())
                    }
                }
            },
            render_input: true
        });
        me.to_date.set_value(frappe.datetime.str_to_obj(frappe.datetime.get_today()))
        me.wrapper_page.set_primary_action(__("Export"), function () {
            //me.create_pdf()
            me.make_export()
        })
        me.wrapper_page.set_secondary_action(__("Refresh"),function() { 
            window.location.reload();
        })
    },
    vlcc_change:function(){
    	var me = this;
    	$(me.page).find(".render-table").empty();
    	me.render_layout();
    },
    cc_change:function(){
    	var me = this;
    	$(me.page).find(".render-table").empty();
    	if(me.vlcc.get_value()){
            me.vlcc.set_value("")
        }
        me.render_layout();
    },
    from_date_change: function(date_){
        var me =this;
        $(me.page).find(".render-table").empty();
        me.render_layout();
    },
    to_date_change: function(date_){
        var me =this;
        $(me.page).find(".render-table").empty();
        me.render_layout();
    },
    create_pdf: function(){
        var me = this;
        console.log(me.cc_vlcc_details,"cc_vlcc_details")
        console.log("before print ")
        var base_url = frappe.urllib.get_base_url();
        var print_css = frappe.boot.print_css;
        var html = frappe.render_template("scr_pdf",{
            content: frappe.render_template("smarterp_comparison_report_print",{
                                                        'cc_vlcc_details':me.cc_vlcc_details
                                                    }),
            title:__("SmartERP - SmartERP Comparison Report"),
            base_url: base_url,
            print_css: print_css
        });
        open_pdf(html)
    },
    make_export:function(){
        var me = this;
        var args = {
            cmd: 'dairy_erp.dairy_erp.page.smarterp_comparison_report.smarterp_comparison_report.get_xlsx',
            data:{'amcu_data':me.amcu_data,'cc_vlcc_details':me.cc_vlcc_details},
        }
        open_url_post(frappe.request.url, args);
    }
})