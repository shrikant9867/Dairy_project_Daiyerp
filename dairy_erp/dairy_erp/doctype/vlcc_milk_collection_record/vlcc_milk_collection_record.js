// Copyright (c) 2017, indictrans technologies and contributors
// For license information, please see license.txt
var milk_quality_type = {
	'Good':'G',
	'Curdled by Society':'CS',
	'Curdled by Transporter':'CT',
	'Sub Standard':'SS'
}

frappe.ui.form.on('Vlcc Milk Collection Record', {
	milkquantity: function(frm) {
		if(frm.doc.milkquantity > 0){
			frm.trigger("calculate_amount");
		}
		else{
			if(frm.doc.status == "Accept"){		
				frm.set_value("milkquantity",1)
				frappe.throw("Milk Quantity Can not be less or equal to zero")	
			}
		}
	},

	rate: function(frm) {
		if(frm.doc.rate > 0){
			frm.trigger("calculate_amount");
		}
		else{
			if(frm.doc.status == "Accept"){		
				frm.set_value("rate",1)
				frappe.throw("Rate Can not be less or equal to zero")	
			}
		}
	},

	collectionroute:function(frm){
		var route = String(frm.doc.collectionroute)
		if(route.length < 3 && frm.doc.collectionroute){
			frm.set_value("collectionroute","")
			frappe.throw("Collection Route contain atleast 3 Charaters")
		}
	},

	validate: function(frm) {
		frm.trigger("calculate_amount");
		frm.trigger("validate_milk_quality");
	},

	calculate_amount: function(frm) {
		if(frm.doc.milkquantity && frm.doc.rate) {
			frm.set_value("amount", flt(frm.doc.rate * frm.doc.milkquantity))
		}
		else {
			frm.set_value("amount", 0)
		}
	},

	validate_milk_quality: function(frm){
		if(frm.doc.status == "Reject" && frm.doc.milkquality == "G") {
			frm.set_value("milkquality", "")
			frm.set_value("milk_quality_type", "")
			frappe.throw("For Reject Stauts Please Select Milk Quality Type as 'Curdled by Society' or 'Curdled by Transporter' or 'Sub Standard' ")
		}
		if (in_list(['Curdled by Society', 'Curdled by Transporter', 'Sub Standard'], frm.doc.milk_quality_type) && frm.doc.status == "Accept"){
			frm.set_value("milkquality", "")
			frm.set_value("milk_quality_type", "")
			frappe.throw("For Accept Stauts Please Select Milk Quality Type as 'Good' ")
		}
	},

	onload: function(frm) {
		if (has_common(frappe.user_roles, ["Chilling Center Manager", "Chilling Center Operator"])){		
			frappe.db.get_value("User",frappe.session.user,"branch_office", function(v){
				frappe.db.get_value("Address",v['branch_office'],"centre_id", function(c){
					frm.set_value("societyid", c['centre_id'])	
				})
			})
		}
		/*if(frm.doc.status){
			if(frm.doc.status == "Accept") {
				frm.set_df_property("milk_quality_type", "options", ['Good']);
				frm.set_value("milk_quality_type","Good")
				frm.set_value("milkquality","G")
			}
			else if(frm.doc.status == "Reject") {
				frm.set_df_property("milk_quality_type", "options", ['Curdled by Society','Curdled by Transporter','Sub Standard']);
				frm.set_value("milk_quality_type","")
				frm.set_value("milkquality","")
			}
		}*/
	},

	status: function(frm){
		if(frm.doc.status == "Accept") {
			frm.set_value("milk_quality_type","Good")
			frm.set_value("milkquality","G")
		}
		else if(frm.doc.status == "Reject") {
			frm.set_value("milk_quality_type","")
			frm.set_value("milkquality","")
		}
	},
	
	milk_quality_type:function(frm){
		if(frm.doc.milk_quality_type && frm.doc.milk_quality_type != ' '){
			frm.set_value("milkquality",String(milk_quality_type[frm.doc.milk_quality_type]))
		}
		else{
			frm.set_value("milkquality",'')
		}
	},
	
	associated_vlcc:function(frm){
		/*if(frm.doc.associated_vlcc && frm.doc.long_format_farmer_id){
			var collectionroute = frm.doc.long_format_farmer_id.split('_')[2]
			frm.set_value("collectionroute",collectionroute)
		}*/
		//Created by Shrikant 15:00
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Village Level Collection Centre",
					filters: {"name": frm.doc.associated_vlcc },
					fieldname: ["longformatfarmerid","longformatsocietyid_e"]
				},
				async:false,
				callback: function(r){
					if(r.message){
						if (frm.doc.shift == "MORNING") {
							frm.set_value("long_format_farmer_id",r.message.longformatfarmerid)
							frm.refresh_fields('long_format_farmer_id')
							 if(frm.doc.associated_vlcc && frm.doc.long_format_farmer_id){
							 var collectionroute = frm.doc.long_format_farmer_id.split('_')[2]
							 frm.set_value("collectionroute",collectionroute)
							 }
						}
						else if(frm.doc.shift == "EVENING"){
							frm.set_value("long_format_farmer_id_e",r.message.longformatsocietyid_e)
							frm.refresh_fields('long_format_farmer_id_e')
							 if(frm.doc.associated_vlcc && frm.doc.long_format_farmer_id_e){
							 var collectionroute = frm.doc.long_format_farmer_id_e.split('_')[2]
							 frm.set_value("collectionroute",collectionroute)
							 }
						}


					}
				}
			});
		//end
	},
	shift:function(frm){
		frm.set_value("associated_vlcc","");
		frm.set_value("farmerid","");
		frm.set_value("long_format_farmer_id","");
		frm.set_value("long_format_farmer_id_e","");
		frm.set_value("collectionroute","");

	}

});
