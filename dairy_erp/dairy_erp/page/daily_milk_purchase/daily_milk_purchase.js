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
    render_layout: function(date_) {
        var me = this;
        frappe.call({
            method: "dairy_erp.dairy_erp.page.daily_milk_purchase.daily_milk_purchase.get_data",
            args: {
                "curr_date":date_
            },
            callback: function(r){
                if(r.message){
                    me.table_data = r.message
                    $(me.page).find(".render-table").empty();
                    me.print = frappe.render_template("daily_milk_purchase",{
                            "fmcr_stock_data":me.table_data.fmcr_stock_data,
                            "avg_data":me.table_data.avg_data,
                            "local_sale_data":me.table_data.local_sale_data,
                            "member_data":me.table_data.member_data
                            })
                    $(me.page).find(".render-table").append(me.print)
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
        me.wrapper_page.set_primary_action(__("Print"), function () {
            me.create_pdf(me.curr_date.get_value())
        })
        me.wrapper_page.set_secondary_action(__("Refresh"),function() { 
            window.location.reload();
        })
    },
    curr_date_change: function(date_){
        var me =this;
            $(me.page).find(".render-table").empty();
            me.render_layout(date_);
    },
    create_pdf: function(date_){
        var me = this;
        var base_url = frappe.urllib.get_base_url();
        var print_css = frappe.boot.print_css;
        var html = frappe.render_template("pdf",{
            content: frappe.render_template("daily_milk_purchase_print",{
                            "fmcr_stock_data":me.table_data.fmcr_stock_data,
                            "avg_data":me.table_data.avg_data,
                            "local_sale_data":me.table_data.local_sale_data,
                            "member_data":me.table_data.member_data,
                            "vlcc":me.table_data.vlcc,
                            "vlcc_addr":me.table_data.vlcc_addr,
                            "date_":frappe.datetime.str_to_user(date_)
                            }),
            title:__("daily_milk_purchase_report_"+frappe.datetime.str_to_user(frappe.datetime.get_today())),
            base_url: base_url,
            print_css: print_css
        });
        open_pdf(html)
    }
})

open_pdf = function(html) {
        //Create a form to place the HTML content
        var formData = new FormData();

        //Push the HTML content into an element
        formData.append("html", html);
        // formData.append("orientation", orientation);
        var blob = new Blob([], { type: "text/xml"});
        //formData.append("webmasterfile", blob);
        formData.append("blob", blob);

        var xhr = new XMLHttpRequest();
        xhr.open("POST", '/api/method/frappe.utils.print_format.report_to_pdf');
        xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);
        xhr.responseType = "arraybuffer";

        xhr.onload = function(success) {
            if (this.status === 200) {
                var blob = new Blob([success.currentTarget.response], {type: "application/pdf"});
                var objectUrl = URL.createObjectURL(blob);

                //Open report in a new window
                window.open(objectUrl);
            }
        };
        xhr.send(formData);
    }