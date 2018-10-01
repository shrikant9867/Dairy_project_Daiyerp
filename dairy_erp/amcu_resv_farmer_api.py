from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,get_time
from frappe import _
import dairy_utils as utils
from datetime import timedelta
import amcu_api as amcu_api
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate
import requests
import json



def make_stock_receipt(message,method,data,row,response_dict,qty,warehouse,societyid,vmcr_doc=None,fmcr=None):

	try:
		item_code = ""
		stock_doc = ""

		amcu_api.create_item(row)
		amcu_api.make_uom_config("Nos")
	
		if row.get('milktype') == "COW":
			item_code = "COW Milk"
		elif row.get('milktype') == "BUFFALO":
			item_code = "BUFFALO Milk"

		item_ = frappe.get_doc("Item",item_code)

		if method == 'create_fmrc':
			if not frappe.db.get_value('Stock Entry',
				{"transaction_id":row.get('transactionid')},"name"):
				stock_doc = stock_entry_creation(message,item_,method,data,row,qty,warehouse,societyid,vmcr_doc,fmcr)
			else:
				response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"success","response":"Record already created please check on server,if any exception check 'Dairy log'."})
		else:
			stock_doc = stock_entry_creation(message,item_,method,data,row,qty,warehouse,societyid,vmcr_doc,fmcr)	
			
		if stock_doc:
			response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Stock Receipt": stock_doc.name})

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method=method, status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": frappe.get_traceback()})
	return response_dict


def stock_entry_creation(message,item_,method,data,row,qty,warehouse,societyid,vmcr_doc,fmcr):

	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":societyid},["name","warehouse"],as_dict=True)
	company_details = frappe.db.get_value("Company",{"name":vlcc.get('name')},['default_payable_account','abbr','cost_center'],as_dict=1)
	remarks = {}

	stock_doc = frappe.new_doc("Stock Entry")
	stock_doc.purpose =  "Material Receipt"
	stock_doc.company = vlcc.get('name')
	stock_doc.transaction_id = row.get('transactionid')
	stock_doc.fmcr = fmcr.name if method == 'handling_loss_after_vmcr' or method == 'handling_gain_after_vmcr' else ""
	stock_doc.vmcr = vmcr_doc.name if method == 'handling_loss' or method == 'handling_gain' else ""
	if method == 'handling_loss' or method == 'handling_loss_after_vmcr':
		stock_doc.wh_type = 'Loss'
	elif method == 'handling_gain' or method == 'handling_gain_after_vmcr':
		stock_doc.wh_type = 'Gain'

	if row.get('transactionid'):
		stock_doc.shift = data.get('shift')
		stock_doc.milktype = row.get('milktype')
		stock_doc.societyid = data.get('societyid')
		stock_doc.is_reserved_farmer = 1 if method == "create_fmrc" else 0
		stock_doc.farmer_id = row.get('farmerid')
		stock_doc.fat = row.get('fat')
		stock_doc.snf = row.get('snf')
		stock_doc.clr = row.get('clr')
		remarks.update({"Farmer ID":row.get('farmerid'),"Transaction Id":row.get('transactionid'),
			"Collection Time":row.get('collectiontime'),"Message": message,"shift":data.get('shift')})
	else:
		remarks.update({"Farmer ID":row.get('farmerid'),
			"Collection Time":row.get('collectiontime'),"Message": message,"shift":data.get('shift')})

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