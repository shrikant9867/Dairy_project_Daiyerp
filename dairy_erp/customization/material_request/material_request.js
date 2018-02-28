frappe.ui.form.on('Material Request', {
	refresh: function(frm) {
		var operator_type
		frappe.call({
			method: "frappe.client.get_value",
			async : false,
			args: {
				doctype: "User",
				filters: {"name": frappe.session.user},
				fieldname: ["operator_type","company"]
			},
			callback: function(r){
				if(r.message){
					operator_type = r.message.operator_type
					get_co(r.message.company)
				}
			}
		});
		/*if(!frm.doc.__islocal && frm.doc.docstatus == 1 && operator_type == 'Camp Office'){
			frm.add_custom_button(__("Make PO"), function() {
				make_dialog(frm)
			})
		}*/

	},
	onload : function (frm) {
		console.log(get_session_user_type())
		if (get_session_user_type().operator_type == "Chilling Centre"){
			camp = address_attr(get_session_user_type().branch_office)
			console.log(camp,"##")
			frm.set_value("camp_office",camp.camp_office)
		}
	}


})

get_co = function(company){
	frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Village Level Collection Centre",
				filters: {"name": company},
				fieldname: ["camp_office","warehouse"]
			},
			callback: function(r){
				if(r.message){
					cur_frm.set_value("camp_office",r.message.camp_office)
					$.each(cur_frm.doc.items,function(i,d){
						frappe.model.set_value(d.doctype, d.name, "warehouse", r.message.warehouse);
					})
				}
			}
	});
}

make_dialog = function(frm){
	var dialog = new frappe.ui.Dialog({
	title: __("PO Details"),
	fields: [
		{
			"label": __("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"reqd": 1
		},
		{
			"label": __("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"label": __("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"reqd": 1
		},
		{
			"label": __("Taxes and Charges"),
			"fieldname": "taxes_and_charges",
			"fieldtype": "Link",
			"options": "Purchase Taxes and Charges Template"
		},
	]
});
	dialog.set_primary_action(__("Submit"), function() {
		frappe.call({
			method:"dairy_erp.customization.material_request.material_request.make_po",
			args:{
				"data":dialog.get_values(),
				"doc":frm.doc
			},
			callback:function(r){
			}
		})

	})
	dialog.hide()
	dialog.show()

}

get_session_user_type = function() {
	var user;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "User",
			filters: {"name": frappe.session.user},
			fieldname: ["operator_type","company","branch_office"]
		},
		async:false,
		callback: function(r){
			if(r.message){	
				user = {
					"operator_type": r.message.operator_type,
					"company": r.message.company,
					"branch_office":r.message.branch_office
				}		
			}
		}
	});

	return user
}


address_attr = function(branch_office) {
	var camp;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "Address",
			filters: {"name": branch_office},
			fieldname: ["associated_camp_office"]
		},
		async:false,
		callback: function(r){
			if(r.message){
			console.log(r.message.associated_camp_office)	
				camp = {
					"camp_office": r.message.associated_camp_office,
				}		
			}
		}
	});

	return camp
}