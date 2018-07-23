from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime
from frappe import _
import dairy_utils as utils
from datetime import timedelta
import amcu_api as amcu_api
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate
import requests
import json



def make_stock_receipt(message,method,data,row,response_dict,qty,warehouse,societyid,vmcr_doc=None):

	try:
		vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":societyid},["name","warehouse"],as_dict=True)
		company_details = frappe.db.get_value("Company",{"name":vlcc.get('name')},['default_payable_account','abbr','cost_center'],as_dict=1)
		remarks = {}
		item_code = ""

		amcu_api.create_item(row)
		amcu_api.make_uom_config("Nos")
	
		if row.get('milktype') == "COW":
			item_code = "COW Milk"
		elif row.get('milktype') == "BUFFALO":
			item_code = "BUFFALO Milk"

		item_ = frappe.get_doc("Item",item_code)

		if not frappe.db.get_value('Stock Entry',
			{"transaction_id":row.get('transactionid')},"name"):

			stock_doc = frappe.new_doc("Stock Entry")
			stock_doc.purpose =  "Material Receipt"
			stock_doc.posting_date = getdate(data.get('rcvdtime'))
			stock_doc.company = vlcc.get('name')
			stock_doc.transaction_id = row.get('transactionid')
			stock_doc.vmcr = vmcr_doc.name if method == 'handling_loss' or method == 'handling_gain' else ""
			stock_doc.wh_type = 'Loss' if method == 'handling_loss' else 'Gain'
			if row.get('transactionid'):
				stock_doc.shift = data.get('shift')
				stock_doc.milktype = row.get('milktype')
				stock_doc.societyid = data.get('societyid')
				stock_doc.is_reserved_farmer = 1
				stock_doc.farmer_id = row.get('farmerid')
				stock_doc.fat = row.get('fat')
				stock_doc.snf = row.get('snf')
				stock_doc.clr = row.get('clr')
				remarks.update({"Farmer ID":row.get('farmerid'),"Transaction Id":row.get('transactionid'),
					"Rcvd Time":data.get('rcvdtime'),"Message": message,"shift":data.get('shift')})
			else:
				remarks.update({"Farmer ID":row.get('farmerid'),
					"Rcvd Time":data.get('rcvdtime'),"Message": message,"shift":data.get('shift')})

			stock_doc.remarks = "\n".join("{}: {}".format(k, v) for k, v in remarks.items())
			stock_doc.append("items",
				{
					"item_code": item_.item_code,
					"item_name": item_.item_code,
					"description": item_.item_code,
					"uom": "Litre",
					"qty": qty,
					"t_warehouse": warehouse,
					"cost_center":company_details.get('cost_center'),
					"basic_rate": row.get('rate')
				}
			)
			stock_doc.flags.ignore_permissions = True
			stock_doc.flags.is_api = True
			stock_doc.submit()
			if method == 'handling_loss' or method == 'handling_gain':
				response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Stock Receipt": stock_doc.name})
			else:
				response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Stock Receipt": stock_doc.name})
		else:
			response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"success","response":"Record already created please check on server,if any exception check 'Dairy log'."})

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method=method, status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": frappe.get_traceback()})
	return response_dict