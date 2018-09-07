// Copyright (c) 2018, indictrans technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dairy Register', {
	refresh: function(frm) {
		$('.page-actions').hide()
		$('.indicator').hide()
		var html='';
        html+=repl('<div class="row">\
        			<div class="col-xs-6">\
        			<a target="_blank" href="#dairy_register_one" style="margin-left:26px"><b>Dairy Register One</b></a>\
        			</div>\
        			<div class="col-xs-6">\
        			<a target="_blank" href="#dairy_register_two" style="margin-left:26px"><b>Dairy Register Two</b></a>\
        			</div>\
                    </div>')
        $(cur_frm.fields_dict.page_link.wrapper).html(html);
	}
});
