# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt
# Author Khushal Trivedi

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe import _
from amcu_update_api import update_fmcr
from amcu_delete_api import delete_fmcr
from amcu_resv_farmer_api import make_stock_receipt
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate,get_time
from frappe.utils.data import add_to_date
from amcu_loss_gain import handling_loss_gain,loss_gain_computation
import dairy_utils as utils
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
import requests
import json


@frappe.whitelist()
def create_fmrc(data):
	""" API for pushing amcu data over erpnext. mapper must of field type to update doc.
		Lower casing for the same, create farmer milk record if accepted issue Purchase Receipt
		Make Log for sync fail : VLCC"""
	
	response_dict, response_data = {}, []
	try:
		api_data = json.loads(data)
		for i,v in api_data.items():
			if i != "collectionEntryList":
				api_data[i.lower()] = api_data.pop(i)
			else: 
				for d in v:
					for m,n in d.items():
						d[m.lower()] = d.pop(m)
		
		fmrc = make_fmrc(api_data,response_dict)

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})

	return response_dict


def make_fmrc(data, response_dict):   
	"""record JSON irrespective of 'status', epoch to timestamp(Op)
		no of field = 56(enum), update row 40 type field in one row to make one FMCR : VLCC 
	"""
	traceback = ""
	farmer1,farmer2 = "",""
	if data.get('societyid'):
		for i,v in data.items():
			if i == "collectionEntryList":
				for row in v:
					try:
						vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},"name")
						if frappe.db.get_value("VLCC Settings",vlcc,'name'):
							resv_farmer = frappe.db.get_value('VLCC Settings',{'vlcc':vlcc},['farmer_id1','farmer_id2','configurable_days'],as_dict=True) 
							if resv_farmer:
								farmer1 = resv_farmer.get('farmer_id1')
								farmer2 = resv_farmer.get('farmer_id2')
							if response_dict.get(row.get('farmerid')+"-"+row.get('milktype')):
								response_dict.get(row.get('farmerid')+"-"+row.get('milktype'))
							else:
								response_dict.update({row.get('farmerid')+"-"+row.get('milktype'): []})
							if data.get('imeinumber') and data.get('rcvdtime') and data.get('shift') and data.get('collectiondate'):
								if row.get('farmerid') and row.get('milktype') and row.get('collectiontime') \
									and row.get('milkquantity') and row.get('rate') and row.get('status') and row.get('transactionid'):	
									if row.get('farmerid') not in [farmer1,farmer2]:
										if row.get('operation') == 'CREATE':
											fmrc_entry = validate_fmrc_entry(data,row)
											if not fmrc_entry:
												if validate_society_exist(data):
													if farmer_associate_vlcc(data,row):
														vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
														farmer = frappe.db.get_value("Farmer",{"vlcc_name": vlcc},'name')
														farmer_supplier = frappe.db.get_value("Farmer",row.get('farmerid'),'full_name')
														row.update(
															{
																"collectiontime": row.get('collectiontime'), #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('collectiontime'))/1000)),
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
														fmrc_doc.processedstatus = data.get('processedstatus')
														fmrc_doc.societyid = data.get('societyid')
														fmrc_doc.longformatsocietyid = data.get('longformatsocietyid')
														fmrc_doc.collectiondate =  data.get('collectiondate') # time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
														fmrc_doc.posting_date = getdate(data.get('collectiontime'))
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
															pr = make_purchase_receipt_vlcc(data, row, vlcc, farmer_supplier, response_dict, fmrc_doc.name )
															purchase_invoice_against_farmer(data, row, vlcc,  farmer_supplier, pr.get('item_'), response_dict, pr.get('pr_obj'), fmrc_doc.name, resv_farmer.get('configurable_days'))
													else:
														traceback = "farmer does not exist"
														frappe.throw(_("farmer does not exist"))
												
												else :
													traceback = "vlcc does not exist!" 
													frappe.throw(_("vlcc does not exist!"))					
											else:
												response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"success","response":"Record already created please check on server,if any exception check 'Dairy log'."})
										elif row.get('operation') == 'UPDATE':
											update_fmcr(data,row,response_dict)
										elif row.get('operation') == 'DELETE':
											delete_fmcr(data,row,response_dict)
									elif row.get('farmerid') in (resv_farmer.get('farmer_id1'),resv_farmer.get('farmer_id2')):
										wh = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},["name","warehouse"],as_dict=True)
										make_stock_receipt(message="Material Receipt for Reserved Farmer",method="create_fmrc",
														data=data,row=row,response_dict=response_dict,qty=row.get('milkquantity'),
														warehouse=wh.get('warehouse'),
														societyid=data.get('societyid'))
								else:
									traceback = "data missing"
									response_dict.update({"status":"Error","response":"Data Missing","message": "farmerid,milktype,collectiontime,milkquantity,rate, status must be one of Accept or Reject are manadatory"})
							else:
								traceback = "data Missing"
								response_dict.update({"status":"Error","response":"Data Missing","message":"imeinumber,collectionDate,shift,rcvdTime are manadatory"})
						else:
							traceback = "Please create vlcc setting first"
							response_dict.update({"status":"Error","response":"Data Missing","message":"Please create vlcc setting first"})
					except Exception,e:
						utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
						data = data, message=e, traceback=frappe.get_traceback())
						response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": traceback})		
	else:
		response_dict.update({"status":"Error","response":"society id missing"})
	return response_dict


