var i = 0;
frappe.pages['dairy-dashboard'].on_page_load = function(wrapper) {
    new frappe.dairy_dashboard({
        $wrapper: $(wrapper)
    });
    frappe.breadcrumbs.add("Dairy Erp");
}

frappe.pages['dairy-dashboard'].refresh = function(wrapper) {
    if (i!=0) {
        location.reload()
    }
    i=i+1
}

frappe.dairy_dashboard = Class.extend({
    init : function(opts){
        this.$wrapper = opts.$wrapper
        this.render_layout();
    },

    render_layout: function() {
        this.$wrapper.empty();
        this.$wrapper.append(frappe.render_template("dashboard_layout", {"header": "Dairy"}));
        this.$sidebar = this.$wrapper.find("#dairy_sidebar");
        this.$content = this.$wrapper.find(".dairy_content");
        this.$total_row = this.$wrapper.find('.total_summery');
        this.make();
    },

    make: function() {
        this.make_sidebar();
        this.fetch_data();
        this.bind_event();
    },

    make_sidebar: function() {
        side_menus = [{
            "label": "Head Office",
            "doctype": "Address",
            "add_type": "Head Office"
        },
        {
            "label": __("Camp Office"),
            "doctype": "Address",
            "add_type": "Camp Office"
        },
        {
            "label": "Chilling Center",
            "doctype": "Address",
            "add_type": "Chilling Centre"
        },
        {
            "label": "Plant Office",
            "doctype": "Address",
            "add_type": "Plant"
        },
        {
            "label": "VLCC",
            "doctype": "Village Level Collection Centre",
            "add_type": ""
        },
        {
            "label": "Supplier",
            "doctype": "Supplier",
            "add_type": ""
        },
        {
            "label": "Material Price List",
            "doctype": "Material Price List",
            "add_type": ""
        }]

        this.$sidebar.append(frappe.render_template('dashboard_sidebar', {'side_menus': side_menus}))
    },

    fetch_data: function() {
        var me = this;
        frappe.call({
            method:"dairy_erp.dairy_erp.page.dairy_dashboard.dairy_dashboard.get_data",
            callback : function(r){
                me.data = r.message
                me.render_view();
                me.bind_event()
            }
        })
    },

    render_view: function() {
        var me = this;
        me.$content.append(frappe.render_template("dairy_dashboard",{"data":me.data || {}}))
        me.$total_row.append(frappe.render_template('total_summery', {
            'data': me.data['total_summery']
        }))
    },

    bind_event : function(){
        var me = this;
        if(me.data){
            $.each(me.data.addr,function(i,d){
                if(d && d.address_type == "Head Office"){
                    $('#head-office').hide()
                }
            })
        }
        $("#head-office").on("click",function(){
            frappe.route_options = {
                "address_type": "Head Office"
            };
            frappe.new_doc("Address")
        })
        $("#camp-office").on("click",function(){
            frappe.route_options = {
                "address_type": "Camp Office",
                "Dynamic Link.link_doctype" : "Company",
                "Dynamic Link.link_name" : "Dairy"
            };
            frappe.new_doc("Address")
        })
        $("#chilling-centre").on("click",function(){
            frappe.route_options = {
                "address_type": "Chilling Centre"
            };
            frappe.new_doc("Address")
        })
        $("#plant").on("click",function(){
            frappe.route_options = {
                "address_type": "Plant"
            };
            frappe.new_doc("Address")
        })
        $("#new_vlcc").on("click",function(){
            frappe.new_doc("Village Level Collection Centre")
        })
        $("#new_supp").on("click",function(){
            frappe.route_options = {
                "supplier_type": "Dairy Local"
            };
            frappe.new_doc("Supplier")
        })

        $(".camp-office").on("click",function(){
            frappe.set_route("List", "Address", {'address_type': "Camp Office"});
        })
        $(".head-office-list").on("click",function(){
            frappe.set_route("List", "Address", {'address_type': "Head Office"});
        })
        $(".chilling-centre").on("click",function(){
            frappe.set_route("List", "Address", {'address_type': "Chilling Centre"});
        })
        $(".plant").on("click",function(){
            frappe.set_route("List", "Address", {'address_type': "Plant"});
        })

        $('._doctype').on("click", function() {
            doctype = $(this).attr('data-doctype');
            add_type = $(this).attr('data-add_type');
            filters =  add_type ? {"address_type": add_type} : {}
            frappe.set_route("List", doctype, filters)
        })
        $(".supplier-list").on("click",function(){
            frappe.set_route("List", "Supplier", {'supplier_type': "Dairy Local"});
        })

        // Refresh Btn
        $('.refresh_btn').on("click", function() {
            window.location.reload();
        })
    }
})