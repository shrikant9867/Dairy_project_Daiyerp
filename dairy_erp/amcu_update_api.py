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
from amcu_loss_gain import handling_loss_gain,loss_gain_computation
import amcu_api as amcu_api
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
import requests
import json


def update_fmcr(data, row,response_dict):

	try: 
		vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},"name")
		config_hrs = frappe.db.get_value('VLCC Settings',{'vlcc':vlcc},'hours') or 0
		fmcr = frappe.db.get_value('Farmer Milk Collection Record',
				{"transactionid":row.get('transactionid'),"farmerid":row.get('farmerid')},"name")
		min_rcvdtm_fmcr = frappe.db.sql("""select min(collectiontime) as min_time
							from  
								`tabFarmer Milk Collection Record` 
							where 
								societyid = %s and 
								milktype = %s and 
								shift = %s and 
								docstatus =1 and 
								date(collectiontime) = %s""",
								(data.get('societyid'),row.get('milktype'),
								data.get('shift'),getdate(row.get('collectiontime'))),
							as_dict=True,debug=0)
		if fmcr:
			fmcr_doc = frappe.get_doc("Farmer Milk Collection Record",fmcr)
			max_time = get_datetime(min_rcvdtm_fmcr[0].get('min_time')) +  timedelta(hours=int(config_hrs))
			if now_datetime() < max_time: 
				update_fmcr_amt(fmcr_doc, data,row,response_dict)
			else:
				response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "Allowed updation time has been elapsed for {0}".format(fmcr_doc.name)})
		else:
			is_fmcr_created = 1
			fmrc_doc = make_fmcr(data,row,response_dict,is_fmcr_created)
			fmcr = frappe.db.get_value('Farmer Milk Collection Record',
				{"transactionid":row.get('transactionid'),"farmerid":row.get('farmerid')},"name")
			response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "There are no transactions present with the transaction id {0} so new {1} has been created".format(row.get('transactionid'),fmcr)})
	except Exception,e:
		frappe.db.rollback()
		utils.make_dairy_log(title="Sync failed for Data push",method="update_fmcr", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": frappe.get_traceback()})	
	return response_dict
	
def update_fmcr_amt(fmcr_doc,data,row,response_dict):

	pi = frappe.db.get_value("Purchase Invoice",{"farmer_milk_collection_record":fmcr_doc.name},"name") or ""
	pr = frappe.db.get_value("Purchase Receipt",{"farmer_milk_collection_record":fmcr_doc.name},"name") or ""
	se = frappe.db.get_value("Stock Entry",{"fmcr":fmcr_doc.name},"name") or ""

	if pi:
		frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(pi))
		frappe.db.sql("""delete from `tabPurchase Invoice` where name = %s""",(pi))
	if pr:
		frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(pr))
		frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_no = %s""",(pr))
		frappe.db.sql("""delete from `tabPurchase Receipt` where name = %s""",(pr))

	fmcr_doc.cancel()

	fmcr = make_fmcr(data,row,response_dict)

def make_fmcr(data,row,response_dict,is_fmcr_created=0):
	
	traceback = ""
	try:
		if data.get('imeinumber') and data.get('rcvdtime') and data.get('shift') and data.get('collectiondate'):
			if row.get('farmerid') and row.get('milktype') and row.get('collectiontime') \
				and row.get('milkquantity') and row.get('rate') and row.get('status') and row.get('transactionid'):
				if row.get('operation') == 'UPDATE':
					fmrc_entry = amcu_api.validate_fmrc_entry(data,row)
					if not fmrc_entry:
						if amcu_api.validate_society_exist(data):
							if amcu_api.farmer_associate_vlcc(data,row):
								vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
								farmer = frappe.db.get_value("Farmer",{"vlcc_name": vlcc},'name')
								farmer_supplier = frappe.db.get_value("Farmer",row.get('farmerid'),'full_name')
								row.update(
									{
										"qualitytime": row.get('qualitytime'), #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('qualitytime'))/1000)),
										"quantitytime": row.get('quantitytime') #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('quantitytime'))/1000))
									}
								)
								fmrc_doc = frappe.new_doc("Farmer Milk Collection Record")
								fmrc_doc.farmer = farmer_supplier
								fmrc_doc.id = data.get('id')
								fmrc_doc.associated_vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
								fmrc_doc.imeinumber = data.get('imeinumber')
								fmrc_doc.rcvdtime = data.get('rcvdtime')
								fmrc_doc.fmcr_created = is_fmcr_created
								fmrc_doc.processedstatus = data.get('processedstatus')
								fmrc_doc.societyid = data.get('societyid')
								fmrc_doc.longformatsocietyid = data.get('longformatsocietyid')
								fmrc_doc.collectiondate = data.get('collectiondate') # time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
								fmrc_doc.shift = data.get('shift')
								fmrc_doc.starttime = data.get('starttime') #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('starttime')/1000))
								fmrc_doc.endtime = data.get('endtime') #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('endtime')/1000))
								fmrc_doc.endshift = 1 if data.get('endshift') == True else 0
			 					fmrc_doc.update(row)
								fmrc_doc.flags.ignore_permissions = True
								fmrc_doc.flags.is_api = True
								fmrc_doc.submit()
								response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"fmrc": fmrc_doc.name})
								if row.get('status') == "Accept":
									pr = amcu_api.make_purchase_receipt_vlcc(data, row, vlcc, farmer_supplier, response_dict, fmrc_doc.name )
									amcu_api.purchase_invoice_against_farmer(data, row, vlcc,  farmer_supplier, pr.get('item_'), response_dict, pr.get('pr_obj'), fmrc_doc.name)
							else:
								traceback = "farmer does not exist"
								frappe.throw(_("farmer does not exist"))
						
						else :
							traceback = "vlcc does not exist!" 
							frappe.throw(_("vlcc does not exist!"))					
					else:
						response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"success","response":"Record already created please check on server,if any exception check 'Dairy log'."})
			else:
				traceback = "data missing"
				response_dict.update({"status":"Error","response":"Data Missing","message": "farmerid,milktype,collectiontime,milkquantity,rate, status must be one of Accept or Reject are manadatory"})
		else:
			traceback = "data Missing"
			response_dict.update({"status":"Error","response":"Data Missing","message":"imeinumber,collectionDate,shift,rcvdTime are manadatory"})
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": traceback})		
	return fmrc_doc