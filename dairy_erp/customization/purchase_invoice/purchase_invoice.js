$.extend(cur_frm.cscript, new dairy.price_list.PriceListController({frm: cur_frm}));

frappe.ui.form.on("Purchase Invoice", {
	onload: function(frm) {
		frm.trigger("set_credit_to");
	},

	company: function(frm) {
		frm.trigger("set_credit_to");
	},

	set_credit_to: function(frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Company",
				filters: {"name": frm.doc.company},
				fieldname: ["abbr"]
			},
			async:false,
			callback: function(r){
				frm.set_value("credit_to", "Creditors - "+r.message.abbr)
			}
		})
	}
})