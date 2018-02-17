frappe.pages['vlcc-dashboard'].on_page_load = function(wrapper) {
	new frappe.vlcc_dashboard({
		$wrapper: $(wrapper)
	});
	frappe.breadcrumbs.add("Dairy Erp");
}

frappe.vlcc_dashboard = Class.extend({
	init: function(opts) {
		this.$wrapper = opts.$wrapper
		this.render_layout();
	},

	render_layout: function() {
		this.$wrapper.empty();
		this.$wrapper.append(frappe.render_template("dashboard_layout", {"header": "VLCC"}));
		this.$sidebar = this.$wrapper.find("#dairy_sidebar");
		this.$content = this.$wrapper.find(".dairy_content");
		this.$total_row = this.$wrapper.find('.total_summery');
		this.$addresses = this.$wrapper.find('.addresses');
		this.$party_master = this.$wrapper.find('.party_master');
		this.make();
	},

	make: function() {
		this.make_sidebar();
		this.fetch_vlcc_data();
		this.bind_event();
	},

	make_sidebar: function() {
		side_menus = [{
			"label": "Head Office",
			"doctype": "Address",
			"add_type": "Head Office"
		},
		{
			"label": "Camp Office",
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
			"label": "Farmer",
			"doctype": "Farmer",
			"add_type": ""
		}]
		this.$sidebar.append(frappe.render_template('dashboard_sidebar', {'side_menus': side_menus}))
	},

	fetch_vlcc_data: function() {
		var me = this;
		frappe.call({
			method: "dairy_erp.dairy_erp.page.vlcc_dashboard.vlcc_dashboard.get_vlcc_data",
			callback: function(r) {
				if(!r.exc && r.message){
					me.render_content(r.message)
					me.bind_event();
				}
				else {
					me.$content.append('<div class="text-muted no_data">No Data Found</div>')
				}
			}
		})
	},

	render_content: function(data) {
		var me = this;
		// total sumerry row
		me.$total_row.append(frappe.render_template('total_summery', {
			'data': data['total_summery']
		}))

		//addresses
		$.each(data['addresses'], function(idx, address){
			me.$addresses.append(frappe.render_template('dashboard_panel', {
				'data': address
			}))
		})

		//farmer
		me.$party_master.append(frappe.render_template('dashboard_panel', {
			'data': data['farmer']
		}))

		//supplier
		me.$party_master.append(frappe.render_template('dashboard_panel', {
			'data': data['supplier']
		}))
	},


	bind_event: function() {
		//side bar menu click
		$('._doctype').on("click", function() {
			doctype = $(this).attr('data-doctype');
			add_type = $(this).attr('data-add_type');
			filters =  add_type ? {"address_type": add_type} : {}
			frappe.set_route("List", doctype, filters)
		})

		//add new btn
		$('.new_master').on("click", function() {
			doctype = $(this).attr('data-doctype');
			frappe.new_doc(doctype)
		})

		// Refresh Btn
		$('.refresh_btn').on("click", function() {
			window.location.reload();
		})
	}
})