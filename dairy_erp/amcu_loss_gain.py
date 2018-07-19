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
	fmcr_record = frappe.db.sql("""select ifnull(sum(milkquantity),0) as qty ,
								group_concat(name) as fmcr,shift,milktype,
								date(rcvdtime) as recv_date,societyid
							from 
								`tabFarmer Milk Collection Record` 
							where 
								shift = '{0}' and milktype = '{1}' and 
								date(rcvdtime) = '{2}' and societyid = '{3}' 
								and docstatus = 1 and is_stock_settled = 0
			""".format(data.get('shift'),row.get('milktype'),
				getdate(data.get('rcvdtime')),
				row.get('farmerid')),as_dict=1,debug=0)

	stock_record = frappe.db.sql("""select ifnull(sum(se.qty),0) as qty ,
								group_concat(s.name) as stock,s.shift,
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
	print fmcr_record,"fmcr_record_______________________________\n\n"
	print stock_record,"stock_record____________________________________\n\n"

	fmcr_data = fmcr_record[0].get('qty') if fmcr_record and fmcr_record[0].get('qty') else []
	stock_data = stock_record[0].get('qty') if stock_record and stock_record[0].get('qty') else []

	if fmcr_data and stock_data:
		for fmcr in fmcr_record:
			for stock in stock_record:
				print "inside both_______________\n\n"
				fmcr_list = fmcr.get('fmcr').split(",") if fmcr and fmcr.get('fmcr') else []
				stock_list = stock.get('stock').split(",") if stock and stock.get('stock') else []
				if fmcr.get('shift') == stock.get('shift') and \
					fmcr.get('milktype') == stock.get('milktype') \
					and getdate(fmcr.get('recv_date')) == getdate(stock.get('posting_date')) \
					and fmcr.get('societyid') == stock.get('societyid'):

					fmcr_stock_qty = flt(fmcr.get('qty')) + flt(stock.get('qty'))
					
					loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,row=row,
						data=data,vmcr_doc=vmcr_doc,response_dict=response_dict,
						stock=stock,fmcr=fmcr)
					set_stock_flag(stock_list)
					set_flag_fmcr(fmcr_list)
				else:
					loss_gain_computation(fmcr_stock_qty=flt(fmcr.get('qty')),row=row,data=data,
						vmcr_doc=vmcr_doc,response_dict=response_dict,fmcr=fmcr)
					set_flag_fmcr(fmcr_list)
					
					loss_gain_computation(fmcr_stock_qty=flt(stock.get('qty')),row=row,data=data,
						vmcr_doc=vmcr_doc,response_dict=response_dict,stock=stock)
					set_se_flag(stock_list)
	elif fmcr_data:
		print "inside fmcr_data_______________\n\n"
		for fmcr in fmcr_record:
			fmcr_list = fmcr.get('fmcr').split(",") if fmcr and fmcr.get('fmcr') else []
			fmcr_stock_qty = flt(fmcr.get('qty'))
			loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,row=row,data=data,
				vmcr_doc=vmcr_doc,response_dict=response_dict,fmcr=fmcr)
			set_flag_fmcr(fmcr_list)
	elif stock_data:
		print "stock_data_______________\n\n"
		for stock in stock_record:
			stock_list = stock.get('stock').split(",") if stock and stock.get('stock') else []
			fmcr_stock_qty = flt(stock.get('qty'))
			loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,row=row,data=data,
				vmcr_doc=vmcr_doc,response_dict=response_dict,stock=stock)
			set_se_flag(stock_list)


def loss_gain_computation(fmcr_stock_qty,row,data,vmcr_doc,response_dict,stock=None,fmcr=None):

	vlcc = frappe.db.get_value("Village Level Collection Centre",
		{"amcu_id":row.get('farmerid')},
		["name","warehouse","handling_loss","calibration_gain"],as_dict=True)
	if fmcr_stock_qty:
		if fmcr_stock_qty > row.get('milkquantity'):
			qty = fmcr_stock_qty - row.get('milkquantity')
			make_stock_receipt(
				message="Material Receipt for Handling Loss",method="handling_loss",
				data=data,row=row,response_dict=response_dict,
				qty=qty,warehouse=vlcc.get('handling_loss'),
				societyid=row.get('farmerid'),vmcr_doc=vmcr_doc)
		elif fmcr_stock_qty < row.get('milkquantity'):
			qty = row.get('milkquantity') - fmcr_stock_qty
			make_stock_receipt(
				message="Material Receipt for Calibration Gain",
				method="handling_gain",data=data,row=row,
				response_dict=response_dict,
				qty=qty,warehouse=vlcc.get('calibration_gain'),
				societyid=row.get('farmerid'),vmcr_doc=vmcr_doc)
		elif fmcr_stock_qty == row.get('milkquantity'):
			utils.make_dairy_log(title="Quantity Balanced after VMCR Creation",
				method="handling_loss_gain", status="Success",data="Qty" ,
				message= "Quantity is Balanced so stock entry is not created",
				traceback="Scheduler")
			if stock:
				frappe.db.set_value("Vlcc Milk Collection Record",vmcr_doc.name,"is_scheduler",1)

		# fmcr_list = fmcr.get('fmcr').split(",") if fmcr and fmcr.get('fmcr') else []
		# stock_list = stock.get('stock').split(",") if stock and stock.get('stock') else []
		# set_flag_fmcr(fmcr_list=fmcr_list)
		# set_stock_flag(stock_list=stock_list)

def set_flag_fmcr(fmcr_list):
	if fmcr_list:
		for data in fmcr_list:
			fmcr_doc = frappe.get_doc('Farmer Milk Collection Record',data)
			fmcr_doc.is_stock_settled = 1
			fmcr_doc.flags.ignore_permissions = True
			fmcr_doc.save()

def set_stock_flag(stock_list):

	if stock_list:
		for data in stock_list:
			se = frappe.get_doc('Stock Entry',data)
			se.is_stock_settled = 1
			se.flags.ignore_permissions = True
			se.save()

def set_se_flag(stock_list):
	#if quantity is balanced or stock  entry is individual

	if stock_list:
		for data in stock_list:
			se = frappe.get_doc('Stock Entry',data)
			se.is_stock_settled = 1
			se.is_scheduler = 1
			se.flags.ignore_permissions = True
			se.save()