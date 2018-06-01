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

	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},["name","warehouse","handling_loss","calibration_gain"],as_dict=True)

	fmcr_record = frappe.db.sql("""select ifnull(sum(milkquantity),0) as qty ,
								group_concat(name) as fmcr
							from 
								`tabFarmer Milk Collection Record` 
							where 
								shift = '{0}' and milktype = '{1}' and 
								date(rcvdtime) = '{2}' and societyid = '{3}' 
								and docstatus = 1 and is_stock_settled = 0
			""".format(data.get('shift'),row.get('milktype'),
				getdate(data.get('rcvdtime')),
				row.get('farmerid')),as_dict=1,debug=1)

	if len(fmcr_record):
		for fmcr in fmcr_record:
			if fmcr:
				fmcr_list = fmcr.get('fmcr').split(",")

				if fmcr.get('qty') > row.get('milkquantity'):
					qty = fmcr.get('qty') - row.get('milkquantity')
					make_stock_receipt(
						message="Material Receipt for Handling Loss",method="handling_loss_gain",
						data=data,row=row,response_dict=response_dict,
						qty=qty,warehouse=vlcc.get('handling_loss'),
						societyid=row.get('farmerid'),vmcr_doc=vmcr_doc)
				elif fmcr.get('qty') < row.get('milkquantity'):
					qty = row.get('milkquantity') - fmcr.get('qty')
					make_stock_receipt(
						message="Material Receipt for Calibration Gain",
						method="handling_loss_gain",data=data,row=row,
						response_dict=response_dict,
						qty=qty,warehouse=vlcc.get('calibration_gain'),
						societyid=row.get('farmerid'),vmcr_doc=vmcr_doc)

				set_flag_fmcr(fmcr_list=fmcr_list,is_stock_settled=1)

def set_flag_fmcr(fmcr_list,is_stock_settled):

	if fmcr_list:
		for data in fmcr_list:
			fmcr_doc = frappe.get_doc('Farmer Milk Collection Record',data)
			fmcr_doc.is_stock_settled = is_stock_settled
			fmcr_doc.flags.ignore_permissions = True
			fmcr_doc.save()