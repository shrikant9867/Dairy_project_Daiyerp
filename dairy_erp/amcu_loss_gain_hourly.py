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
	fmcr_stock_qty = 0

	try:
		fmcr_records = frappe.db.sql("""select name,sum(milkquantity) as qty,societyid, 
									min(collectiontime) as min_time,shift,milktype  
									from   
										`tabFarmer Milk Collection Record` 
									where  
										is_fmrc_updated = 0 and docstatus = 1 
									group by societyid,date(collectiontime),
									shift,milktype order by collectiontime""",as_dict=True)

		fmcr_data = fmcr_records[0].get('qty') if fmcr_records and fmcr_records[0].get('qty') else []
		if fmcr_data:
			for fmcr in fmcr_records:
				vlcc = frappe.db.get_value("Village Level Collection Centre",
					{"amcu_id":fmcr.get('societyid')},["name","chilling_centre",
					"warehouse","edited_gain","edited_loss"],as_dict=True) or {}
				config_hrs = frappe.db.get_value('VLCC Settings',{'vlcc':vlcc.get('name')},'hours') or 0
				min_time = get_datetime(fmcr.get('min_time')) + timedelta(hours=int(config_hrs))
				if now_datetime() > min_time:
					actual_fmcr = frappe.db.sql("""select ifnull(sum(fmcr_qty),0) as qty
								from 
									`tabFMCR Quantity Log`
								where 
									purpose = 'Actual Qty of FMCR' and
									is_scheduler = 0 and 
									shift = %s and vlcc = %s and
									milktype = %s and 
									collectiontime = %s""",(fmcr.get('shift'),
									vlcc.get('name'),fmcr.get('milktype'),
									getdate(fmcr.get('min_time'))),as_dict=1,debug=0)
					actual_fmcr_qty = actual_fmcr[0].get('qty') if actual_fmcr and actual_fmcr[0].get('qty') else 0
					if actual_fmcr_qty:
						loss_gain_computation(actual_fmcr_qty=actual_fmcr_qty,
							edited_fmcr_qty=fmcr.get('qty'),vlcc=vlcc,fmcr=fmcr)
				
	except Exception,e:
		utils.make_dairy_log(title="Scheduler Error",method="get_fmcr_hourly", 
		status="Error",data=message ,message=e, traceback=frappe.get_traceback())
	

def loss_gain_computation(actual_fmcr_qty,edited_fmcr_qty,vlcc,fmcr):

	if flt(actual_fmcr_qty,2) < flt(edited_fmcr_qty,2):
		qty = flt(edited_fmcr_qty,2) - flt(actual_fmcr_qty,2)
		make_stock_adjust(
				purpose='Material Transfer',
				message="Stock Transfer to Edited Gain",
				vlcc=vlcc,fmcr=fmcr,qty=qty,actual_fmcr_qty=actual_fmcr_qty,
				t_warehouse=vlcc.get('edited_gain'),
				s_warehouse=vlcc.get('warehouse'))

	elif flt(actual_fmcr_qty,2) > flt(edited_fmcr_qty,2):
		
		qty = flt(actual_fmcr_qty,2) - flt(edited_fmcr_qty,2)
		make_stock_adjust(
				purpose='Material Receipt',
				message="Stock In to Edited Loss",
				vlcc=vlcc,fmcr=fmcr,qty=qty,actual_fmcr_qty=actual_fmcr_qty,
				t_warehouse=vlcc.get('edited_loss'))

	elif flt(actual_fmcr_qty,2) == flt(edited_fmcr_qty,2):
			set_flag(fmcr)
			make_farmer_edition_log(fmcr=fmcr,
									edited_stock_entry = "Quantity Balanced",
									actual_fmcr_qty=actual_fmcr_qty)

def make_stock_adjust(purpose,message,vlcc,fmcr,qty,actual_fmcr_qty,t_warehouse,s_warehouse=None):
	try:
		company_details = frappe.db.get_value("Company",{"name":vlcc.get('name')},
			['default_payable_account','abbr','cost_center'],as_dict=1)
		remarks,response_dict = {} ,{}
		item_code = ""

		amcu_api.create_item(fmcr)
		amcu_api.make_uom_config("Nos")
	
		if fmcr.get('milktype') == "COW":
			item_code = "COW Milk"
		elif fmcr.get('milktype') == "BUFFALO":
			item_code = "BUFFALO Milk"

		item_ = frappe.get_doc("Item",item_code)

		stock_doc = frappe.new_doc("Stock Entry")
		stock_doc.purpose =  purpose
		stock_doc.company = vlcc.get('name')
		remarks.update({"Farmer ID":fmcr.get('farmerid'),
			"Rcvd Time":fmcr.get('min_time'),"Message": message,"shift":fmcr.get('shift')})
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
				"basic_rate": fmcr.get('rate')
			}
		)
		stock_doc.flags.ignore_permissions = True
		stock_doc.flags.is_api = True
		stock_doc.submit()	

		set_flag(fmcr)
		make_farmer_edition_log(fmcr=fmcr,
								edited_stock_entry=stock_doc.name,
								edited_loss_gain=qty,actual_fmcr_qty=actual_fmcr_qty)

		return qty

	except Exception,e:
		utils.make_dairy_log(title="Scheduler Error",method="make_stock_adjust", status="Error",
		data=message ,message=e, traceback=frappe.get_traceback())


def make_farmer_edition_log(fmcr,edited_stock_entry,actual_fmcr_qty,edited_loss_gain=0):
	
	edition_log = frappe.new_doc("Farmer Edition Log")
	edition_log.edited_qty = fmcr.get('qty')
	edition_log.actual_fmcr_qty = actual_fmcr_qty
	edition_log.edited_loss_gain = edited_loss_gain
	edition_log.stock_entry = edited_stock_entry
	edition_log.vlcc = fmcr.get('societyid')
	edition_log.flags.ignore_permissions = True
	edition_log.save()

def set_flag(fmcr):
	vlcc = frappe.db.get_value("Village Collection Level Centre",{"amcu_id":fmcr.get('societyid')},"name")
	frappe.db.sql("""update 
						`tabFarmer Milk Collection Record`
					set 
						is_fmrc_updated = 1,is_stock_settled=1
					where  
						docstatus = 1 and 
						shift = '{0}' and milktype = '{1}' and 
						date(collectiontime) = '{2}' and societyid = '{3}' """.
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('min_time')),fmcr.get('societyid')))

	frappe.db.sql("""update 
						`tabFMCR Quantity Log`
					set 
						is_scheduler = 1
					where 
						purpose = 'Actual Qty of FMCR' and 
						shift = %s and vlcc = %s and
						milktype = %s and 
						collectiontime = %s""",(fmcr.get('shift'),vlcc,
						fmcr.get('milktype'),getdate(fmcr.get('min_time'))))
	

def check_hourly_dairy_log():
	utils.make_dairy_log(title="Scheduler Checking for 1Hour",method="make_stock_adjust", status="Success",
		data="test Scheduler" ,message= "Stock Adjustment" , traceback="Scheduler")