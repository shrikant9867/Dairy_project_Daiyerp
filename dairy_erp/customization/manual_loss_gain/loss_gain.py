from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.data import to_timedelta
import time
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate,get_time
from frappe import _
from datetime import timedelta
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
import requests
import json
import dairy_erp.dairy_utils as utils

def handling_loss_gain(data,row,vmcr_doc):

	fmcr_stock_qty,local_sale_qty = 0,0
	se = ""
	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},"name")
	fmcr_record = frappe.db.sql("""select name,ifnull(sum(milkquantity),0) as qty,
								shift,milktype,fat,snf,rate,
								date(collectiontime) as collectiontime,societyid,farmerid
							from 
								`tabFarmer Milk Collection Record` 
							where 
								shift = '{0}' and milktype = '{1}' and 
								date(collectiontime) = '{2}' and societyid = '{3}' 
								and docstatus = 1 and is_stock_settled = 0
			""".format(data.get('shift'),row.get('milktype'),
				getdate(row.get('collectiontime')),row.get('farmerid')),as_dict=1,debug=0)

	stock_record = frappe.db.sql("""select s.name,ifnull(sum(se.qty),0) as qty ,
								s.shift,
								s.societyid,s.milktype,s.posting_date as collectiontime,
								s.farmer_id as farmerid
							from 
								`tabStock Entry` s, `tabStock Entry Detail` se 
							where 
								s.name = se.parent and 
								s.shift = '{0}' and s.milktype = '{1}' and 
								s.posting_date = '{2}' and s.societyid = '{3}' 
								and s.docstatus = 1 and s.is_stock_settled = 0
								and s.is_reserved_farmer = 1 
			""".format(data.get('shift'),row.get('milktype'),
				getdate(row.get('collectiontime')),
				row.get('farmerid')),as_dict=1,debug=0)

	fmcr_data = fmcr_record[0].get('qty') if fmcr_record and fmcr_record[0].get('qty') else []
	stock_data = stock_record[0].get('qty') if stock_record and stock_record[0].get('qty') else []
	local_sale_data = get_local_sale_data(row,data)
	if local_sale_data and local_sale_data[0].get('qty'):
		local_sale_qty = local_sale_data[0].get('qty')

	if fmcr_data:
		for fmcr in fmcr_record:
			stock_record = frappe.db.sql("""select ifnull(sum(se.qty),0) as qty ,
								s.shift,
								s.societyid,s.milktype,s.posting_date as collectiontime
							from 
								`tabStock Entry` s, `tabStock Entry Detail` se 
							where 
								s.name = se.parent and 
								s.shift = '{0}' and s.milktype = '{1}' and 
								s.posting_date = '{2}' and s.societyid = '{3}' 
								and s.docstatus = 1 and s.is_stock_settled = 0
								and s.is_reserved_farmer = 1 
			""".format(fmcr.get('shift'),fmcr.get('milktype'),
				getdate(fmcr.get('collectiontime')),
				fmcr.get('societyid')),as_dict=1,debug=0)

			fmcr_stock_qty = (flt(fmcr.get('qty'),2) + flt(stock_record[0].get('qty'),2)) - flt(local_sale_qty,2)
			
			se = loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,row=row,
						data=data,vmcr_doc=vmcr_doc,total_vmcr_qty=row.get('milkquantity'))
			make_fmcr_qty_log(data=data,row=row,stock_qty = stock_record[0].get('qty'),
				local_sale_qty=local_sale_qty,fmcr_qty=fmcr.get('qty'))
		set_flag(fmcr,vlcc)

	elif stock_data:
		for stock in stock_record:
			fmcr_stock_qty = flt(stock.get('qty'),2) - flt(local_sale_qty,2)
			se = loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,row=row,data=data,
				vmcr_doc=vmcr_doc,stock=stock,total_vmcr_qty=row.get('milkquantity'))
			make_fmcr_qty_log(data=data,row=row,stock_qty=stock.get('qty')
				,local_sale_qty=local_sale_qty)
		set_se_flag(stock,vlcc)
	else:
		create_loss_gain(fmcr_stock_qty=fmcr_stock_qty,row=row,
						data=data,vmcr_doc=vmcr_doc)
	return se


def get_local_sale_data(row,data):

	item_code = ""
	if row.get('milktype') == "COW":
		item_code = "COW Milk"
	elif row.get('milktype') == "BUFFALO":
		item_code = "BUFFALO Milk"
	vlcc = frappe.db.get_value("Village Level Collection Centre", {"amcu_id": row.get('farmerid')}, 'name')

	return frappe.db.sql("""select ifnull(sum(si.qty),0) as qty  
					from 
						`tabSales Invoice Item` si,
						`tabSales Invoice` s 
					where 
						s.name= si.parent and 
						s.docstatus = 1 and
						s.local_sale = 1 and
						si.is_stock_settled = 0 and
						si.item_code = '{0}' and
						s.posting_date = '{1}' and s.shift = '{2}' and s.company = '{3}'
						""".format(item_code,getdate(row.get('collectiontime')),
							data.get('shift'),vlcc),as_dict=True,debug=0)


