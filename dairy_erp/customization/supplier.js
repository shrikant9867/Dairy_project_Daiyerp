frappe.ui.form.on('Supplier', {
	refresh: function(frm) {
		if(!frm.doc.__islocal && in_list(['Dairy Local'], frm.doc.supplier_type)){
					frm.add_custom_button(__("Dairy Dashboard"), function() {
						frappe.set_route("dairy-dashboard");
					})
				}
	},
	onload: function(frm){
		var operator = get_session_user_type()
		if (operator.operator_type == 'Camp Office'){
			cur_frm.set_query("supplier_type", function () {
				return {
					"filters": {
						"supplier_type":  ["in",["Dairy Local","Vlcc Type"]]
					}
				}
			});		
		}
		else if(operator.operator_type == 'VLCC'){
			cur_frm.set_query("supplier_type", function () {
				return {
					"filters": {
						"supplier_type":  ["in",['Dairy Type','Farmer','VLCC Local']]
					}
				}
			});	
		}
	}
})


get_session_user_type = function() {
	var user;
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "User",
			filters: {"name": frappe.session.user},
			fieldname: ["operator_type","company"]
		},
		async:false,
		callback: function(r){
			if(r.message){	
	
				user = {
					"operator_type": r.message.operator_type,
					"company": r.message.company
				}		
			}
		}
	});

	return user
}