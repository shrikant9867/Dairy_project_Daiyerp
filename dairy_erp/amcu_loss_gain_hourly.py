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
									min(rcvdtime) as min_time,shift,milktype  
									from   
										`tabFarmer Milk Collection Record` 
									where  
										is_fmrc_updated = 0 and docstatus = 1 
									group by societyid,date(rcvdtime),
									shift,milktype order by rcvdtime""",as_dict=True)

		fmcr_data = fmcr_records[0].get('qty') if fmcr_records and fmcr_records[0].get('qty') else []
		if fmcr_data:
			for fmcr in fmcr_records:
				stock_record = frappe.db.sql("""select ifnull(sum(se.qty),0) as qty,
								s.shift,s.societyid,s.milktype,s.posting_date
							from 
								`tabStock Entry` s, `tabStock Entry Detail` se 
							where 
								s.name = se.parent
								and s.docstatus = 1 and s.is_scheduler = 0
								and s.is_reserved_farmer = 1 
								and s.shift = '{0}' and s.milktype = '{1}' and 
								s.posting_date = '{2}' and s.societyid = '{3}' 
							""".format(fmcr.get('shift'),fmcr.get('milktype'),
								getdate(fmcr.get('min_time')),
								fmcr.get('societyid')),as_dict=1,debug=0)

				fmcr_stock_qty = flt(fmcr.get('qty'),2) + flt(stock_record[0].get('qty'),2)
				if fmcr_stock_qty:
					loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,fmcr=fmcr,stock=stock_record)
				
	except Exception,e:
		utils.make_dairy_log(title="Scheduler Error",method="get_fmcr_hourly", 
		status="Error",data=message ,message=e, traceback=frappe.get_traceback())
	

def loss_gain_computation(fmcr_stock_qty,fmcr,stock=None):
	
	vlcc = frappe.db.get_value("Village Level Collection Centre",
		{"amcu_id":fmcr.get('societyid')},["name","chilling_centre",
		"warehouse","edited_gain","edited_loss"],as_dict=True) or {}
	cc = frappe.db.get_value("Address",vlcc.get('chilling_centre'),"centre_id")
	config_hrs = frappe.db.get_value('VLCC Settings',{'vlcc':vlcc.get('name')},'hours') or 0
	min_time = get_datetime(fmcr.get('min_time')) + timedelta(hours=int(config_hrs))
	
	if now_datetime() > min_time:
		vmcr_records = frappe.db.sql("""select name,sum(milkquantity) as qty,
								rcvdtime as recv_date,shift,farmerid,milktype
							from 
								`tabVlcc Milk Collection Record` 
							where 
								docstatus = 1 and is_scheduler = 0 and 
								shift = '{0}' and milktype = '{1}' and 
								date(rcvdtime) = '{2}' and farmerid = '{3}' and
								societyid = '{4}'
			""".format(fmcr.get('shift'),fmcr.get('milktype'),
				getdate(fmcr.get('min_time')),
				fmcr.get('societyid'),cc),as_dict=1,debug=0)

		vmcr_data = vmcr_records[0].get('qty') if vmcr_records and vmcr_records[0].get('qty') else []
		if vmcr_data:
			for vmcr in vmcr_records:
				se = frappe.db.get_value('Stock Entry',{'vmcr':vmcr.get('name')},
					['name','wh_type'],as_dict=1) or {}
				se_qty = frappe.db.get_value('Stock Entry Detail',
					{'parent':se.get('name')},'qty') or 0
				if se and se.get('wh_type') == 'Loss':

					loss_gain_qty = flt(fmcr_stock_qty,2) - flt(se_qty,2)

					if flt(loss_gain_qty,2) > flt(vmcr.get('qty'),2):
						qty = flt(loss_gain_qty,2) - flt(vmcr.get('qty'),2)
						gain = make_stock_adjust(
			 				purpose='Material Transfer',
			 				message="Stock Transfer to Edited Gain",
			 				vlcc=vlcc,fmcr=fmcr,qty=qty,
			 				vmcr_qty=vmcr.get('qty'),
			 				t_warehouse=vlcc.get('edited_gain'),se_qty=se_qty,
			 				s_warehouse=vlcc.get('warehouse'),stock=stock)

					elif flt(loss_gain_qty,2) < flt(vmcr.get('qty'),2):
						qty = flt(vmcr.get('qty'),2) - flt(loss_gain_qty,2)
						loss = make_stock_adjust(
			 				purpose='Material Receipt',
			 				message="Stock In to Edited Loss",
			 				vlcc=vlcc,fmcr=fmcr,qty=qty,
			 				vmcr_qty=vmcr.get('qty'),
			 				t_warehouse=vlcc.get('edited_loss'),
			 				se_qty=se_qty,stock=stock)

					elif flt(loss_gain_qty,2) == flt(vmcr.get('qty'),2):
						reserved_qty = stock[0].get('qty') if stock[0].get('qty') else 0
			 			set_flag(fmcr,vlcc)
			 			make_farmer_edition_log(fmcr=fmcr,
			 									edited_stock_entry = "Quantity Balanced",
			 									loss_gain_qty=se_qty,vmcr_qty=vmcr.get('qty'),
			 									edited_qty=0,reserved_qty=reserved_qty)

				elif se and se.get('wh_type') == 'Gain':

					loss_gain_qty = flt(fmcr_stock_qty,2) + flt(se_qty,2)

					if flt(loss_gain_qty,2) > flt(vmcr.get('qty'),2):
						qty = flt(loss_gain_qty,2) - flt(vmcr.get('qty'),2)
						gain = make_stock_adjust(
			 				purpose='Material Transfer',
			 				message="Stock Transfer to Edited Gain",
			 				vlcc=vlcc,fmcr=fmcr,qty=qty,
			 				vmcr_qty=vmcr.get('qty'),
			 				t_warehouse=vlcc.get('edited_gain'),se_qty=se_qty,
			 				s_warehouse=vlcc.get('warehouse'),stock=stock)

					elif flt(loss_gain_qty,2) < flt(vmcr.get('qty'),2):
						qty = flt(vmcr.get('qty'),2) - flt(loss_gain_qty,2)
						loss = make_stock_adjust(
			 				purpose='Material Receipt',
			 				message="Stock In to Edited Loss",
			 				vlcc=vlcc,fmcr=fmcr,qty=qty,
			 				vmcr_qty=vmcr.get('qty'),
			 				t_warehouse=vlcc.get('edited_loss'),
			 				se_qty=se_qty,stock=stock)

			 		elif flt(loss_gain_qty,2) == flt(vmcr.get('qty'),2):
			 			reserved_qty = stock[0].get('qty') if stock[0].get('qty') else 0
			 			set_flag(fmcr,vlcc)
			 			make_farmer_edition_log(fmcr=fmcr,
			 						edited_stock_entry = "Quantity Balanced",
			 						loss_gain_qty=se_qty,vmcr_qty=vmcr.get('qty'),
									edited_qty=0,reserved_qty=reserved_qty)
			 	else:
			 		if flt(fmcr_stock_qty,2) > flt(vmcr.get('qty'),2):
			 			qty = flt(fmcr_stock_qty,2) - flt(vmcr.get('qty'),2)
						gain = make_stock_adjust(
			 				purpose='Material Transfer',
			 				message="Stock Transfer to Edited Gain",
			 				vlcc=vlcc,fmcr=fmcr,qty=qty,
			 				vmcr_qty=vmcr.get('qty'),
			 				t_warehouse=vlcc.get('edited_gain'),se_qty=0,
			 				s_warehouse=vlcc.get('warehouse'),stock=stock)

					elif flt(fmcr_stock_qty,2) < flt(vmcr.get('qty'),2):
						qty = flt(vmcr.get('qty'),2) - flt(fmcr_stock_qty,2)
						loss = make_stock_adjust(
			 				purpose='Material Receipt',
			 				message="Stock In to Edited Loss",
			 				vlcc=vlcc,fmcr=fmcr,qty=qty,
			 				vmcr_qty=vmcr.get('qty'),
			 				t_warehouse=vlcc.get('edited_loss'),
			 				se_qty=0,stock=stock)

					elif flt(fmcr_stock_qty,2) == flt(vmcr.get('qty'),2):
			 			reserved_qty = stock[0].get('qty') if stock[0].get('qty') else 0
			 			set_flag(fmcr,vlcc)
			 			make_farmer_edition_log(fmcr=fmcr,
			 						edited_stock_entry = "Quantity Balanced",
			 						loss_gain_qty=0,vmcr_qty=vmcr.get('qty'),
									edited_qty=0,reserved_qty=reserved_qty)

def make_stock_adjust(purpose,message,vlcc,fmcr,qty,vmcr_qty,t_warehouse,se_qty,s_warehouse=None,stock=None):
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

		set_flag(fmcr,vlcc)
		reserved_qty = stock[0].get('qty') if stock[0].get('qty') else 0
		make_farmer_edition_log(fmcr=fmcr,
								edited_stock_entry=stock_doc.name,
								loss_gain_qty=se_qty,vmcr_qty=vmcr_qty,
								edited_qty=qty,reserved_qty=reserved_qty)

		return qty

	except Exception,e:
		utils.make_dairy_log(title="Scheduler Error",method="make_stock_adjust", status="Error",
		data=message ,message=e, traceback=frappe.get_traceback())


def make_farmer_edition_log(fmcr,edited_stock_entry,loss_gain_qty,vmcr_qty,edited_qty,reserved_qty):
	
	edition_log = frappe.new_doc("Farmer Edition Log")
	edition_log.fmcr_qty = fmcr.get('qty')
	edition_log.reserved_qty = reserved_qty
	edition_log.loss_gain_qty = loss_gain_qty
	edition_log.vmcr_qty = vmcr_qty
	edition_log.stock_entry = edited_stock_entry
	edition_log.edited_qty = edited_qty
	edition_log.vlcc = fmcr.get('societyid')
	edition_log.flags.ignore_permissions = True
	edition_log.save()

def set_flag(fmcr,vlcc):
	cc = frappe.db.get_value("Address",vlcc.get('chilling_centre'),"centre_id")
	frappe.db.sql("""update 
						`tabFarmer Milk Collection Record`
					set 
						is_fmrc_updated = 1,is_stock_settled=1
					where  
						docstatus = 1 and 
						shift = '{0}' and milktype = '{1}' and 
						date(rcvdtime) = '{2}' and societyid = '{3}' """.
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('min_time')),fmcr.get('societyid')))
	frappe.db.sql("""update 
						`tabStock Entry`
					set 
						is_scheduler = 1,is_stock_settled=1
					where  
						docstatus = 1 and is_reserved_farmer = 1 and
						shift = '{0}' and milktype = '{1}' and 
						posting_date = '{2}' and societyid = '{3}' """.
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('min_time')),fmcr.get('societyid')))
	frappe.db.sql("""update 
						`tabVlcc Milk Collection Record`
					set 
						is_scheduler = 1 
					where  
						docstatus = 1  and
						shift = '{0}' and milktype = '{1}' and 
						date(rcvdtime) = '{2}' and farmerid = '{3}' and 
						societyid = '{4}'""".
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('min_time')),fmcr.get('societyid'),
						cc))

def check_hourly_dairy_log():
	utils.make_dairy_log(title="Scheduler Checking for 1Hour",method="make_stock_adjust", status="Success",
		data="test Scheduler" ,message= "Stock Adjustment" , traceback="Scheduler")