def create_loss_gain(fmcr_stock_qty,row,data,vmcr_doc,stock=None):
	se = frappe.db.get_value("Stock Entry",{"milktype":row.get('milktype'),
		"shift":data.get('shift'),"posting_date":getdate(row.get('collectiontime')),
		"farmer_id":row.get('farmerid'),"societyid":data.get('societyid'),"docstatus":1,
		"wh_type":('in', ['Loss','Gain'])},"name")

	if se:
		se_doc = frappe.get_doc("Stock Entry",se)
		se_qty = frappe.db.get_value("Stock Entry Detail",{"parent":se},"qty") or 0
		actual_fmcr_qty = flt(get_actual_fmcr_qty(data,row),2)
		if se_doc.wh_type == 'Loss':
			total_vmcr_qty = flt((actual_fmcr_qty - se_qty + row.get('milkquantity')),2)
			loss_gain_computation(actual_fmcr_qty,row,data,vmcr_doc,stock,total_vmcr_qty)
			cancel_se(se)
		elif se_doc.wh_type == 'Gain':
			total_vmcr_qty =  flt((actual_fmcr_qty + se_qty + row.get('milkquantity')),2)
			loss_gain_computation(actual_fmcr_qty,row,data,vmcr_doc,stock,total_vmcr_qty)
			cancel_se(se)

def get_actual_fmcr_qty(data,row):

	actual_qty = 0
	vlcc = frappe.db.get_value("Village Level Collection Centre",
		{"amcu_id":row.get('farmerid')},
		["name","warehouse","handling_loss","calibration_gain"],as_dict=True)

	qty = frappe.db.sql("""select ifnull(sum(fmcr_qty),0) as qty
						from 
							`tabFMCR Quantity Log`
						where 
							purpose = 'Actual Qty of FMCR' and
							shift = %s and vlcc = %s and 
							milktype = %s and 
							collectiontime = %s""",(data.get('shift'),
							vlcc.get('name'),row.get('milktype'),
							getdate(row.get('collectiontime'))),as_dict=1,debug=0)
	if qty and qty[0].get('qty'):
		actual_qty = qty[0].get('qty')
	return actual_qty

def cancel_se(se):
	se_doc = frappe.get_doc("Stock Entry",se)
	se_doc.cancel()

def loss_gain_computation(fmcr_stock_qty,row,data,vmcr_doc,stock=None,total_vmcr_qty=0):

	se = ""
	vlcc = frappe.db.get_value("Village Level Collection Centre",
		{"amcu_id":row.get('farmerid')},
		["name","warehouse","handling_loss","calibration_gain"],as_dict=True)
	if fmcr_stock_qty:
		if flt(fmcr_stock_qty,2) > flt(total_vmcr_qty,2):
			qty = flt(fmcr_stock_qty,2) - flt(total_vmcr_qty)
			se = make_stock_receipt(
				message="Material Receipt for Handling Loss",method="handling_loss",
				data=data,row=row,
				qty=qty,warehouse=vlcc.get('handling_loss'),s_warehouse=vlcc.get('warehouse'),
				societyid=row.get('farmerid'),vmcr_doc=vmcr_doc)
		
		elif flt(fmcr_stock_qty,2) < flt(total_vmcr_qty,2):
			qty = flt(total_vmcr_qty) - flt(fmcr_stock_qty,2)
			se = make_stock_receipt(
				message="Material Receipt for Calibration Gain",
				method="handling_gain",data=data,row=row,
				qty=qty,warehouse=vlcc.get('calibration_gain'),s_warehouse=vlcc.get('warehouse'),
				societyid=row.get('farmerid'),vmcr_doc=vmcr_doc)
		
		elif flt(fmcr_stock_qty,2) == flt(total_vmcr_qty,2):
			utils.make_dairy_log(title="Quantity Balanced after VMCR Creation",
				method="handling_loss_gain", status="Success",data="Qty" ,
				message= "Quantity is Balanced so stock entry is not created",
				traceback="Manual VMCR")
	return se

