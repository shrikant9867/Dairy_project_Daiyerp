from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import timedelta
from frappe.utils import flt, cstr, cint
import dairy_utils as utils
import amcu_api as amcu_api
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate

def get_fmcr_hourly():

	check_hourly_dairy_log()
	message = ""
	try:
		fmcr = frappe.db.sql("""select name,sum(milkquantity) as qty,rate,societyid,
								rcvdtime,shift,milktype,farmerid,GROUP_CONCAT(name) as fmcr
				 	from 
					 	`tabFarmer Milk Collection Record`
					where 
						is_fmrc_updated = 0 and docstatus = 1
					group by societyid,date(rcvdtime),shift,milktype
					order by rcvdtime""",as_dict=True,debug=0)

		if len(fmcr):
			for data in fmcr:
				min_time = frappe.db.sql("""select min(rcvdtime) as rcvdtime
						 	from 
							 	`tabFarmer Milk Collection Record`
							where 
								docstatus = 1 and date(rcvdtime) = '{0}' and 
								shift = '{1}' and milktype = '{2}' and societyid = '{3}'
								""".
								format(getdate(data.get('rcvdtime')),
									data.get('shift'),data.get('milktype'),
									data.get('societyid')),as_dict=True,debug=0)

				data.update({"min_time":min_time[0].get('rcvdtime')})

				vmcr = frappe.db.sql("""select name,sum(milkquantity) as qty,
										rcvdtime,shift,farmerid,GROUP_CONCAT(name) as vmcr
			 					from 
			 						`tabVlcc Milk Collection Record` 
			 					where 
			 						shift = '{0}' and milktype = '{1}' and 
			 						date(rcvdtime) = '{2}' and farmerid = '{3}' and
			 						docstatus = 1 and is_scheduler = 0
			 					group by societyid 
			 					order by rcvdtime
			 	""".format(data.get('shift'),data.get('milktype'),
			 		getdate(data.get('rcvdtime')),
			 		data.get('societyid')),as_dict=1,debug=0)
			 	
			 	vlcc = frappe.db.get_value("Village Level Collection Centre",
			 				{"amcu_id":data.get('societyid')},"name")
				vlcc_wh = frappe.db.get_value("Village Level Collection Centre",vlcc,
						["warehouse","edited_gain","edited_loss"],as_dict=1) or {}
			 	config_hrs = frappe.db.get_value('VLCC Settings',{'vlcc':vlcc},'hours') or 0
			 	min_time = get_datetime(data.get('min_time')) + timedelta(hours=int(config_hrs))
			 	fmcr = data.get('fmcr').split(',') if data else []
			 	if now_datetime() < min_time: 
			 		pass
			 	elif now_datetime() > min_time: 
				 	if len(vmcr):
		 				se = frappe.db.get_value('Stock Entry',{'vmcr':vmcr[0].get('name')},['name','wh_type'],as_dict=1) or {}
	 					se_qty = frappe.db.get_value('Stock Entry Detail',{'parent':se.get('name')},'qty') or 0

	 					if se.get('wh_type') == 'Loss':
	 						loss_gain_qty = data.get('qty') - se_qty
	 						if loss_gain_qty > vmcr[0].get('qty'):
	 							qty = loss_gain_qty - vmcr[0].get('qty')
	 							gain = make_stock_adjust(
				 				purpose='Material Transfer',
				 				message="Stock Transfer to Edited Gain",
				 				vlcc=vlcc,data=data,qty=qty,vmcr=vmcr[0].get('name'),
				 				t_warehouse=vlcc_wh.get('edited_gain'),
				 				s_warehouse=vlcc_wh.get('warehouse'))
				 				set_flag_fmcr(fmcr_list=fmcr,is_fmcr_updated=1)
								set_flag_vmcr(vmcr=vmcr[0].get('name'),is_scheduler=1)

	 						elif loss_gain_qty < vmcr[0].get('qty'):
	 							qty = vmcr[0].get('qty') - loss_gain_qty
				 				loss = make_stock_adjust(
				 				purpose='Material Receipt',
				 				message="Stock In to Edited Loss",
				 				vlcc=vlcc,data=data,qty=qty,vmcr=vmcr[0].get('name'),
				 				t_warehouse=vlcc_wh.get('edited_loss'),
				 				s_warehouse=None)
				 				set_flag_fmcr(fmcr_list=fmcr,is_fmcr_updated=1)
								set_flag_vmcr(vmcr=vmcr[0].get('name'),is_scheduler=1)

							elif loss_gain_qty == vmcr[0].get('qty'):
					 			set_flag_fmcr(fmcr_list=fmcr,is_fmcr_updated=1)
								set_flag_vmcr(vmcr=vmcr[0].get('name'),is_scheduler=1)
								utils.make_dairy_log(title="Quantity Balanced",method="make_stock_adjust", status="Success",
									data="Qty" ,message= "Quantity is Balanced so stock entry is not created" , traceback="Scheduler")

	 					elif se.get('wh_type') == 'Gain':
	 						loss_gain_qty = data.get('qty') + se_qty
	 						if loss_gain_qty > vmcr[0].get('qty'):
	 							qty = loss_gain_qty - vmcr[0].get('qty')
	 							gain = make_stock_adjust(
				 				purpose='Material Transfer',
				 				message="Stock Transfer to Edited Gain",
				 				vlcc=vlcc,data=data,qty=qty,vmcr=vmcr[0].get('name'),
				 				t_warehouse=vlcc_wh.get('edited_gain'),
				 				s_warehouse=vlcc_wh.get('warehouse'))
				 				set_flag_fmcr(fmcr_list=fmcr,is_fmcr_updated=1)
								set_flag_vmcr(vmcr=vmcr[0].get('name'),is_scheduler=1)

	 						elif loss_gain_qty < vmcr[0].get('qty'):
	 							qty = vmcr[0].get('qty') - loss_gain_qty
	 							loss = make_stock_adjust(
				 				purpose='Material Receipt',
				 				message="Stock In to Edited Loss",
				 				vlcc=vlcc,data=data,qty=qty,vmcr=vmcr[0].get('name'),
				 				t_warehouse=vlcc_wh.get('edited_loss'),
				 				s_warehouse=None)
				 				set_flag_fmcr(fmcr_list=fmcr,is_fmcr_updated=1)
								set_flag_vmcr(vmcr=vmcr[0].get('name'),is_scheduler=1)

					 		elif loss_gain_qty == vmcr[0].get('qty'):
					 			set_flag_fmcr(fmcr_list=fmcr,is_fmcr_updated=1)
								set_flag_vmcr(vmcr=vmcr[0].get('name'),is_scheduler=1)
								utils.make_dairy_log(title="Quantity Balanced",method="make_stock_adjust", status="Success",
									data="Qty" ,message= "Quantity is Balanced so stock entry is not created" , traceback="Scheduler")
	except Exception,e:
		utils.make_dairy_log(title="Scheduler Error",method="get_fmcr_hourly", status="Error",
		data=message ,message=e, traceback=frappe.get_traceback())