def validate_fmrc_entry(data, row):
	"""validate for duplicate entry for Farmer Milk Record Collection"""
	
	return frappe.db.get_value('Farmer Milk Collection Record',
			{"transactionid":row.get('transactionid'),"docstatus":['=',1] },"name")


def validate_society_exist(data):

	return frappe.db.sql("""select name from `tabVillage Level Collection Centre`
		where amcu_id = '{0}'""".format(data.get('societyid')))


def farmer_associate_vlcc(data, row):
	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
	return frappe.db.get_value("Farmer",{"vlcc_name": vlcc,"name":row.get('farmerid')},'name')


def make_purchase_receipt_vlcc(data, row, vlcc, farmer, response_dict, fmrc):
	"""If Accepted at AMCU unit make purchase receipt.Making Item On head further, groups and
	   items(Hard CD).Maintainable over milk type.stock to respective vlcc must 
	   be auxillary(enum). : VLCC """

	item_code = ""
	
	try:
		create_item(row)
		make_uom_config("Nos")
	
		if row.get('milktype') == "COW":
			item_code = "COW Milk"
		elif row.get('milktype') == "BUFFALO":
			item_code = "BUFFALO Milk"
		cost_center = frappe.db.get_value("Cost Center", {"company": vlcc}, 'name')
		item_ = frappe.get_doc("Item",item_code)
		if farmer:
			purchase_rec = frappe.new_doc("Purchase Receipt")
			purchase_rec.farmer_milk_collection_record = fmrc
			purchase_rec.supplier =  farmer
			purchase_rec.company = vlcc
			purchase_rec.append("items",
				{
					"item_code": item_.item_code,
					"item_name": item_.item_code,
					"description": item_.item_code,
					"uom": "Litre",
					"qty": row.get('milkquantity'),
					"rate": row.get('rate'),
					"price_list_rate": row.get('rate'),
					"amount": row.get('amount'),
					"warehouse": frappe.db.get_value("Village Level Collection Centre", vlcc, 'warehouse'),
					"cost_center": cost_center
				}
			)
			purchase_rec.status = "Completed"
			purchase_rec.per_billed = 100
			purchase_rec.flags.ignore_permissions = True
			purchase_rec.submit()
			set_posting_datetime(purchase_rec,row)
			set_stock_ledger_date(purchase_rec,row)
			response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"purchase receipt": purchase_rec.name})

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error":frappe.get_traceback()})
	return {"item_":item_, "pr_obj": purchase_rec.name}


