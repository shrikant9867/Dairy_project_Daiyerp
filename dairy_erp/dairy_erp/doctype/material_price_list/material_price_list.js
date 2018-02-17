// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Price List', {
	refresh: function(frm) {

	},
	party_type: function(frm) {
	if(cur_frm.doc.party_type == "VLCC"){
		frm.set_value("selling",1)
		frm.set_value("buying",0)
	}
	if(cur_frm.doc.party_type == "Local Supplier"){
		frm.set_value("buying",1)
		frm.set_value("selling",0)
	}
}
});


cur_frm.fields_dict['items'].grid.get_field("item").get_query = function(doc, cdt, cdn) {

	var item_list = []
	for(var i = 0 ; i < cur_frm.doc.items.length ; i++){
		if(cur_frm.doc.items[i].item){
			item_list.push(cur_frm.doc.items[i].item);
		}
	}
	return {
	filters: [
			['Item', 'name', 'not in', item_list]
		]
	}
}