def make_fmcr_qty_log(data,row,stock_qty,local_sale_qty,fmcr_qty=0):

	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},"name")
	if not frappe.db.get_value("FMCR Quantity Log",{"purpose":"Acutual Qty of FMCR",
		"shift":data.get('shift'),"vlcc":vlcc,"milktype":row.get('milktype'),
		"collectiontime":getdate(row.get('collectiontime'))},"name"):

		fmcr_qty_doc = frappe.new_doc("FMCR Quantity Log")
		fmcr_qty_doc.purpose = 'Actual Qty of FMCR'
		fmcr_qty_doc.vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},"name")
		fmcr_qty_doc.shift = data.get('shift')
		fmcr_qty_doc.milktype = row.get('milktype')
		fmcr_qty_doc.collectiontime  = getdate(row.get('collectiontime'))
		fmcr_qty_doc.fmcr_qty = flt(fmcr_qty,2)
		fmcr_qty_doc.flags.ignore_permissions = True
		fmcr_qty_doc.save()
	else:
		utils.make_dairy_log(title="FMCR Quantity Log",
				method="make_fmcr_qty_log", status="Success",data="Qty" ,
				message= "FMCR Quantity Log not creted since Record is already present",
				traceback="Manual VMCR")

def set_flag(fmcr,vlcc):
	vlcc_cc = frappe.db.get_value("Village Level Collection Centre",vlcc,"chilling_centre")
	cc = frappe.db.get_value("Address",vlcc_cc,"centre_id")
	frappe.db.sql("""update 
						`tabFarmer Milk Collection Record`
					set 
						is_stock_settled=1
					where  
						docstatus = 1 and 
						shift = '{0}' and milktype = '{1}' and 
						date(collectiontime) = '{2}' and societyid = '{3}' """.
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('collectiontime')),fmcr.get('societyid')))
	frappe.db.sql("""update 
						`tabStock Entry`
					set 
						is_stock_settled=1
					where  
						docstatus = 1 and is_reserved_farmer = 1 and
						shift = '{0}' and milktype = '{1}' and 
						posting_date = '{2}' and societyid = '{3}' """.
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('collectiontime')),fmcr.get('societyid')))
	frappe.db.sql("""update 
						`tabVlcc Milk Collection Record`
					set 
						is_stock_settled = 1 
					where  
						docstatus = 1  and
						shift = '{0}' and milktype = '{1}' and 
						date(collectiontime) = '{2}' and farmerid = '{3}' and 
						societyid = '{4}'""".
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('collectiontime')),fmcr.get('societyid'),
						cc))
	set_local_sale_flag(fmcr,vlcc)


def set_se_flag(stock,vlcc):
	#if quantity is balanced or stock  entry is individual

	vlcc_cc = frappe.db.get_value("Village Level Collection Centre",vlcc,"chilling_centre")
	cc = frappe.db.get_value("Address",vlcc_cc,"centre_id")
	frappe.db.sql("""update 
						`tabStock Entry`
					set 
						is_stock_settled=1,is_scheduler = 1
					where  
						docstatus = 1 and is_reserved_farmer = 1 and
						shift = '{0}' and milktype = '{1}' and 
						posting_date = '{2}' and societyid = '{3}' """.
						format(stock.get('shift'),stock.get('milktype'),
						getdate(stock.get('posting_date')),stock.get('societyid')))
	frappe.db.sql("""update 
						`tabVlcc Milk Collection Record`
					set 
						is_stock_settled = 1,is_scheduler = 1
					where  
						docstatus = 1  and
						shift = '{0}' and milktype = '{1}' and 
						date(collectiontime) = '{2}' and farmerid = '{3}' and 
						societyid = '{4}'""".
						format(stock.get('shift'),stock.get('milktype'),
						getdate(stock.get('posting_date')),stock.get('societyid'),
						cc))
	set_local_sale_flag(stock,vlcc)

def set_local_sale_flag(fmcr,vlcc):
	item_code = ""
	if fmcr.get('milktype') == "COW":
		item_code = "COW Milk"
	elif fmcr.get('milktype') == "BUFFALO":
		item_code = "BUFFALO Milk"

	frappe.db.sql("""update 
						`tabSales Invoice Item` si, 
						`tabSales Invoice` s  
					set 
						si.is_stock_settled = 1 
					where  
						s.name= si.parent and  
						s.docstatus = 1 and 
						s.local_sale = 1 and 
						si.item_code = '{0}' 
						and s.posting_date = '{1}' 
						and s.shift = '{2}' 
						and s.company = '{3}'""".format(item_code,
							getdate(fmcr.get('collectiontime')),fmcr.get('shift'),vlcc))

def set_fmcr_log_flag(data,row):
	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},"name")
	frappe.db.sql("""update 
						`tabFMCR Quantity Log`
					set 
						is_stock_settled = 1
					where 
						purpose = 'Actual Qty of FMCR' and 
						shift = %s and vlcc = %s and
						milktype = %s and 
						collectiontime = %s""",(data.get('shift'),
							vlcc,row.get('milktype'),
							getdate(row.get('collectiontime'))))