@frappe.whitelist()
def create_farmer(data):
	"""Separate API(client req), should have been merge in main(future scope) : VLCC"""
	response_dict = {}
	traceback = ""
	api_data = json.loads(data)
	if api_data:
		for row in api_data:
			response_dict.update({row.get('farmer_id'):[]})
			vlcc_ = frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('society_id')},'name')
			farmer_ = frappe.db.get_value("Farmer",row.get('farmer_id'),'name')
			try:
				if row.get('society_id') and row.get('farmer_id') and row.get('full_name') and row.get('mode') == "CREATE" and row.get('cattle_type'):
					vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('society_id')},'name')
					if vlcc :
						if not frappe.db.sql("select full_name from `tabFarmer` where full_name=%s",(row.get("full_name"))):
							if  reserved_farmer_exist(row,vlcc):
								if  not frappe.db.exists("Farmer",row.get("farmer_id")):
									farmer_obj = frappe.new_doc("Farmer")
									farmer_obj.full_name = row.get('full_name')
									farmer_obj.farmer_id = row.get('farmer_id')
									farmer_obj.contact_number = row.get('contact_no')
									farmer_obj.vlcc_name = vlcc
									farmer_obj.registration_date = row.get('registration_date')
									farmer_obj.update_date = row.get('updation_date')
									farmer_obj.cattle_type = row.get('cattle_type')
									farmer_obj.insert()
									response_dict.get(row.get('farmer_id')).append({"status": "success","name":farmer_obj.name})
								else:
									traceback = " Farmer ID Exist"
									frappe.throw(_("Id Exist"))
							else:
									traceback = "This is reserved farmer id,you can not use"
									frappe.throw(_("an not use this id, this is reserverd  id"))
						else:
							traceback = "Farmer Exist with same name"
							frappe.throw("Farmer Exist with same name")
					else:
						traceback = "Society ID(VLCC-amcu id) does not exist"
						frappe.throw(_("Society does not exist"))
				elif  row.get('farmer_id')  and row.get('mode') == "UPDATE" and row.get('updation_date') and farmer_:
					if update_farmer(row, response_dict, traceback):
						response_dict.get(row.get('farmer_id')).append({"status": "successfully updated","name": row.get('farmer_id')})
					else:
						traceback = "Farmer Does Not exist, for more info check dairy log"
						frappe.throw(_("Farmer does not exist"))
				elif row.get('farmer_id')  and row.get('mode') == "UPDATE" and row.get('updation_date') and not farmer_ :
					if vlcc_:
						if  not frappe.db.sql("select full_name from `tabFarmer` where full_name=%s",(row.get("full_name"))):
							if reserved_farmer_exist(row,vlcc_):
								create_farmer_mode(row,vlcc_)
								response_dict.get(row.get('farmer_id')).append({"status": "successfully created","name": row.get('farmer_id')})
							else:
								traceback = "This is reserved farmer id,you can not use"
								frappe.throw(_("can not use this id, this is reserverd  id"))
						else:
							traceback = "Farmer Exist with same name"
							frappe.throw("Farmer Exist with same name")
					else:
						traceback = "Society ID(VLCC-amcu id) does not exist"
						frappe.throw(_("Society ID(VLCC-amcu id) does not exist"))
				else:
					traceback = "Society ID, Full Name, Farmer ID, mode,cattle type are manadatory data"
					frappe.throw(_("Society ID, full_name, farmerid  does not exist(Vlcc at ERP)"))
	
			except Exception,e:
				utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
				data = data, message=e, traceback=frappe.get_traceback())
				response_dict.get(row.get('farmer_id')).append({"Error": traceback})
				# response_dict.get(row('farmer_id')).append(farmer_obj.name)

	return response_dict		

def update_farmer(data, response_dict, traceback):
	#update farmer only(cattle type and contact)
	if  frappe.db.exists("Farmer",data.get("farmer_id")):
		farmer_doc = frappe.get_doc("Farmer",data.get('farmer_id'))
		if data.get('contact_no'):
			farmer_doc.contact_number = data.get('contact_no')
		if data.get('cattle_type'):
			farmer_doc.cattle_type = data.get('cattle_type')
		if data.get('updation_date'):
			farmer_doc.update_date = data.get('updation_date')
		farmer_doc.save()
		return True
	else:
		return False

def create_farmer_mode(row, vlcc):
	farmer_obj = frappe.new_doc("Farmer")
	farmer_obj.full_name = row.get('full_name')
	farmer_obj.farmer_id = row.get('farmer_id')
	farmer_obj.contact_number = row.get('contact_no')
	farmer_obj.vlcc_name = vlcc
	farmer_obj.registration_date = row.get('registration_date')
	farmer_obj.update_date = row.get('updation_date')
	farmer_obj.cattle_type = row.get('cattle_type')
	farmer_obj.insert()

def reserved_farmer_exist(data,vlcc):
	apnd_list = []
	apnd_list.append(frappe.db.get_value("VLCC Settings", vlcc, 'farmer_id1'))
	apnd_list.append(frappe.db.get_value("VLCC Settings", vlcc, 'farmer_id2'))
	if data.get('farmer_id') in apnd_list:
		return False
	return True


@frappe.whitelist()
def create_vmrc(data):
	"""Create Village level Milk colection record at Dairy Level.Make Purchase Receipt 
		if status accepted :Dairy"""

	response_dict = {}
	api_data = json.loads(data)

	try:
		api_data = json.loads(data)
		for i,v in api_data.items():
			if i != "collectionEntryList":
				api_data[i.lower()] = api_data.pop(i)
			else:
				for d in v:
					for m,n in d.items():
						d[m.lower()] = d.pop(m)
		vmrc = make_vmrc(api_data,response_dict)

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status":"error","message":e, "traceback": frappe.get_traceback()})

	return response_dict

