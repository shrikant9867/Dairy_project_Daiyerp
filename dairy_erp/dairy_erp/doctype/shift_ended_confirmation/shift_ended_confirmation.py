# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stellapps Technologies Private Ltd.
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import time
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate
from frappe import _
from datetime import timedelta
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
import requests
import json

class ShiftEndedConfirmation(Document):
	def validate(self):
		fmcr_stock_qty = 0
		stock_doc = ""
		try:
			amcu_id = frappe.db.get_value("Village Level Collection Centre",{"name":self.vlcc},"amcu_id")
			se = self.validate_stock_entry(amcu_id)
			
			if not se:
				fmcr_record = frappe.db.sql("""select name,ifnull(sum(milkquantity),0) as qty,
										shift,milktype,fat,snf,rate,
										date(collectiontime) as collectiontime,societyid,farmerid
									from 
										`tabFarmer Milk Collection Record` 
									where 
										shift = '{0}' and milktype = '{1}' and 
										date(collectiontime) = '{2}' and societyid = '{3}' 
										and docstatus = 1 and is_stock_settled = 0
					""".format(self.shift,self.milktype,
						getdate(self.collectiontime),amcu_id),as_dict=1,debug=0)

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
					""".format(self.shift,self.milktype,
						getdate(self.collectiontime),amcu_id),as_dict=1,debug=0)
				fmcr_data = fmcr_record[0].get('qty') if fmcr_record and fmcr_record[0].get('qty') else []
				stock_data = stock_record[0].get('qty') if stock_record and stock_record[0].get('qty') else []

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
						""".format(self.shift,self.milktype,
						getdate(self.collectiontime),amcu_id),as_dict=1,debug=0)

						fmcr_stock_qty = (flt(fmcr.get('qty'),2) + flt(stock_record[0].get('qty'),2))
						stock_doc = self.loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty,fmcr_qty=flt(fmcr.get('qty'),2),
							stock_qty=flt(stock_record[0].get('qty'),2))
					self.set_flag(amcu_id)

				elif stock_data:
					for stock in stock_record:
						fmcr_stock_qty = flt(stock.get('qty'),2)
						stock_doc = self.loss_gain_computation(fmcr_stock_qty=fmcr_stock_qty)
					self.set_se_flag(amcu_id)

				if stock_doc and stock_doc.name:
					frappe.msgprint("Stock Entry: '{0}' Created!!".format(stock_doc.name))

			else:
				frappe.throw("Stock Entry already created for above combination")
		except Exception,e:
			self.make_dairy_log(title="Stock Entry by Support failed to create",method="shift_ended_confirmation", status="Error",
			data = "data", message="message", traceback=frappe.get_traceback())

	def validate_stock_entry(self,amcu_id):
		se_name = ""
		se = frappe.db.sql("""select name 
							from 
								`tabStock Entry` 
							where 
								is_shift_ended = 1 and
								shift = %s and societyid = %s and 
								milktype = %s and posting_date =%s""",
								(self.shift,amcu_id,self.milktype,
								getdate(self.collectiontime)),as_dict=1)
		if se and se[0].get('name'):
			se_name = se[0].get('name')
		return se_name


	def loss_gain_computation(self,fmcr_stock_qty,fmcr_qty=0,stock_qty=0):
		se = ""
		vlcc = frappe.db.get_value("Village Level Collection Centre",
				{"name":self.vlcc},
				["amcu_id","chilling_centre","name","warehouse","handling_loss","calibration_gain"],as_dict=True)
		cc = frappe.db.get_value("Address",vlcc.get('chilling_centre'),"centre_id")

		vmcr_records = frappe.db.sql("""select name,sum(milkquantity) as qty,
								shift,farmerid,milktype
							from 
								`tabVlcc Milk Collection Record` 
							where 
								docstatus = 1 and is_stock_settled = 0 and 
								shift = '{0}' and milktype = '{1}' and 
								date(collectiontime) = '{2}' and farmerid = '{3}' and
								societyid = '{4}'
			""".format(self.shift,self.milktype,
				getdate(self.collectiontime),
				vlcc.get('amcu_id'),cc),as_dict=1,debug=0)

		vmcr_data = vmcr_records[0].get('qty') if vmcr_records and vmcr_records[0].get('qty') else []
		if vmcr_data:
			for vmcr in vmcr_records:
				if flt(fmcr_stock_qty,2) > flt(vmcr.get('qty'),2):
					qty = flt(fmcr_stock_qty,2) - flt(vmcr.get('qty'),2)
					se = self.make_stock_receipt(
						message="Material Receipt for Handling Loss",method="handling_loss",
						qty=qty,warehouse=vlcc.get('handling_loss'))
					self.make_fmcr_qty_log(fmcr_stock_qty=fmcr_stock_qty,vmcr_qty=flt(vmcr.get('qty'),2),
						loss_gain_qty= qty,fmcr_qty=fmcr_qty,stock_qty=stock_qty)
				elif flt(fmcr_stock_qty,2) < flt(vmcr.get('qty'),2):
					qty = flt(vmcr.get('qty'),2) - flt(fmcr_stock_qty,2)
					se = self.make_stock_receipt(
						message="Material Receipt for Calibration Gain",
						method="calibration_gain",
						qty=qty,warehouse=vlcc.get('calibration_gain'))
					self.make_fmcr_qty_log(fmcr_stock_qty=fmcr_stock_qty,vmcr_qty=flt(vmcr.get('qty'),2),
						loss_gain_qty= qty,fmcr_qty=fmcr_qty,stock_qty=stock_qty)
				elif flt(fmcr_stock_qty,2) == flt(vmcr.get('qty'),2):
					self.make_dairy_log(title="Quantity Balanced",
						method="handling_loss_gain", status="Success",data="Qty" ,
						message= "Quantity is Balanced so stock entry is not created",
						traceback="Scheduler")
			return se
			    
	def make_dairy_log(self,**kwargs):
		dlog = frappe.get_doc({"doctype":"Dairy Log"})
		dlog.update({
				"title":kwargs.get("title"),
				"method":kwargs.get("method"),
				"sync_time": now_datetime(),
				"status":kwargs.get("status"),
				"data":kwargs.get("data", ""),
				"error_message":kwargs.get("message", ""),
				"traceback":kwargs.get("traceback", ""),
				"doc_name": kwargs.get("doc_name", "")
			})
		dlog.insert(ignore_permissions=True)
		frappe.db.commit()
		return dlog.name

	def make_stock_receipt(self,message,method,qty,warehouse):
		vlcc = frappe.db.get_value("Village Level Collection Centre",{"name":self.vlcc},["warehouse","amcu_id"],as_dict=True)
		company_details = frappe.db.get_value("Company",{"name":self.vlcc},['default_payable_account','abbr','cost_center'],as_dict=1)
		remarks = {}

		self.make_uom_config("Nos")
		if self.milktype == "COW":
			item_code = "COW Milk"
		elif self.milktype == "BUFFALO":
			item_code = "BUFFALO Milk"

		item_ = frappe.get_doc("Item",item_code)

		stock_doc = frappe.new_doc("Stock Entry")
		stock_doc.purpose =  "Material Receipt"
		stock_doc.company = self.vlcc
		stock_doc.is_shift_ended = 1
		if method == 'handling_loss':
			stock_doc.wh_type = 'Loss'
		elif method == 'calibration_gain':
			stock_doc.wh_type = 'Gain'

		stock_doc.shift = self.shift
		stock_doc.milktype = self.milktype
		stock_doc.societyid = vlcc.get('amcu_id')
		remarks.update({"VLCC":self.vlcc,
				"Collection Time":self.collectiontime,"Message": message,"shift":self.shift})

		stock_doc.remarks = "\n".join("{}: {}".format(k, v) for k, v in remarks.items())
		stock_doc.append("items",
			{
				"item_code": item_.item_code,
				"item_name": item_.item_code,
				"description": item_.item_code,
				"uom": "Litre",
				"qty": qty,
				"t_warehouse": warehouse,
				"cost_center":company_details.get('cost_center')
			}
		)
		stock_doc.flags.ignore_permissions = True
		stock_doc.flags.is_api = True
		stock_doc.flags.ignore_mandatory = True
		stock_doc.submit()
		if self.collectiontime:
			frappe.db.sql("""update `tabStock Entry` 
				set 
					posting_date = '{0}'
				where 
					name = '{1}'""".format(getdate(self.collectiontime),stock_doc.name))
			frappe.db.sql("""update `tabGL Entry` 
				set 
					posting_date = %s
				where 
					voucher_no = %s""",(getdate(self.collectiontime),stock_doc.name))
			frappe.db.sql("""update `tabStock Ledger Entry` 
				set 
					posting_date = %s
				where 
					voucher_no = %s""",(getdate(self.collectiontime),stock_doc.name))
		return stock_doc

	def make_uom_config(self,doc):
		uom_obj = frappe.get_doc("UOM",doc)
		uom_obj.must_be_whole_number = 0
		uom_obj.flags.ignore_permissions = True
		uom_obj.save()

	def make_fmcr_qty_log(self,fmcr_stock_qty,vmcr_qty,loss_gain_qty,fmcr_qty=0,stock_qty=0):

		fmcr_qty_doc = frappe.new_doc("FMCR Quantity Log")
		fmcr_qty_doc.purpose = 'Stock Entry by Support'
		fmcr_qty_doc.vlcc = self.vlcc
		fmcr_qty_doc.shift = self.shift
		fmcr_qty_doc.milktype = self.milktype
		fmcr_qty_doc.collectiontime  = getdate(self.collectiontime)
		fmcr_qty_doc.fmcr_qty = flt(fmcr_qty,2) if fmcr_qty else 0
		fmcr_qty_doc.reserved_farmer_qty = flt(stock_qty,2) if stock_qty else flt(fmcr_stock_qty,2)
		fmcr_qty_doc.vmcr_qty = vmcr_qty
		fmcr_qty_doc.loss_gain_qty = loss_gain_qty
		fmcr_qty_doc.flags.ignore_permissions = True
		fmcr_qty_doc.save()

	def set_flag(self,amcu_id):
		vlcc_cc = frappe.db.get_value("Village Level Collection Centre",self.vlcc,"chilling_centre")
		cc = frappe.db.get_value("Address",vlcc_cc,"centre_id")
		frappe.db.sql("""update 
						`tabFarmer Milk Collection Record`
					set 
						is_stock_settled=1
					where  
						docstatus = 1 and 
						shift = '{0}' and milktype = '{1}' and 
						date(collectiontime) = '{2}' and societyid = '{3}' """.
						format(self.shift,self.milktype,
						getdate(self.collectiontime),amcu_id))
		frappe.db.sql("""update 
						`tabStock Entry`
					set 
						is_stock_settled=1
					where  
						docstatus = 1 and is_reserved_farmer = 1 and
						shift = '{0}' and milktype = '{1}' and 
						posting_date = '{2}' and societyid = '{3}' """.
						format(self.shift,self.milktype,
						getdate(self.collectiontime),amcu_id))
		frappe.db.sql("""update 
						`tabVlcc Milk Collection Record`
					set 
						is_stock_settled=1
					where  
						docstatus = 1  and
						shift = '{0}' and milktype = '{1}' and 
						date(collectiontime) = '{2}' and farmerid = '{3}' and 
						societyid = '{4}'""".
						format(self.shift,self.milktype,
						getdate(self.collectiontime),amcu_id,
						cc))

	def set_se_flag(self,amcu_id):
	#if quantity is balanced or stock  entry is individual as edit won't happen in special farmer case

		vlcc_cc = frappe.db.get_value("Village Level Collection Centre",self.vlcc,"chilling_centre")
		cc = frappe.db.get_value("Address",vlcc_cc,"centre_id")
		frappe.db.sql("""update 
							`tabStock Entry`
						set 
							is_stock_settled=1,is_scheduler = 1
						where  
							docstatus = 1 and is_reserved_farmer = 1 and
							shift = '{0}' and milktype = '{1}' and 
							posting_date = '{2}' and societyid = '{3}' """.
							format(self.shift,self.milktype,
							getdate(self.collectiontime),amcu_id))
		frappe.db.sql("""update 
							`tabVlcc Milk Collection Record`
						set 
							is_stock_settled = 1,is_scheduler = 1
						where  
							docstatus = 1  and
							shift = '{0}' and milktype = '{1}' and 
							date(collectiontime) = '{2}' and farmerid = '{3}' and 
							societyid = '{4}'""".
							format(self.shift,self.milktype,
							getdate(self.collectiontime),amcu_id,
							cc))