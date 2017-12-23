
frappe.ui.form.on('Purchase Order', {

	refresh : function (frm) {
		cur_frm.add_custom_button(__('Get items from MR'), function() {
			make_dialog(frm)
		})
		
	}

})

make_dialog = function(frm){
	// console.log(frm,"@@")
	var dialog = new frappe.ui.Dialog({
	title: __("Select Material Requests"),
	fields: [
		{
			"label": __("Camp Office"),
			"fieldname": "camp_office",
			"fieldtype": "Link",
			"options": "Address",
			"reqd": 1,
			"get_query":function(){
				return {
						query:"dairy_erp.customization.customization.get_camp_office"
					}
			}
		},
		{
			"fieldname": "mr_area",
			"fieldtype": "HTML"
		},
		{
			"label":__("Get MR"),
			"fieldname": "get_mr",
			"fieldtype": "Button"
		}
		
	]
});
	dialog.fields_dict.get_mr.$input.click(function(frm,cdt,cdn) {
		// console.log(frm.doc,"----")
		frappe.call({
			method:"dairy_erp.customization.customization.get_pending_mr",
			args:{
				"data":dialog.get_values()
			},
			callback:function(r){
              $('.frappe-control input:checkbox').removeAttr('checked');
		      var html = "<form><table class='table table-bordered' id='mytable' width=80%>\
			      <thead class='grid-heading-row'>\
			      <tr><th class='text-center'>Name</th>\
			      <th class='text-center'>VLCC</th>\
			      <th class='text-center'>Camp Office</th>\
			      <th class='text-center'>Date</th>\
			      </thead>\
			      <tbody>"
			for (var i = 0; i<r.message.length; i=i+1) {
			     html+="<tr>\
			      <td class='text-center'><label style='font-weight: normal;'><input type='checkbox' class='select' id='_select' name='"+r.message[i].name+"' value='"+r.message[i].name+"'> "+r.message[i].name+ "</label></td>\
			      <td class='text-right' id='company'>"+r.message[i].company+"</td>\
			      <td class='text-right' id='camp_office'>"+r.message[i].camp_office+"</td>\
			      <td class='text-right' id='date'>"+r.message[i].schedule_date+"</td>\
			      </tr>";

			}
		     html+="</tbody>\
		      </table></form><br>";

		    var wrapper = dialog.fields_dict.mr_area.$wrapper;
			wrapper.html(html);
  
			}
		})
		});
	dialog.set_primary_action(__("Get Items"), function(frm) {
		var pending_mr = []
		$.each($('.frappe-control input:checkbox:checked'), function(i,v) {
			var company = $(this).closest("tr").find('#company').text().trim()
			var camp_office = $(this).closest("tr").find('#camp_office').text().trim()
			var mr_dict = {"name":$(v).val(),"company":company,"camp_office":camp_office}
			pending_mr.push(mr_dict)
		})
		frappe.call({
			method:"dairy_erp.customization.customization.get_item_table",
			args:{
				"data":pending_mr,
				"doc":cur_frm.doc
			},
			callback:function(r){
				if(r.message){
					console.log(frm,"row....")
				}

			}
		})
	dialog.hide()
	})
	dialog.show()

}