def make_vmrc(data, response_dict):
	""":Dairy"""
	traceback,quality_type = "",""
	if data.get('societyid'):
		for i,v in data.items():
			if i == "collectionEntryList":
				for row in v:
					try:
						response_dict.update({row.get('farmerid')+"-"+row.get('milktype'):[]})
						if frappe.db.get_singles_dict('Dairy Setting').get('configurable_days'):
							if data.get('imeinumber') and data.get('rcvdtime') and data.get('shift') and data.get('collectiondate'):
								if row.get('farmerid') and row.get('milktype') and row.get('collectiontime') and row.get('milkquantity') and row.get('status') and row.get('collectionroute'):
									if row.get('milkquality') in ['G','CT','CS','SS']:
										collectiontime = row.get('collectiontime') # time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('collectiontime'))/1000))
										collectiondate = data.get('collectiondate') # time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
										vlcc_name = frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('farmerid')},'name')
										vmrc = validate_vmrc_entry(row)
										if row.get('operation') == 'CREATE':
											if not vmrc:
												vmrc_doc = create_vmcr_doc(data,row,collectiontime,collectiondate,vlcc_name,response_dict)	
												handling_loss_gain(data,row,vmrc_doc,response_dict)
											else:
												response_dict.update({row.get('farmerid')+"-"+row.get('milktype'):["Record already created please check on server,if any exception check 'Dairy log'."]})
										elif row.get('operation') == 'UPDATE':
											if vmrc:
												delete_previous_linked_doc(data,row,collectiontime,collectiondate,vlcc_name,response_dict)
											else:
												is_vmcr_created = 1
												vmrc_doc = create_vmcr_doc(data,row,collectiontime,collectiondate,vlcc_name,response_dict,is_vmcr_created)	
												handling_loss_gain(data,row,vmrc_doc,response_dict)
												response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "There are no transactions present with the transaction id {0} so new {1} has been created".format(row.get('transactionid'),vmrc_doc.name)})
												# response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "There are no transactions present with the transaction id {0}".format(row.get('transactionid'))})
									else:
										if row.get('status') == 'Accept':
											quality_type = 'G'
										elif row.get('status') == 'Reject':
											quality_type = 'CT,CS or SS'
										response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"Milkquality must be {0}".format(quality_type)}) if quality_type else ""
								else:
									response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":["Error status_response Data Missing. status_message farmerid,milktype,collectiontime,milkquantity,rate,collectionroute are manadatory"]})
							else:
								response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"Error","response":"Data Missing","message":"imeinumber,collectionDate,shift,rcvdTime are manadatory"})
						else:
							response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"Error","response":"Data Missing","message":"Please Create dairy settings"})
							# frappe.throw(_("Please create dairy settings first"))
					except Exception,e:
						utils.make_dairy_log(title="Sync failed for Data push",method="create_vmrc", status="Error",
						data = data, message=e, traceback=frappe.get_traceback())
						response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": frappe.get_traceback()})