def make_stock_adjust(purpose,message,vlcc,data,qty,vmcr,t_warehouse,s_warehouse):
	try:
		company_details = frappe.db.get_value("Company",{"name":vlcc},['default_payable_account','abbr','cost_center'],as_dict=1)
		remarks,response_dict = {} ,{}
		item_code = ""

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

		utils.make_dairy_log(title="Stock Entry Created",method="make_stock_adjust", status="Success",
		data=stock_doc.name ,message= "Stock Adjustment" , traceback="Scheduler")

		return qty

	except Exception,e:
		utils.make_dairy_log(title="Scheduler Error",method="make_stock_adjust", status="Error",
		data=message ,message=e, traceback=frappe.get_traceback())


def set_flag_fmcr(fmcr_list,is_fmcr_updated):

	if fmcr_list:
		for data in fmcr_list:
			fmcr_doc = frappe.get_doc('Farmer Milk Collection Record',data)
			fmcr_doc.is_fmrc_updated = is_fmcr_updated
			fmcr_doc.flags.ignore_permissions = True
			fmcr_doc.save()

def set_flag_vmcr(vmcr,is_scheduler):
	if vmcr:
		frappe.db.set_value("Vlcc Milk Collection Record",vmcr,"is_scheduler",is_scheduler)

def check_hourly_dairy_log():
	utils.make_dairy_log(title="Scheduler Checking for 1Hour",method="make_stock_adjust", status="Success",
		data="test Scheduler" ,message= "Stock Adjustment" , traceback="Scheduler")