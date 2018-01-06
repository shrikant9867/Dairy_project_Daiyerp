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
import dairy_utils as utils
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
	if data.get('societyid'):
		for i,v in data.items():
			if i == "collectionEntryList":
				for row in v:
					try:
						if data.get('imeinumber') and data.get('rcvdtime') and data.get('shift') and data.get('collectiondate'):
							if row.get('farmerid') and row.get('milktype') and row.get('collectiontime') and row.get('milkquantity') and row.get('rate') and row.get('status'):
								response_dict.update({row.get('farmerid')+"-"+row.get('milktype'): []})
								fmrc_entry = validate_fmrc_entry(data,row)
								if not fmrc_entry:
									if validate_society_exist(data):
										if farmer_associate_vlcc(data,row):
											vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
											farmer = frappe.db.get_value("Farmer",{"vlcc_name": vlcc},'name')
											farmer_supplier = frappe.db.get_value("Farmer",row.get('farmerid'),'full_name')
											row.update(
												{
													"collectiontime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('collectiontime'))/1000)),
													"qualitytime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('qualitytime'))/1000)),
													"quantitytime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('quantitytime'))/1000))
												}
											)
											fmrc_doc = frappe.new_doc("Farmer Milk Collection Record")
											fmrc_doc.id = data.get('id')
											fmrc_doc.associated_vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
											fmrc_doc.imeinumber = data.get('imeinumber')
											fmrc_doc.rcvdtime = data.get('rcvdtime')
											fmrc_doc.processedstatus = data.get('processedstatus')
											fmrc_doc.societyid = data.get('societyid')
											fmrc_doc.collectiondate =  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
											fmrc_doc.shift = data.get('shift')
											fmrc_doc.starttime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('starttime')/1000))
											fmrc_doc.endtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('endtime')/1000))
											fmrc_doc.endshift = 1 if data.get('endshift') == True else 0
						 					fmrc_doc.update(row)
											fmrc_doc.flags.ignore_permissions = True
											fmrc_doc.submit()
											response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"fmrc": fmrc_doc.name})
											if row.get('status') == "Accept":
												pr = make_purchase_receipt_vlcc(data, row, vlcc, farmer_supplier, response_dict, fmrc_doc.name )
												purchase_invoice_against_farmer(data, row, vlcc,  farmer_supplier, pr.get('item_'), response_dict, pr.get('pr_obj'), fmrc_doc.name)
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

	else:
		response_dict.update({"status":"Error","response":"society id missing"})
	return response_dict


