// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["VLCC Payment Settlement"] = {

	"filters": [
		{
			"fieldname":"cycle",
			"label": __("Cycle"),
			"fieldtype": "Select",
			"on_change":function(){
				frappe.call({
				method:"dairy_erp.dairy_erp.report.vlcc_payment_settlement.vlcc_payment_settlement.test",
				callback:function(r){
					
				}
			})

			}
		},
		{
			"fieldname":"vlcc",
			"label": __("VLCC"),
			"fieldtype": "Link",
			"options":"Village Level Collection Centre",
			"reqd":1
		},
		{
			"fieldname":"start_date",
			"label": __("Start Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd":1
		},
		{
			"fieldname":"end_date",
			"label": __("End Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd":1
		},
		{
			"fieldname":"prev_transactions",
			"label": __("Previous Transactions"),
			"fieldtype": "Check"
		},

	],
	formatter: function(row, cell, value, columnDef, dataContext,default_formatter) {
				if (columnDef.df.label=="") {
					return repl("<input type='checkbox' \
						data-row='%(row)s' %(checked)s>", {
							row: row,
							checked: (dataContext.selected ? "checked=\"checked\"" : "")
						});
				}
				value = default_formatter(row, cell, value, columnDef, dataContext);
				return value
				},
	onload: function(report) {

		var me = frappe.container.page.query_report;
		

		frappe.selected_rows = []

		var cycles = [""]
		var cycle_filter = frappe.query_report_filters_by_name.cycle;

		
		frappe.call({
			method:"dairy_erp.dairy_erp.report.vlcc_payment_settlement.vlcc_payment_settlement.get_cycles",
			callback:function(r){
				for (var i = 1; i <= r.message[0].value; i++) {
					cycles.push("Cycle "+ i)
					cycle_filter.df.options = cycles
					cycle_filter.refresh();		
				}
			}
		})

		report.page.add_inner_button(__("Payment Settlement"), function() {

			/*if(!report.get_values().vlcc){
				frappe.throw("Please select VLCC first")
			}*/
			frappe.selected_rows = []

			$.each(me.data,function(i,d){
				if (d.selected == true){
					frappe.selected_rows.push(d.Name)
				}
			})
			
			frappe.query_reports['VLCC Payment Settlement'].get_summary_dialog(report)
		});

		$('body').on("click", "input[type='checkbox'][data-row]", function() {
			me.data[$(this).attr('data-row')].selected
					= this.checked ? true : false;
		})
	},
	get_summary_dialog:function(report){
		var dialog = new frappe.ui.Dialog({
		title: __("Payment Settlement"),
		fields: [
			{
				"label": __("Payble Amount"),
				"fieldname": "payble",
				"fieldtype": "Currency",
				"read_only": 1,
			},
			{
				"label": __("Receivable Amount"),
				"fieldname": "receivable",
				"fieldtype": "Currency",
				"read_only": 1,
			},
			{
				"label": __("Settlement Amount(Auto)"),
				"fieldname": "set_amt",
				"fieldtype": "Currency",
				"read_only": 1,
			},
			{
				"label": __("Settlement Amount(Manual)"),
				"fieldname": "input",
				"fieldtype": "Currency"
			}
		]
	});

	frappe.call({
		method:"dairy_erp.dairy_erp.report.vlcc_payment_settlement.vlcc_payment_settlement.get_payment_amt",
		args : {"row_data":frappe.selected_rows},
		callback : function(r){
			dialog.set_values({
				'payble': r.message.payble,
				'receivable': r.message.receivable,
				"set_amt":r.message.set_amt
			});
			if(r.message.payble <= r.message.receivable){
				dialog.get_field('input').df.hidden = 0;
				dialog.get_field('input').refresh();
			}
		}
	})
	
	dialog.show()

	dialog.set_primary_action(__("Submit"), function() {

		frappe.call({
			method:"dairy_erp.dairy_erp.report.vlcc_payment_settlement.vlcc_payment_settlement.make_payment",
			args : {
					"data":dialog.get_values(),
					"row_data":frappe.selected_rows,
					"filters":report.get_values()
					},
			callback : function(r){
				
				dialog.hide()
			}
		})
	})
	},
	remove: function(array, element) {
    	const index = array.indexOf(element);
    	array.splice(index, 1);
	}

}