def make_stock_receipt(message,method,data,row,qty,warehouse,s_warehouse,societyid,vmcr_doc=None,fmcr=None):

	try:
		item_code = ""
		stock_doc = ""
	
		create_item(row)
		make_uom_config("Litre")

		if row.get('milktype') == "COW":
			item_code = "COW Milk"
		elif row.get('milktype') == "BUFFALO":
			item_code = "BUFFALO Milk"

		item_ = frappe.get_doc("Item",item_code)

		if method == 'create_fmrc':
			if not frappe.db.get_value('Stock Entry',
				{"transaction_id":row.get('transactionid')},"name"):
				stock_doc = stock_entry_creation(message,item_,method,data,row,qty,warehouse,s_warehouse,societyid,vmcr_doc,fmcr)
		else:
			stock_doc = stock_entry_creation(message,item_,method,data,row,qty,warehouse,s_warehouse,societyid,vmcr_doc,fmcr)	
		return stock_doc
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method=method, status="Error",
		data = data, message=e, traceback=frappe.get_traceback())

def stock_entry_creation(message,item_,method,data,row,qty,warehouse,s_warehouse,societyid,vmcr_doc,fmcr):

	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":societyid},["name","warehouse"],as_dict=True)
	company_details = frappe.db.get_value("Company",{"name":vlcc.get('name')},['default_payable_account','abbr','cost_center'],as_dict=1)
	remarks = {}
	farmerid = ""

	stock_doc = frappe.new_doc("Stock Entry")
	stock_doc.purpose =  "Material Receipt"
	stock_doc.company = vlcc.get('name')
	stock_doc.fmcr = fmcr.name if method == 'handling_loss_after_vmcr' or method == 'handling_gain_after_vmcr' else ""
	stock_doc.vmcr = vmcr_doc.name if method == 'handling_loss' or method == 'handling_gain' else ""
	if method == 'handling_loss' or method == 'handling_loss_after_vmcr':
		stock_doc.wh_type = 'Loss'
		stock_doc.purpose = 'Material Transfer'
	elif method == 'handling_gain' or method == 'handling_gain_after_vmcr':
		stock_doc.wh_type = 'Gain'

	stock_doc.shift = data.get('shift')
	stock_doc.milktype = row.get('milktype')
	stock_doc.societyid = data.get('societyid')
	stock_doc.is_reserved_farmer = 1 if method == "create_fmrc" else 0
	stock_doc.farmer_id = row.get('farmerid')

	if data.get('shift') == 'EVENING':
		farmerid = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},"longformatsocietyid_e")
	else:
		farmerid = row.get('longformatfarmerid')

	stock_doc.long_format_id = farmerid
	stock_doc.fat = row.get('fat')
	stock_doc.snf = row.get('snf')
	stock_doc.clr = row.get('clr')
	remarks.update({"Farmer ID":row.get('farmerid'),"Transaction Id":row.get('transactionid'),
		"Collection Time":row.get('collectiontime'),"Message": message,"shift":data.get('shift')})
	stock_doc.remarks = "\n".join("{}: {}".format(k, v) for k, v in remarks.items())
	stock_doc_item = {
		"item_code": item_.item_code,
		"item_name": item_.item_code,
		"description": item_.item_code,
		"uom": "Litre",
		"qty": qty,
		"t_warehouse": warehouse,
		"cost_center":company_details.get('cost_center'),
		"basic_rate": row.get('rate')
	}
	if method == 'handling_loss' or method == 'handling_loss_after_vmcr':
		stock_doc_item['s_warehouse'] = s_warehouse
	
	stock_doc.append("items",stock_doc_item)
	stock_doc.flags.ignore_permissions = True
	stock_doc.flags.is_api = True
	stock_doc.submit()
	if row.get('collectiontime'):
		frappe.db.sql("""update `tabStock Entry` 
			set 
				posting_date = '{0}',posting_time = '{1}'
			where 
				name = '{2}'""".format(getdate(row.get('collectiontime')),
					get_time(row.get('collectiontime')),stock_doc.name))
		frappe.db.sql("""update `tabGL Entry` 
			set 
				posting_date = %s
			where 
				voucher_no = %s""",(getdate(row.get('collectiontime')),stock_doc.name))
		frappe.db.sql("""update `tabStock Ledger Entry` 
			set 
				posting_date = %s
			where 
				voucher_no = %s""",(getdate(row.get('collectiontime')),stock_doc.name))
	return stock_doc

def create_item(row):

	if row.get('milktype') and not frappe.db.exists('Item', row.get('milktype')+" Milk"):
		item = frappe.new_doc("Item")
		item.item_code = row.get('milktype')+" Milk"
		item.item_group = "Milk & Products"
		item.weight_uom = "Litre"
		item.is_stock_item = 1
		item.flags.ignore_permissions = True
		item.insert()

def make_uom_config(doc):
	uom_obj = frappe.get_doc("UOM",doc)
	uom_obj.must_be_whole_number = 0
	uom_obj.flags.ignore_permissions = True
	uom_obj.save()