def validate_fmrc_entry(data, row):
	"""validate for duplicate entry for Farmer Milk Record Collection"""

	collectiontime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('collectiontime'))/1000))
	collectiondate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
	
	return frappe.db.sql(""" select name,collectiontime,societyid,rcvdtime,
		collectiondate,shift,farmerid,milktype from `tabFarmer Milk Collection Record`
		where societyid='{0}' and collectiontime = '{1}' and collectiondate = '{2}'
		and  rcvdtime = '{3}' and shift = '{4}' and farmerid = '{5}' and milktype = '{6}'
		""".format(data.get('societyid'),collectiontime,collectiondate,
			data.get('rcvdtime'),data.get('shift'),row.get('farmerid'),row.get('milktype')),as_dict=1,debug=1
		)


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
		print "_________",cost_center,vlcc,fmrc
		item_ = frappe.get_doc("Item",item_code)
		if farmer:
			print "_________________________________"
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
					"amount": row.get('amount'),
					"warehouse": frappe.db.get_value("Village Level Collection Centre", vlcc, 'warehouse'),
					"cost_center": cost_center
				}
			)
			purchase_rec.status = "Completed"
			purchase_rec.per_billed = 100
			purchase_rec.flags.ignore_permissions = True
			purchase_rec.submit()
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
			try:
				if row.get('society_id') and row.get('farmer_id') and row.get('full_name'):
					vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('society_id')},'name')
					if vlcc :
						if not frappe.db.sql("select full_name from `tabFarmer` where full_name=%s",(row.get("full_name"))):
							if not frappe.db.exists("Farmer",row.get("farmer_id")):
								farmer_obj = frappe.new_doc("Farmer")
								farmer_obj.full_name = row.get('full_name')
								farmer_obj.farmer_id = row.get('farmer_id')
								farmer_obj.contact_number = row.get('contact_no')
								farmer_obj.vlcc_name = vlcc
								farmer_obj.insert()
								response_dict.get(row.get('farmer_id')).append({"status": "success","name":farmer_obj.name})
							else:
								traceback = " Farmer ID Exist"
								frappe.throw(_("Id Exist"))
						else:
							traceback = "Farmer Exist with same name"
							frappe.throw("Farmer Exist with same name")
					else:
						traceback = "Society ID(VLCC-amcu id) does not exist"
						frappe.throw(_("Society does not exist"))
				else:
					traceback = "Society ID, Full Name, Farmer ID are manadatory data"
					frappe.throw(_("Society ID, full_name, farmerid  does not exist(Vlcc at ERP)"))
	
			except Exception,e:
				utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
				data = data, message=e, traceback=frappe.get_traceback())
				response_dict.get(row.get('farmer_id')).append({"Error": traceback})
				# response_dict.get(row('farmer_id')).append(farmer_obj.name)

	return response_dict		


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
	traceback = ""
	if data.get('societyid'):
		for i,v in data.items():
			if i == "collectionEntryList":
				for row in v:
					try:
						if data.get('imeinumber') and data.get('rcvdtime') and data.get('shift') and data.get('collectiondate'):
							if row.get('farmerid') and row.get('milktype') and row.get('collectiontime') and row.get('milkquantity') and row.get('rate') and row.get('status'):
								response_dict.update({row.get('farmerid')+"-"+row.get('milktype'):[]})
								collectiontime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('collectiontime'))/1000))
								collectiondate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
								vlcc_name = frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('farmerid')},'name')		
								vmrc = validate_vmrc_entry(data,row, collectiontime, collectiondate)
								if not vmrc:
									if  validate_society_exist_dairy(data):
										if validate_vlcc(row):
											row.update(
												{
													"collectiontime": collectiontime,
													"qualitytime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('qualitytime'))/1000)),
													"quantitytime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('quantitytime'))/1000)),		
													"tippingendtime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('tippingendtime'))/1000)),		
													"tippingstarttime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('tippingstarttime'))/1000)),
													"associated_vlcc": frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('farmerid')},'name')		
												})
											vmrc_doc = frappe.new_doc("Vlcc Milk Collection Record")
											vmrc_doc.id = data.get('id')
											vmrc_doc.imeinumber = data.get('imeinumber')
											vmrc_doc.rcvdtime = data.get('rcvdtime')
											vmrc_doc.processedstatus = data.get('processedstatus')
											vmrc_doc.societyid = data.get('societyid')
											vmrc_doc.collectiondate =  collectiondate
											vmrc_doc.shift = data.get('shift')
											vmrc_doc.starttime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('starttime')/1000))
											vmrc_doc.endtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('endtime')/1000))
											vmrc_doc.endshift = 1 if data.get('endshift') == True else 0
						 					vmrc_doc.update(row)
											vmrc_doc.flags.ignore_permissions = True
											vmrc_doc.submit()
											response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"vmrc":vmrc_doc.name})
											vlcc = validate_vlcc(row)
											if row.get('status') == "Accept":
												make_purchase_receipt_dairy(data, row, vlcc_name, response_dict, vmrc_doc.name)
										else:
											traceback = "vlcc does not exist"
											frappe.throw(_("Vlcc Does not exist"))
									else :
										traceback = "Society Does Not Exist"
										frappe.throw(_("Society does not exist"))
								else:
									response_dict.update({row.get('farmerid')+"-"+row.get('milktype'):["created already check erpnext.Exception if any check dairy log"]})
							else:
								response_dict.update({"status":["Error status_response Data Missing. status_message farmerid,milktype,collectiontime,milkquantity,rate are manadatory"]})
						else:
							response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"Error","response":"Data Missing","message":"imeinumber,collectionDate,shift,rcvdTime are manadatory"})
					except Exception,e:
						utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
						data = data, message=e, traceback=frappe.get_traceback())
						response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": traceback})


def validate_vmrc_entry(data, row, collectiontime, collectiondate):
	
	print data.get('rcvdtime'),frappe.db.sql(""" select name,rcvdtime from `tabVlcc Milk Collection Record` where societyid='{0}' and 
						collectiontime = '{1}' and collectiondate = '{2}'
						and  rcvdtime = '{3}' and shift = '{4}' and farmerid = '{5}' and
						milktype = '{6}'""".format(data.get('societyid'),collectiontime,
						collectiondate,data.get('rcvdtime'),data.get('shift'),
						row.get('farmerid'),row.get('milktype')),as_dict=1)

	return frappe.db.sql(""" select name from `tabVlcc Milk Collection Record` where societyid='{0}' and 
						collectiontime = '{1}' and collectiondate = '{2}'
						and  rcvdtime = '{3}' and shift = '{4}' and farmerid = '{5}' and
						milktype = '{6}'""".format(data.get('societyid'),collectiontime,
						collectiondate,data.get('rcvdtime'),data.get('shift'),
						row.get('farmerid'),row.get('milktype')),as_dict=1)