def delete_previous_linked_doc(data,row,collectiontime,collectiondate,vlcc_name,response_dict):
	#cannot use cancel doc, delete doc  deadlock occurs, so explicitly hard delete
	vmcr = frappe.db.get_value('Vlcc Milk Collection Record',
				{"transactionid":row.get('transactionid'),"farmerid":row.get('farmerid'),"docstatus":['=',1]},"name")
	if vmcr:
		pr = frappe.db.get_value("Purchase Receipt",{"vlcc_milk_collection_record":vmcr,"docstatus":['=',1]},"name")
		dn = frappe.db.get_value("Delivery Note",{"vlcc_milk_collection_record":vmcr,"docstatus":['=',1]},"name")
		pi = frappe.db.get_value("Purchase Invoice",{"vlcc_milk_collection_record":vmcr,"docstatus":['=',1]},"name")
		si = frappe.db.get_value("Sales Invoice",{"vlcc_milk_collection_record":vmcr,"docstatus":['=',1]},"name")
		vmcr_doc = frappe.get_doc("Vlcc Milk Collection Record",vmcr)
		se = frappe.db.get_value('Stock Entry',{'vmcr':vmcr},
					['name','wh_type'],as_dict=1) or {}		
		vmcr_stock_qty = vmcr_stock_qty_computation(vmcr,se)

		if si:
			frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(si))
			frappe.db.sql("""delete from `tabSales Invoice` where name = %s""",(si))
		if dn:
			frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(dn))
			frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_no = %s""",(dn))
			frappe.db.sql("""delete from `tabDelivery Note` where name = %s""",(dn))
		if pi:
			frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(pi))
			frappe.db.sql("""delete from `tabPurchase Invoice` where name = %s""",(pi))
		if pr:
			frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(pr))
			frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_no = %s""",(pr))
			frappe.db.sql("""delete from `tabPurchase Receipt` where name = %s""",(pr))
		if se.get('name'):
			frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(se.get('name')))
			frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_no = %s""",(se.get('name')))
			frappe.db.sql("""delete from `tabStock Entry` where name = %s""",(se.get('name')))

		vmcr_doc.cancel()
		update_vmcr_doc(data,row,collectiontime,collectiondate,vlcc_name,vmcr_stock_qty,response_dict)
	return ""

def vmcr_stock_qty_computation(vmcr,se):
	#to get the original quantity of fmcr calculating stock entry qty+ vmcr qty 
	#in case of loss
	vmcr_stock_qty = 0
	vmcr_doc = frappe.get_doc("Vlcc Milk Collection Record",vmcr)
	se_qty = frappe.db.get_value('Stock Entry Detail',
		{'parent':se.get('name')},'qty') or 0

	if se and se.get('wh_type') == 'Loss':
		vmcr_stock_qty = flt(se_qty,2) + flt(vmcr_doc.milkquantity,2)
	elif se and se.get('wh_type') == 'Gain':
		vmcr_stock_qty = flt(vmcr_doc.milkquantity,2) - flt(se_qty,2)
	else:
		vmcr_stock_qty = flt(vmcr_doc.milkquantity,2)
	return vmcr_stock_qty

def update_vmcr_doc(data,row,collectiontime,collectiondate,vlcc_name,vmcr_stock_qty,response_dict):
	edited_vmcr_doc = create_vmcr_doc(data,row,collectiontime,collectiondate,vlcc_name,response_dict)
	loss_gain_computation(fmcr_stock_qty=vmcr_stock_qty,row=row,
						data=data,vmcr_doc=edited_vmcr_doc,response_dict=response_dict,
						total_vmcr_qty=row.get('milkquantity'))

def create_vmcr_doc(data,row,collectiontime,collectiondate,vlcc_name,response_dict,is_vmcr_created=0):
	if validate_society_exist_dairy(data):
		if validate_vlcc(row):
			row.update(
				{
					"collectiontime": collectiontime,
					"qualitytime": row.get('qualitytime'), #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('qualitytime'))/1000)),
					"quantitytime": row.get('quantitytime'), #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('quantitytime'))/1000)),		
					"tippingendtime": row.get('tippingendtime'), #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('tippingendtime'))/1000)),		
					"tippingstarttime": row.get('tippingstarttime') ,#time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('tippingstarttime'))/1000)),
					"associated_vlcc": frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('farmerid')},'name'),
					"farmerid": row.get('farmerid'),
					"milkquality": str(row.get('milkquality')),
					"status": row.get('status'),
					"milk_quality_type": get_curdled_warehouse(data,row).get('milk_quality_type')
				})

			vmrc_doc = frappe.new_doc("Vlcc Milk Collection Record")
			vmrc_doc.id = data.get('id')
			vmrc_doc.imeinumber = data.get('imeinumber')
			vmrc_doc.rcvdtime = data.get('rcvdtime')
			vmrc_doc.processedstatus = data.get('processedstatus')
			vmrc_doc.societyid = data.get('societyid')
			vmrc_doc.vmcr_created = is_vmcr_created
			vmrc_doc.collectiondate =  collectiondate
			vmrc_doc.posting_date = getdate(row.get('collectiontime'))
			# vmrc_doc.shift = data.get('shift')
			# vmrc_doc.long_format_farmer_id = data.get('longformatfarmerid')
			# vmrc_doc.starttime = data.get('starttime') #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('starttime')/1000))
			# vmrc_doc.endtime = data.get('endtime') #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('endtime')/1000))
			# vmrc_doc.endshift = 1 if data.get('endshift') == True else 0
			# vmrc_doc.update(row)
			# vmrc_doc.update({
			# 	'amount':flt(row.get('rate') * row.get('milkquantity'),2)
			# })
			vmrc_doc.shift = data.get('shift')#creats Shrikant 27-10-18 20:24
			if data.get('shift') == "MORNING":
				# vmrc_doc.long_format_farmer_id = row.get('longformatfarmerid')
				vmrc_doc.long_format_farmer_id = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},"longformatfarmerid")
				farmerid_len = vmrc_doc.long_format_farmer_id.split('_')
				if len(farmerid_len) >= 4 and farmerid_len[2]:
					collectionroute = str(farmerid_len[2])

				#vmrc_doc.long_format_farmer_id = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},"longformatfarmerid")
			if data.get('shift') == "EVENING":
				vmrc_doc.long_format_farmer_id_e = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row.get('farmerid')},"longformatsocietyid_e")
				farmerid_len = vmrc_doc.long_format_farmer_id_e.split('_')
				if len(farmerid_len) >= 4 and farmerid_len[2]:
					collectionroute = str(farmerid_len[2])

			# Set Long Format Society ID value based which is beong used in list view of VMCR
			longsocietyid_listview = vmrc_doc.long_format_farmer_id if vmrc_doc.long_format_farmer_id else \
											vmrc_doc.long_format_farmer_id_e
			vmrc_doc.longsocietyid_listview = longsocietyid_listview.split('_')[-1]

			vmrc_doc.starttime = data.get('starttime') #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('starttime')/1000))
			vmrc_doc.endtime = data.get('endtime') #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('endtime')/1000))
			vmrc_doc.endshift = 1 if data.get('endshift') == True else 0
			vmrc_doc.update(row)
			vmrc_doc.update({
				'amount':flt(row.get('rate') * row.get('milkquantity'),2),
				'collectionroute':collectionroute
			})
			#end here SD
			# vmrc_doc.milkquality = row.get('milkquality')
			vmrc_doc.flags.ignore_permissions = True
			vmrc_doc.flags.is_api = True
			vmrc_doc.insert()
			vmrc_doc.submit()
			response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"vmrc":vmrc_doc.name})
			vlcc = validate_vlcc(row)
			make_purchase_receipt_dairy(data, row, vlcc_name, response_dict, vmrc_doc.name)
			return vmrc_doc
		else:
			traceback = "vlcc does not exist"
			frappe.throw(_("Vlcc Does not exist"))
	else :
		traceback = "Society Does Not Exist"
		frappe.throw(_("Society does not exist"))

def validate_vmrc_entry(row):

	return frappe.db.get_value('Vlcc Milk Collection Record',
			{"transactionid":row.get('transactionid'),"docstatus":['=',1] },"name")


def validate_society_exist_dairy(data):
	return frappe.db.sql("select name from `tabAddress` where centre_id = '{0}'"
			.format(data.get('societyid')))

def validate_vlcc(row):
	return  frappe.db.sql("select name from `tabVillage Level Collection Centre` where amcu_id = '{0}'".format(row.get('farmerid')),as_dict=1)


def make_purchase_receipt_dairy(data, row, vlcc, response_dict, vmrc):
	"""make Purchase receipt at Dairy Level if status accepted at VMCR"""

	co = frappe.db.get_value("Village Level Collection Centre",{'name':vlcc},"camp_office")
	item_code = ""
	
	try:
		create_item(row)
		make_uom_config("Nos")
		
		if row.get('milktype') == "COW":
			item_code = "COW Milk"
		elif row.get('milktype') == "BUFFALO":
			item_code = "BUFFALO Milk"

		item_ = frappe.get_doc("Item",item_code)
		company = frappe.db.get_value("Company",{"is_dairy":1},'name')
		if vlcc and company:
			rejected_milk_data =  get_curdled_warehouse(data,row)
			pr_co = make_purchase_receipt(data, row, vlcc, company, item_, response_dict, vmrc,co,rejected_milk_data.get('warehouse'))
			price_list_ = frappe.db.get_value("Item Price", {'item_code': item_code, 'price_list':'Standard Buying'},'name')
			# frappe.delete_doc("Item Price", price_list_)
			purchase_invoice_against_vlcc(data, row, vlcc, company, item_, response_dict, pr_co, vmrc,co,rejected_milk_data.get('warehouse'))

		else:
			frappe.throw(_("Head Office does not exist"))

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())


def get_curdled_warehouse(data,row):

	warehouse,milk_quality_type = "",""
	if row.get('milkquality') == 'G':
		milk_quality_type = 'Good'
		warehouse = frappe.db.get_value("Address", {"centre_id":data.get('societyid')}, 'warehouse')
	elif row.get('milkquality') == 'CT':
		milk_quality_type = 'Curdled by Transporter'
		warehouse = frappe.db.get_value("Address", {"centre_id":data.get('societyid')}, 'c_transporter_warehouse')
	elif row.get('milkquality') == 'CS':
		milk_quality_type = 'Curdled by Society'
		warehouse = frappe.db.get_value("Address", {"centre_id":data.get('societyid')}, 'c_society_warehouse')
	elif row.get('milkquality') == 'SS':
		milk_quality_type = 'Sub Standard'
		warehouse = frappe.db.get_value("Address", {"centre_id":data.get('societyid')}, 'sub_std_warehouse')
	
	return {"warehouse":warehouse,"milk_quality_type":milk_quality_type}


def make_uom_config(doc):
	uom_obj = frappe.get_doc("UOM",doc)
	uom_obj.must_be_whole_number = 0
	uom_obj.save()


def delivery_note_for_vlcc(data, row, item_, vlcc, company, response_dict, vmrc):
	try:
		rate = row.get('rate') if row.get('rate') else 0
		if row.get('milkquality') == 'SS' and row.get('rate') >= 0:
			rate = 0
		customer = frappe.db.get_value("Village Level Collection Centre", vlcc, "plant_office")
		warehouse = frappe.db.get_value("Village Level Collection Centre", {"amcu_id": row.get('farmerid')}, 'warehouse')
		cost_center = frappe.db.get_value("Cost Center", {"company": vlcc}, 'name')
		delivry_obj = frappe.new_doc("Delivery Note")
		delivry_obj.customer = customer
		delivry_obj.vlcc_milk_collection_record = vmrc
		delivry_obj.company = vlcc
		delivry_obj.append("items",
		{
			"item_code": item_.item_code,
			"item_name": item_.item_code,
			"description": item_.item_code,
			"uom": "Litre",
			"qty": row.get('milkquantity'),
			"rate": rate,
			"price_list_rate": rate,
			"amount": flt(rate * row.get('milkquantity'),2),
			"warehouse": warehouse,
			"cost_center": cost_center
		})
		delivry_obj.status = "Completed"
		delivry_obj.flags.ignore_permissions = True
		delivry_obj.submit()
		item_price_c = frappe.db.get_value("Item Price",{'price_list':"Standard Selling",'item_code' : item_.item_code}, 'name')
		# frappe.delete_doc("Item Price", item_price_c)
		set_posting_datetime(delivry_obj,row)
		set_stock_ledger_date(delivry_obj,row)
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Delivery Note" : delivry_obj.name})
		sales_invoice_against_dairy(data, row, customer, warehouse, item_, vlcc, cost_center, response_dict, delivry_obj.name, vmrc)
	
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error":frappe.get_traceback()})


def sales_invoice_against_dairy(data, row, customer, warehouse, item_,vlcc, cost_center, response_dict, dn_name, vmrc):
	try:
		rate = row.get('rate') if row.get('rate') else 0
		if row.get('milkquality') in 'SS' and row.get('rate') >= 0:
			rate = 0
		days = frappe.db.get_value("VLCC Settings", vlcc, 'configurable_days') if frappe.db.get_value("VLCC Settings", vlcc, 'configurable_days') else 0
 		si_obj = frappe.new_doc("Sales Invoice")
 		si_obj.customer = customer
 		# si_obj.due_date = add_to_date(getdate(row.get('collectiontime')),0,0,cint(days))
 		si_obj.company = vlcc
		si_obj.vlcc_milk_collection_record = vmrc
 		si_obj.append("items",
 		{
 			"item_code": item_.item_code,
 			"qty":row.get('milkquantity'),
 			"rate": rate,
 			"price_list_rate": rate,
 			"amount": flt(rate * row.get('milkquantity'),2),
 			"warehouse": warehouse,
			"cost_center": cost_center,
			"delivery_note": dn_name
 		})
 		si_obj.flags.ignore_permissions = True
		si_obj.submit()
		set_posting_datetime(si_obj,row,days)
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"sales invoice": si_obj.name})

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())


def make_purchase_receipt(data, row, vlcc, company, item_, response_dict, vmrc,co,warehouse=None):
	try:
		rate = row.get('rate') if row.get('rate') else 0
		if row.get('milkquality') == 'SS' and row.get('rate') >= 0:
			rate = 0
		purchase_rec = frappe.new_doc("Purchase Receipt")
		purchase_rec.supplier =  vlcc
		purchase_rec.vlcc_milk_collection_record = vmrc
		purchase_rec.milk_type = row.get('milkquality')
		purchase_rec.company = company
		purchase_rec.chilling_centre = frappe.db.get_value("Address", {"centre_id" : data.get('societyid')},'name')
		# purchase_rec.camp_office = co
		purchase_rec.append("items",
			{
				"item_code": item_.item_code,
				"item_name": item_.item_code,
				"description": item_.item_code,
				"uom": "Litre",
				"qty": row.get('milkquantity'),
				"rate": rate,
				"price_list_rate": rate,
				"amount": flt(row.get('milkquantity') * rate,2),
				"warehouse": warehouse #frappe.db.get_value("Address", {"centre_id":data.get('societyid')}, 'warehouse')
			}
		)
		purchase_rec.status = "Completed"
		purchase_rec.per_billed = 100
		purchase_rec.flags.ignore_permissions = True
		purchase_rec.submit()
		price_list_ = frappe.db.get_value("Item Price",{'item_code': item_.item_code,'price_list':"Standard Buying"},'name')
		# frappe.delete_doc("Item Price",price_list_)
		set_posting_datetime(purchase_rec,row)
		set_stock_ledger_date(purchase_rec,row)
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"purchase_receipt": purchase_rec.name})
		delivery_note_for_vlcc(data, row, item_, vlcc, company, response_dict, vmrc)

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())

	return purchase_rec.name


def create_item(row):

	if row.get('milktype') and not frappe.db.exists('Item', row.get('milktype')+" Milk"):
			item = frappe.new_doc("Item")
			item.item_code = row.get('milktype')+" Milk"
			item.item_group = "Milk & Products"
			item.weight_uom = "Litre"
			item.is_stock_item = 1
			item.insert()


def purchase_invoice_against_vlcc(data, row, vlcc, company, item_, response_dict, pr_co, vmrc,co,warehouse=None):

	try:
		rate = row.get('rate') if row.get('rate') else 0
		if row.get('milkquality') == 'SS' and row.get('rate') >= 0:
			rate = 0
		dairy_setting = frappe.get_doc("Dairy Setting")
		days = dairy_setting.configurable_days if dairy_setting.configurable_days else 0
		pi_obj = frappe.new_doc("Purchase Invoice")
		pi_obj.supplier =  vlcc
		pi_obj.vlcc_milk_collection_record = vmrc
		pi_obj.pi_type = "VMCR"
		# pi_obj.due_date = add_to_date(getdate(row.get('collectiontime')),0,0,days)
		pi_obj.chilling_centre = frappe.db.get_value("Address", \
							{"centre_id" : data.get('societyid')}, 'name')
		pi_obj.company = company
		pi_obj.append("items",
			{
				"item_code": item_.item_code,
				"item_name": item_.item_code,
				"description": item_.item_code,
				"uom": "Litre",
				"qty": row.get('milkquantity'),
				"rate": rate,
				"price_list_rate": rate,
				"amount": flt(rate * row.get('milkquantity'),2),
				"warehouse": warehouse, #frappe.db.get_value("Address", {"centre_id":data.get('societyid')}, 'warehouse'),
				"purchase_receipt": pr_co
			}
		)

		account = frappe.db.get_value("Address", {"centre_id": data.get('societyid')}, "expense_account")
		pi_obj.remarks = "[#"+account+"#]"
		pi_obj.flags.ignore_permissions = True
		pi_obj.submit()
		set_posting_datetime(pi_obj,row,days)
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"purchase invoice":pi_obj.name})
	
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())


def purchase_invoice_against_farmer(data, row, vlcc,  farmer, item_, response_dict, pr, fmrc, days=None):

	try:
		pi_obj = frappe.new_doc("Purchase Invoice")
		pi_obj.supplier =  farmer
		pi_obj.farmer_milk_collection_record = fmrc
		# pi_obj.due_date = add_to_date(getdate(row.get('collectiontime')),0,0,cint(days))
		pi_obj.company = vlcc
		pi_obj.append("items",
			{
				"item_code": item_.item_code,
				"item_name": item_.item_code,
				"description": item_.item_code,
				"uom": "Litre",
				"qty": row.get('milkquantity'),
				"rate": row.get('rate'),
				"amount": row.get('amount'),
				"warehouse": frappe.db.get_value("Village Level Collection Centre", vlcc, 'warehouse'),
				"purchase_receipt": pr
			}
		)
		pi_obj.flags.ignore_permissions = True
		pi_obj.submit()
		set_posting_datetime(pi_obj,row,days)
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"purchase invoice":pi_obj.name})
	
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())

def set_posting_datetime(doc,row,days=None):
	if row.get('collectiontime'):
		frappe.db.sql("""update `tab{0}` 
			set 
				posting_date = '{1}',posting_time = '{2}'
			where 
				name = '{3}'""".format(doc.doctype,getdate(row.get('collectiontime')),
					get_time(row.get('collectiontime')),doc.name))
		if doc.doctype in ['Sales Invoice','Purchase Invoice']:
			frappe.db.sql("""update `tab{0}` 
				set 
					due_date = '{1}'
				where 
					name = '{2}'""".format(doc.doctype,add_to_date(getdate(row.get('collectiontime')),0,0,cint(days)),doc.name))

		frappe.db.sql("""update `tabGL Entry` 
					set 
						posting_date = %s
					where 
						voucher_no = %s""",(getdate(row.get('collectiontime')),doc.name))

def set_stock_ledger_date(doc,row):
	if row.get('collectiontime'):
		frappe.db.sql("""update `tabStock Ledger Entry` 
				set 
					posting_date = %s
				where 
					voucher_no = %s""",(getdate(row.get('collectiontime')),doc.name))

@frappe.whitelist()
def log_out():
	try:
		response_dict = {}
		frappe.local.login_manager.logout()
		frappe.db.commit()
		response_dict.update({"status":"Success", "message":"Successfully Logged Out"})
	except Exception, e:
		response_dict.update({"status":"Error", "error":e, "traceback":frappe.get_traceback()})

	return response_dict

@frappe.whitelist(allow_guest=True)
def ping():
	"""
	Check server connection
	"""
	return "Success !! Magic begins, Here we Go !!"