{% include "dairy_erp/public/js/openpdf.js" %}
frappe.pages['individual_farmer_milk_report'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Individual Farmer Milk Report',
		single_column: true
	});
    new frappe.individual_farmer_milk_report(wrapper);
    frappe.breadcrumbs.add("Dairy Erp");
}

frappe.individual_farmer_milk_report = Class.extend({
    init : function(wrapper){
        var me = this;
        this.wrapper_page = wrapper.page;
        this.page = $(wrapper).find('.layout-main-section');
        this.wrapper = $(wrapper).find('.page-content');
        this.set_filters();
    },
    render_table: function(vlcc_,cycle_,farmer_) {
        var me = this;
        frappe.call({
            method: "dairy_erp.dairy_erp.page.individual_farmer_milk_report.individual_farmer_milk_report.get_fmcr_data",
            args: {
                "vlcc":vlcc_,
                "cycle":cycle_,
                "farmer":farmer_
            },
            callback: function(r){
                if(r.message){
					console.log("inside r message",r.message)
                    me.table_data = r.message
                    $(me.page).find(".render-table").empty();
                    me.print = frappe.render_template("individual_farmer_milk_report",{
                                                        'fmcr':r.message.fmcr,
                                                        'previous_balance':r.message.previous_balance ? r.message.previous_balance:0.00,
                                                        'total_milk_amount':r.message.total_milk_amount ? r.message.total_milk_amount:0.00,
                                                        'payment':r.message.payment ? r.message.payment : 0.00,
                                                        'cattle_feed':r.message.cattle_feed ? r.message.cattle_feed : 0.00
                                                    });
                    $(me.page).find(".render-table").append(me.print);
                }
                /*else{
                    $(me.page).find(".render-table").empty();
                    __html = "<h1 class='render-table' style='padding-left: 25px;'>Record Not Found</h1>"
                    me.page.find(".render-table").append(__html)
                }*/
            }
        })
    },
    set_filters:function(){
        var me = this;
        html = `<div class='row'>
                    <div class='col-xs-3 vlcc-field' style='padding-left: 48px;'></div>\
                    <div class='col-xs-3 month-field' style='padding-left: 48px;'></div>\
                    <div class='col-xs-3 cycle-field' style='padding-left: 48px;'></div>\
                    <div class='col-xs-3 farmer-field' style='padding-left: 48px;'></div>\
                </div>
                <div class='row'>
                    <div class='col-xs-12 render-table'></div>
                </div>`
        me.page.html(html)
        me.vlcc = frappe.ui.form.make_control({
            parent: me.page.find(".vlcc-field"),
            df: {
	            fieldtype: "Data",
	            label:__("VLCC"),
	            fieldname: "vlcc",
				read_only: 1
            },
            render_input: true
        });
        me.set_vlcc_value();
        me.month = frappe.ui.form.make_control({
            parent: me.page.find(".month-field"),
            df: {
	            fieldtype: "Select",
	            label:__("Month"),
	            fieldname: "month",
	            options:["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
            	reqd:1,
                onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.vlcc.get_value() && me.cycle.get_value() && me.farmer.get_value()) {
                        me.month_change(me.vlcc.get_value(),me.cycle.get_value(),me.farmer.get_value())
                    }
                }
            },
            render_input: true
        });
        me.cycle = frappe.ui.form.make_control({
			parent: me.page.find(".cycle-field"),
			df: {
				fieldtype: "Link",
				label:"Farmer Cycle",
				placeholder: __("Farmer Cycle"),
				fieldname: "cycle",
				options:"Cyclewise Date Computation",
				reqd:1,
				get_query: function () {
					return {
						"filters": {
							"month": me.month.get_value()
							}
						}
				},
                onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.vlcc.get_value() && me.cycle.get_value() && me.farmer.get_value()) {
                        me.cycle_change(me.vlcc.get_value(),me.cycle.get_value(),me.farmer.get_value())
                    }
                }
			},
			render_input: true
		});
		me.cycle.refresh();
		me.farmer = frappe.ui.form.make_control({
			parent: me.page.find(".farmer-field"),
			df: {
				fieldtype: "Link",
				label:"Farmer",
				options:"Farmer",
				placeholder: __("Farmer"),
				fieldname: "farmer",
				reqd:1,
				get_query: function () {
					return {
						"filters": {
							"vlcc_name": me.vlcc.get_value()
							}
						}
				},
				onchange: function(){
                    $(me.page).find(".render-table").empty();
                    if(me.vlcc.get_value() && me.cycle.get_value() && me.farmer.get_value()) {
                        me.farmer_change(me.vlcc.get_value(),me.cycle.get_value(),me.farmer.get_value())
                    }
                }
			},
			render_input: true
		});
		me.farmer.refresh();
        me.wrapper_page.set_primary_action(__("Print"), function () {
            me.create_pdf()
        })
        me.wrapper_page.set_secondary_action(__("Refresh"),function() { 
            window.location.reload();
        })
    },
    set_vlcc_value:function(){
    	var me = this;
    	frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "User",
				filters: {"name": frappe.session.user},
				fieldname: ["company"]
			},
			callback: function(r) {
				if(!r.exc && r.message && !in_list(["Administrator", "Guest"], frappe.session.user)){
					if(has_common(frappe.user_roles, ["Vlcc Operator", "Vlcc Manager"])){
							me.vlcc.set_value(r.message.company);					
					}
				}
			}
		})
    },
    farmer_change: function(vlcc_,cycle_,farmer_){
        var me =this;
        $(me.page).find(".render-table").empty();
        me.render_table(vlcc_,cycle_,farmer_);
    },
    cycle_change: function(vlcc_,cycle_,farmer_){
        var me =this;
        $(me.page).find(".render-table").empty();
        me.render_table(vlcc_,cycle_,farmer_);
    },
    month_change: function(vlcc_,cycle_,farmer_){
        var me =this;
        $(me.page).find(".render-table").empty();
        me.cycle.set_value("")
        me.farmer.set_value("")
    },
    create_pdf: function(){
        var me = this;
        var base_url = frappe.urllib.get_base_url();
        var print_css = frappe.boot.print_css;
        var html = frappe.render_template("ifmr_pdf",{
            content: frappe.render_template("individual_farmer_milk_report",{
                                                        'fmcr':me.table_data.fmcr,
                                                        'previous_balance':me.table_data.previous_balance ? me.table_data.previous_balance:0.00,
                                                        'total_milk_amount':me.table_data.total_milk_amount ? me.table_data.total_milk_amount:0.00,
                                                        'payment':me.table_data.payment ? me.table_data.payment : 0.00,
                                                        'cattle_feed':me.table_data.cattle_feed ? me.table_data.cattle_feed : 0.00
                                                    }),
            title:__("individual_farmer_milk_report"+frappe.datetime.str_to_user(frappe.datetime.get_today())),
            base_url: base_url,
            print_css: print_css
        });
        open_pdf(html)
    }
}) 
