from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import timedelta
from frappe.utils import flt, cstr, cint
import dairy_utils as utils
import amcu_api as amcu_api
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime

def get_fmcr_hourly():

	fmcr = frappe.db.sql("""select name,sum(milkquantity) as qty,rate,societyid,
							rcvdtime,shift,milktype,farmerid,GROUP_CONCAT(name) as fmcr
			 	from 
				 	`tabFarmer Milk Collection Record`
				where 
					is_fmrc_updated = 0 and docstatus = 1
				group by societyid,date(rcvdtime),shift,milktype""",as_dict=True)


	if len(fmcr):
		for data in fmcr:
			vmcr = frappe.db.sql("""select name,sum(milkquantity) as qty,
									rcvdtime,shift,farmerid
		 					from 
		 						`tabVlcc Milk Collection Record` 
		 					where 
		 						shift = '{0}' and milktype = '{1}' and 
		 						date(rcvdTime) = '{2}' and farmerid = '{3}' and
		 						docstatus = 1
		 					group by farmerid
		 	""".format(data.get('shift'),data.get('milktype'),
		 		get_datetime(data.get('rcvdtime')).date(),
		 		data.get('societyid')),as_dict=1)
		 	
		 	vlcc = frappe.db.get_value("Village Level Collection Centre",
		 				{"amcu_id":data.get('societyid')},"name")
			vlcc_wh = frappe.db.get_value("Village Level Collection Centre",vlcc,
					["warehouse","edited_gain","edited_loss"],as_dict=1) or {}
		 	config_hrs = frappe.db.get_value('VLCC Settings',{'vlcc':vlcc},'hours') or 0

		 	max_time = get_datetime(data.get('rcvdtime')) + timedelta(hours=int(config_hrs))

		 	if now_datetime() < max_time: 
		 		pass
		 	elif now_datetime() > max_time: 
			 	if len(vmcr):
			 		if data.get('qty') > vmcr[0].get('qty'):
			 			qty = data.get('qty') - vmcr[0].get('qty')

			 			gain = make_stock_adjust(
			 				purpose='Material Transfer',
			 				message="Stock Transfer to Edited Gain",
			 				vlcc=vlcc,data=data,qty=qty,
			 				t_warehouse=vlcc_wh.get('edited_gain'),
			 				s_warehouse=vlcc_wh.get('warehouse'))

			 		elif data.get('qty') < vmcr[0].get('qty'):
			 			qty = vmcr[0].get('qty') - data.get('qty')

			 			loss = make_stock_adjust(
			 				purpose='Material Receipt',
			 				message="Stock In to Edited Loss",
			 				vlcc=vlcc,data=data,qty=qty,
			 				t_warehouse=vlcc_wh.get('edited_loss'),
			 				s_warehouse=None)

			 			loss_transfer = make_stock_adjust(
			 				purpose='Material Transfer',
			 				message="Stock Transfer to Main Warehouse",
			 				vlcc=vlcc,data=data,qty=loss,
			 				t_warehouse=vlcc_wh.get('warehouse'),
			 				s_warehouse=vlcc_wh.get('edited_loss'))

def make_stock_adjust(purpose,message,vlcc,data,qty,t_warehouse,s_warehouse):
	try:
		company_details = frappe.db.get_value("Company",{"name":vlcc},['default_payable_account','abbr','cost_center'],as_dict=1)
		remarks,response_dict = {} ,{}
		item_code = ""
		fmcr = data.get('fmcr').split(',') if data else []


		amcu_api.create_item(data)
		amcu_api.make_uom_config("Nos")
	
		if data.get('milktype') == "COW":
			item_code = "COW Milk"
		elif data.get('milktype') == "BUFFALO":
			item_code = "BUFFALO Milk"

		item_ = frappe.get_doc("Item",item_code)

		stock_doc = frappe.new_doc("Stock Entry")
		stock_doc.purpose =  purpose
		stock_doc.company = vlcc
		remarks.update({"Farmer ID":data.get('farmerid'),
			"Rcvd Time":data.get('rcvdtime'),"Message": message,"shift":data.get('shift')})
		stock_doc.remarks = "\n".join("{}: {}".format(k, v) for k, v in remarks.items())
		stock_doc.append("items",
			{
				"item_code": item_.item_code,
				"item_name": item_.item_code,
				"description": item_.item_code,
				"uom": "Litre",
				"qty": qty,
				"s_warehouse": s_warehouse,
				"t_warehouse": t_warehouse,
				"cost_center":company_details.get('cost_center'),
				"basic_rate": data.get('rate')
			}
		)
		stock_doc.flags.ignore_permissions = True
		stock_doc.flags.is_api = True
		stock_doc.submit()

		set_flag_fmcr(fmcr_list=fmcr,is_fmcr_updated=1)	

		return qty

	except Exception,e:
		utils.make_dairy_log(title="Schedular Error",method="make_stock_adjust", status="Error",
		data=message ,message=e, traceback=frappe.get_traceback())


def set_flag_fmcr(fmcr_list,is_fmcr_updated):

	if fmcr_list:
		for data in fmcr_list:
			fmcr_doc = frappe.get_doc('Farmer Milk Collection Record',data)
			fmcr_doc.is_fmrc_updated = is_fmcr_updated
			fmcr_doc.flags.ignore_permissions = True
			fmcr_doc.save()