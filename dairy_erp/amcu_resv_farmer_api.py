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
import requests
import json



def make_stock_receipt(data, row,response_dict):

	try:
		vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},["name","warehouse"],as_dict=True)
		company_details = frappe.db.get_value("Company",{"name":vlcc.get('name')},['default_payable_account','abbr','cost_center'],as_dict=1)
		remarks = {}

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
			stock_doc.company = vlcc.get('name')
			stock_doc.transaction_id = row.get('transactionid')
			remarks.update({"Farmer ID":row.get('farmerid'),"Transaction Id":row.get('transactionid'),
				"Rcvd Time":data.get('rcvdtime'),"Message": "Material Receipt for Reserved Farmer"})
			stock_doc.remarks = "\n".join("{}: {}".format(k, v) for k, v in remarks.items())
			stock_doc.append("items",
				{
					"item_code": item_.item_code,
					"item_name": item_.item_code,
					"description": item_.item_code,
					"uom": "Litre",
					"qty": row.get('milkquantity'),
					"t_warehouse": vlcc.get('warehouse'),
					"cost_center":company_details.get('cost_center')
				}
			)
			stock_doc.flags.ignore_permissions = True
			stock_doc.flags.is_api = True
			stock_doc.submit()
			response_dict.update({row.get('farmerid')+"-"+row.get('milktype'): [{"Stock Receipt": stock_doc.name}]})
		else:
			response_dict.update({row.get('farmerid')+"-"+row.get('milktype'):[{"status":"success","response":"Record already created please check on server,if any exception check 'Dairy log'."}]})

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})
	return response_dict