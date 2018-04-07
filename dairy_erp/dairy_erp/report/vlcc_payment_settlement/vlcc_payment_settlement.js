// Copyright (c) 2016, indictrans technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["VLCC Payment Settlement"] = {

	"filters": [
			{
				"fieldname":"vlcc",
				"label": __("VLCC"),
				"fieldtype": "Link",
				"options":"Village Level Collection Centre",
				"reqd":1
				},
			{
				"fieldname":"cycle",
				"label": __("Cycle"),
				"fieldtype": "Link",
				"options": "Cyclewise Date Computation",
				"reqd":1,
				"on_change":function(query_report){
					frappe.call({	
						method:"dairy_erp.dairy_erp.report.vlcc_payment_settlement.vlcc_payment_settlement.get_dates",
						args:{
								"filters":query_report.get_values()
							},
					callback:function(r){
							if(r.message){
								frappe.query_report_filters_by_name.start_date.set_input(r.message[0].start_date);
								frappe.query_report_filters_by_name.end_date.set_input(r.message[0].end_date);
								query_report.trigger_refresh();		
							}
							else{
								frappe.query_report_filters_by_name.start_date.set_input(frappe.datetime.get_today());
								frappe.query_report_filters_by_name.end_date.set_input(frappe.datetime.get_today());
								query_report.trigger_refresh();
							}		
						}
					})
			},
			"get_query":function(query_report){
				var vlcc = frappe.query_report_filters_by_name.vlcc.get_value()

				return{
					query:"dairy_erp.dairy_erp.report.vlcc_payment_settlement.vlcc_payment_settlement.get_settlement_per",
					filters: {
						"vlcc": vlcc
					}

				}

			}
		},
		{
			"fieldname":"start_date",
			"label": __("Start Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"read_only":1
		},
		{
			"fieldname":"end_date",
			"label": __("End Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"read_only":1
		},
		/*{
			"fieldname":"prev_transactions",
			"label": __("Previous Transactions"),
			"fieldtype": "Check"
		},*/

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

		frappe.query_reports['VLCC Payment Settlement'].report_operation(report)
		// frappe.query_reports['VLCC Payment Settlement'].get_default_cycle(report)

	},
	report_operation: function(report){
		var me = frappe.container.page.query_report;
		var filters = report.get_values()
		
		frappe.selected_rows = []

		report.page.add_inner_button(__("Payment Settlement"), function() {

			frappe.selected_rows = []

			$.each(me.data,function(i,d){
				if (d.selected == true){
					frappe.selected_rows.push(d.Name)
				}
			})

			if (frappe.selected_rows.length === 0){
				frappe.throw("Please select records")
			}
			var end_date = frappe.query_report_filters_by_name.end_date.get_value()
			if(frappe.datetime.str_to_obj(frappe.datetime.get_today()) < frappe.datetime.str_to_obj(end_date)){
				frappe.throw(__("Settlement can be done after <b>{0}</b>",[frappe.datetime.str_to_user(end_date)]))
			}
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
				"label": __("Payable Amount"),
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
				"fieldname": "set_amt_manual",
				"fieldtype": "Currency"
			},
			{
				"label": __("Mode Of Payment"),
				"fieldname": "mode_of_payment",
				"fieldtype": "Link",
				"options":"Mode of Payment"
			},
			{fieldtype: "Section Break",fieldname:"sec_brk"},
			{
				"label": __("Cheque/Reference No"),
				"fieldname": "ref_no",
				"fieldtype": "Data"
			},
			{fieldtype: "Column Break"},
			{
				"label": __("Cheque/Reference Date"),
				"fieldname": "ref_date",
				"fieldtype": "Date",
				"default": frappe.datetime.get_today(),
			}
		]
	});

	frappe.call({
		method:"dairy_erp.dairy_erp.report.vlcc_payment_settlement.vlcc_payment_settlement.get_payment_amt",
		args : {"row_data":frappe.selected_rows,"filters":report.get_values()},
		callback : function(r){
			dialog.set_values({
				'payble': r.message.payble,
				'receivable': r.message.receivable,
				"set_amt":r.message.set_amt,
				"set_amt_manual": r.message.payble - r.message.set_amt
			});
			if(r.message.payble <= r.message.receivable){
				dialog.get_field('set_amt_manual').df.hidden = 1;
				dialog.get_field('set_amt_manual').refresh();
				dialog.get_field('mode_of_payment').df.hidden = 1;
				dialog.get_field('mode_of_payment').refresh();
				dialog.get_field('ref_no').df.hidden = 1;
				dialog.get_field('ref_no').refresh();
				dialog.get_field('ref_date').df.hidden = 1;
				dialog.get_field('ref_date').refresh();
				dialog.get_field('sec_brk').df.hidden = 1;
				dialog.get_field('sec_brk').refresh();
			}
		}
	})
		
		dialog.show()

		dialog.set_primary_action(__("Submit"), function() {

			frappe.query_reports['VLCC Payment Settlement'].validate_amount(dialog)

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
	validate_amount:function(dialog){
		var data = dialog.get_values()
		if(data.set_amt && data.set_amt_manual && (data.set_amt_manual > (data.payble - data.set_amt))){		
				frappe.throw(__("<b>Settlement Amount {0}</b> cannot be greater than <b>Payable Amount {1}</b>",
					[data.set_amt_manual,data.payble-data.set_amt]))
		}
		else if(data.payble && !data.set_amt && (data.set_amt_manual > data.payble)){
			frappe.throw(__("<b>Settlement Amount {0}</b> cannot be greater than <b>Payable Amount {1}</b>",
				[data.set_amt_manual,data.payble]))
		}


	},
	get_default_cycle:function(report){
		frappe.call({
				method:"dairy_erp.dairy_erp.report.vlcc_payment_settlement.vlcc_payment_settlement.get_default_cycle",
				args:{
					"filters":report.get_values()
				},
				callback : function(r){
					/*if(r.message){
						frappe.query_report_filters_by_name.cycle.set_input(r.message[0].name);
						frappe.query_report_filters_by_name.start_date.set_input(r.message[0].start_date);
						frappe.query_report_filters_by_name.end_date.set_input(r.message[0].end_date);
						report.trigger_refresh();		
					}
					else{
						// frappe.throw("Please define Cycle from <b>VLCC Payment Cycle</b> ")
						frappe.query_report_filters_by_name.start_date.set_input(frappe.datetime.get_today());
						frappe.query_report_filters_by_name.end_date.set_input(frappe.datetime.get_today());
						report.trigger_refresh();
					}*/
				}
			})
	}

}
