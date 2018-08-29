from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate
from frappe import _
import dairy_utils as utils
from datetime import timedelta
from amcu_resv_farmer_api import make_stock_receipt
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
import requests
import json


def handling_loss_gain(data,row,vmcr_doc,response_dict):

	fmcr_stock_qty = 0
	fmcr_record = frappe.db.sql("""select ifnull(sum(milkquantity),0) as qty,
								shift,milktype,
								date(rcvdtime) as recv_date,societyid
							from 
								`tabFarmer Milk Collection Record` 
							where 
								shift = '{0}' and milktype = '{1}' and 
								date(rcvdtime) = '{2}' and societyid = '{3}' 
								and docstatus = 1 and is_stock_settled = 0
			""".format(data.get('shift'),row.get('milktype'),
				getdate(data.get('rcvdtime')),row.get('farmerid')),as_dict=1,debug=0)

	stock_record = frappe.db.sql("""select ifnull(sum(se.qty),0) as qty ,
								s.shift,
								s.societyid,s.milktype,s.posting_date
							from 
								`tabStock Entry` s, `tabStock Entry Detail` se 
							where 
								s.name = se.parent and 
								s.shift = '{0}' and s.milktype = '{1}' and 
								s.posting_date = '{2}' and s.societyid = '{3}' 
								and s.docstatus = 1 and s.is_stock_settled = 0
								and s.is_reserved_farmer = 1 
			""".format(data.get('shift'),row.get('milktype'),
				getdate(data.get('rcvdtime')),
				row.get('farmerid')),as_dict=1,debug=0)

	fmcr_data = fmcr_record[0].get('qty') if fmcr_record and fmcr_record[0].get('qty') else []
	stock_data = stock_record[0].get('qty') if stock_record and stock_record[0].get('qty') else []

	if fmcr_data:
		for fmcr in fmcr_record:
			stock_record = frappe.db.sql("""select ifnull(sum(se.qty),0) as qty ,
								s.shift,
								s.societyid,s.milktype,s.posting_date
							from 
								`tabStock Entry` s, `tabStock Entry Detail` se 
							where 
								s.name = se.parent and 
								s.shift = '{0}' and s.milktype = '{1}' and 
								s.posting_date = '{2}' and s.societyid = '{3}' 
								and s.docstatus = 1 and s.is_stock_settled = 0
								and s.is_reserved_farmer = 1 
			""".format(fmcr.get('shift'),fmcr.get('milktype'),
				getdate(fmcr.get('recv_date')),
				fmcr.get('societyid')),as_dict=1,debug=0)

			fmcr_stock_qty = flt(fmcr.get('qty'),2) + flt(stock_record[0].get('qty'),2)
			loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,row=row,
						data=data,vmcr_doc=vmcr_doc,response_dict=response_dict)
		set_flag(fmcr)

	elif stock_data:
		for stock in stock_record:
			fmcr_stock_qty = flt(stock.get('qty'),2)
			loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,row=row,data=data,
				vmcr_doc=vmcr_doc,response_dict=response_dict,stock=stock)
		set_se_flag(stock)

def loss_gain_computation(fmcr_stock_qty,row,data,vmcr_doc,response_dict,stock=None):

	vlcc = frappe.db.get_value("Village Level Collection Centre",
		{"amcu_id":row.get('farmerid')},
		["name","warehouse","handling_loss","calibration_gain"],as_dict=True)
	if fmcr_stock_qty:
		if flt(fmcr_stock_qty,2) > flt(row.get('milkquantity'),2):
			qty = flt(fmcr_stock_qty,2) - flt(row.get('milkquantity'))
			make_stock_receipt(
				message="Material Receipt for Handling Loss",method="handling_loss",
				data=data,row=row,response_dict=response_dict,
				qty=qty,warehouse=vlcc.get('handling_loss'),
				societyid=row.get('farmerid'),vmcr_doc=vmcr_doc)
		elif flt(fmcr_stock_qty,2) < flt(row.get('milkquantity'),2):
			qty = flt(row.get('milkquantity')) - flt(fmcr_stock_qty,2)
			make_stock_receipt(
				message="Material Receipt for Calibration Gain",
				method="handling_gain",data=data,row=row,
				response_dict=response_dict,
				qty=qty,warehouse=vlcc.get('calibration_gain'),
				societyid=row.get('farmerid'),vmcr_doc=vmcr_doc)
		elif flt(fmcr_stock_qty,2) == flt(row.get('milkquantity'),2):
			utils.make_dairy_log(title="Quantity Balanced after VMCR Creation",
				method="handling_loss_gain", status="Success",data="Qty" ,
				message= "Quantity is Balanced so stock entry is not created",
				traceback="Scheduler")
			if stock:
				frappe.db.set_value("Vlcc Milk Collection Record",vmcr_doc.name,"is_scheduler",1)

def set_flag(fmcr):

	frappe.db.sql("""update 
						`tabFarmer Milk Collection Record`
					set 
						is_stock_settled=1
					where  
						docstatus = 1 and 
						shift = '{0}' and milktype = '{1}' and 
						date(rcvdtime) = '{2}' and societyid = '{3}' """.
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('recv_date')),fmcr.get('societyid')))
	frappe.db.sql("""update 
						`tabStock Entry`
					set 
						is_stock_settled=1
					where  
						docstatus = 1 and is_reserved_farmer = 1 and
						shift = '{0}' and milktype = '{1}' and 
						posting_date = '{2}' and societyid = '{3}' """.
						format(fmcr.get('shift'),fmcr.get('milktype'),
						getdate(fmcr.get('recv_date')),fmcr.get('societyid')))

def set_se_flag(stock):
	#if quantity is balanced or stock  entry is individual

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