def validate_society_exist_dairy(data):
	return frappe.db.sql("select name from `tabAddress` where centre_id = '{0}'"
			.format(data.get('societyid')))

def validate_vlcc(row):
	return  frappe.db.sql("select name from `tabVillage Level Collection Centre` where amcu_id = '{0}'".format(row.get('farmerid')),as_dict=1)


def make_purchase_receipt_dairy(data, row, vlcc, response_dict, vmrc):
	"""make Purchase receipt at Dairy Level if status accepted at VMCR"""
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
			pr_co = make_purchase_receipt(data, row, vlcc, company, item_, response_dict, vmrc)
			purchase_invoice_against_vlcc(data, row, vlcc, company, item_, response_dict, pr_co, vmrc)

		else:
			frappe.throw(_("Head Office does not exist"))

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())


def make_uom_config(doc):
	uom_obj = frappe.get_doc("UOM",doc)
	uom_obj.must_be_whole_number = 0
	uom_obj.save()


def delivery_note_for_vlcc(data, row, item_, vlcc, company, response_dict, vmrc):
	try:
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
			"rate": row.get('rate'),
			"amount": row.get('amount'),
			"warehouse": warehouse,
			"cost_center": cost_center
		})
		delivry_obj.status = "Completed"
		delivry_obj.flags.ignore_permissions = True
		delivry_obj.submit()
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Delivery Note" : delivry_obj.name})
		sales_invoice_against_dairy(data, row, customer, warehouse, item_, vlcc, cost_center, response_dict, delivry_obj.name, vmrc)
	
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error":frappe.get_traceback()})


def sales_invoice_against_dairy(data, row, customer, warehouse, item_,vlcc, cost_center, response_dict, dn_name, vmrc):
	try:
		si_obj = frappe.new_doc("Sales Invoice")
		si_obj.customer = customer
		si_obj.company = vlcc
		si_obj.vlcc_milk_collection_record = vmrc
		si_obj.append("items",
		{
			"item_code": item_.item_code,
			"item_name": item_.item_code,
			"description": item_.item_code,
			"uom": "Litre",
			"qty": row.get('milkquantity'),
			"rate": row.get('rate'),
			"amount": row.get('amount'),
			"warehouse": warehouse,
			"cost_center": cost_center,
			"delivery_note": dn_name
		})
		si_obj.flags.ignore_permissions = True
		si_obj.submit()
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"sales invoice": si_obj.name})

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())


def make_purchase_receipt(data, row, vlcc, company, item_, response_dict, vmrc):

	try:
		purchase_rec = frappe.new_doc("Purchase Receipt")
		purchase_rec.supplier =  vlcc
		purchase_rec.vlcc_milk_collection_record = vmrc
		purchase_rec.company = company
		purchase_rec.append("items",
			{
				"item_code": item_.item_code,
				"item_name": item_.item_code,
				"description": item_.item_code,
				"uom": "Litre",
				"qty": row.get('milkquantity'),
				"rate": row.get('rate'),
				"amount": row.get('amount'),
				"warehouse": frappe.db.get_value("Address", {"centre_id":data.get('societyid')}, 'warehouse')
			}
		)
		purchase_rec.status = "Completed"
		purchase_rec.per_billed = 100
		purchase_rec.flags.ignore_permissions = True
		purchase_rec.submit()
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
			item.is_stock_item = 1
			item.insert()


def purchase_invoice_against_vlcc(data, row, vlcc, company, item_, response_dict, pr_co, vmrc):

	try:
		pi_obj = frappe.new_doc("Purchase Invoice")
		pi_obj.supplier =  vlcc
		pi_obj.vlcc_milk_collection_record = vmrc
		pi_obj.company = company
		pi_obj.append("items",
			{
				"item_code": item_.item_code,
				"item_name": item_.item_code,
				"description": item_.item_code,
				"uom": "Litre",
				"qty": row.get('milkquantity'),
				"rate": row.get('rate'),
				"amount": row.get('amount'),
				"warehouse": frappe.db.get_value("Address", {"centre_id":data.get('societyid')}, 'warehouse'),
				"purchase_receipt": pr_co
			}
		)
		pi_obj.flags.ignore_permissions = True
		pi_obj.submit()
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"purchase invoice":pi_obj.name})
	
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())


def purchase_invoice_against_farmer(data, row, vlcc,  farmer, item_, response_dict, pr, fmrc):

	try:
		pi_obj = frappe.new_doc("Purchase Invoice")
		pi_obj.supplier =  farmer
		pi_obj.farmer_milk_collection_record = fmrc
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
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"purchase invoice":pi_obj.name})
	
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())


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

