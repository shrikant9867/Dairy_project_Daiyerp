# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
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
		fmrc = make_fmrc(api_data)
		response_dict.update({
			"status": "Updated",
			"data":	fmrc
			})

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})

	return response_dict


def make_fmrc(data):
	"""record JSON irrespective of 'status', epoch to timestamp(Op)
		no of field = 56(enum), update row 40 type field in one row to make one FMCR : VLCC 
	"""
	
	if data.get('societyid'):
		for i,v in data.items():
			if i == "collectionEntryList":
				for row in v:
					fmrc_entry = validate_fmrc_entry(data,row)
					if not fmrc_entry:
						if validate_society_exist(data) and farmer_associate_vlcc(data,row):							
							vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
							farmer = frappe.db.get_value("Farmer",{"vlcc_name": vlcc},'name')
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
							if row.get('status') == "Accept":
								make_purchase_receipt(data, row, vlcc, farmer)

						else : 
							return "Could not find vlcc associated with <b>'{0}'</b>society id or farmer association with specific vlcc".format(data.get('societyid'))
					else: 
						return fmrc_entry					
	
	else: 
		return "Society Id Missing in Request data"		


def validate_fmrc_entry(data, row):
	"""validate for duplicate entry for Farmer Milk Record Collection"""

	collectiontime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('collectiontime'))/1000))
	collectiondate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
	
	return frappe.db.sql(""" select name,collectiontime,societyid,rcvdtime,
		collectiondate,shift,farmerid,milktype from `tabFarmer Milk Collection Record`
		where societyid='{0}' and collectiontime = '{1}' and collectiondate = '{2}'
		and  rcvdtime = '{3}' and shift = '{4}' and farmerid = '{5}' and milktype = '{6}'
		""".format(data.get('societyid'),collectiontime,collectiondate,
			data.get('rcvdtime'),data.get('shift'),row.get('farmerid'),row.get('milktype')),as_dict=1
		)


def validate_society_exist(data):

	return frappe.db.sql("""select name from `tabVillage Level Collection Centre`
		where amcu_id = '{0}'""".format(data.get('societyid')))


def farmer_associate_vlcc(data, row):
	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
	return frappe.db.get_value("Farmer",{"vlcc_name": vlcc},'name')


def make_purchase_receipt(data, row, vlcc, farmer):
	"""If Accepted at AMCU unit make purchase receipt.Making Item On head further, groups and
	   items(Hard CD).Maintainable over milk type.stock to respective vlcc must 
	   be auxillary(enum). : VLCC """

	item_code = ""
	
	if row.get('milktype') and not frappe.db.exists('Item', row.get('milktype')+" Milk"):
		item = frappe.new_doc("Item")
		item.item_code = row.get('milktype')+" Milk"
		item.item_group = "Milk & Products"
		item.is_stock_item = 1
		item.insert()
	
	if row.get('milktype') == "COW":
		item_code = "COW Milk"
	elif row.get('milktype') == "BUFFALO":
		item_code = "BUFFALO Milk"

	item_ = frappe.get_doc("Item",item_code)
	if farmer:
		purchase_rec = frappe.new_doc("Purchase Receipt")
		purchase_rec.supplier =  frappe.db.get_value("Farmer",farmer,'full_name')
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
				"warehouse": frappe.db.get_value("Village Level Collection Centre", vlcc, 'warehouse')
			}
		)
		purchase_rec.flags.ignore_permissions = True
		purchase_rec.submit()


@frappe.whitelist()
def create_farmer(data):
	"""Separate API(client req), should have been merge in main(future scope) : VLCC"""

	response_dict = {}
	api_data = json.loads(data)
	try:
		if api_data:
			for row in api_data:
				if row.get('society_id'):
					vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('society_id')},'name')
					if vlcc and not frappe.db.exists("Farmer",row.get("farmer_id")):
						farmer_obj = frappe.new_doc("Farmer")
						farmer_obj.full_name = row.get('full_name')
						farmer_obj.farmer_id = row.get('farmer_id')
						farmer_obj.contact_number = row.get('contact_no')
						farmer_obj.vlcc_name = vlcc
						farmer_obj.insert()
						response_dict.update({"status":"success","data":farmer_obj.__dict__})
	
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status":"error","message":e, "traceback": frappe.get_traceback()})	

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
		vmrc = make_vmrc(api_data)

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status":"error","message":e, "traceback": frappe.get_traceback()})


def make_vmrc(data):
	""":Dairy"""

	try:
		if data.get('societyid'):
			for i,v in data.items():
				if i == "collectionEntryList":
					for row in v:
						collectiontime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('collectiontime'))/1000))
						collectiondate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
						vlcc_name = frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('farmerid')},'name')		
						vmrc = validate_vmrc_entry(data,row, collectiontime, collectiondate)
						if not vmrc:
							if validate_society_exist_dairy(data):
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
									print "##################",row.get('status') == "Accept"
									vlcc = validate_vlcc(row)
									if row.get('status') == "Accept":
										make_purchase_receipt_dairy(data, row, vlcc)
								else:
									frappe.throw(_("Vlcc Does not exist"))
							else :
								frappe.throw(_("Society does not exist"))
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())

							

def validate_vmrc_entry(data, row, collectiontime, collectiondate):

	return frappe.db.sql(""" select name,collectiontime,societyid,rcvdtime,
						collectiondate,shift,farmerid,milktype from 
						`tabVlcc Milk Collection Record` where societyid='{0}' and 
						collectiontime = '{1}' and collectiondate = '{2}'
						and  rcvdtime = '{3}' and shift = '{4}' and farmerid = '{5}' and
						milktype = '{6}'""".format(data.get('societyid'),collectiontime,
						collectiondate,data.get('rcvdtime'),data.get('shift'),
						row.get('farmerid'),row.get('milktype')),as_dict=1)


def validate_society_exist_dairy(data):
	return frappe.db.sql("select name from `tabAddress` where centre_id = '{0}'"
			.format(data.get('societyid')))

def validate_vlcc(row):
	return frappe.db.get_value("Village Level Collection Centre", {"amcu_id": row.get('farmerid')}, 'name')

def make_purchase_receipt_dairy(data, row, vlcc):
	"""make Purchase receipt at Dairy Level if status accepted at VMCR"""
	print "+++++++++++++++++++",vlcc
	item_code = ""
	
	try:
		if row.get('milktype') and not frappe.db.exists('Item', row.get('milktype')+" Milk"):
			item = frappe.new_doc("Item")
			item.item_code = row.get('milktype')+" Milk"
			item.item_group = "Milk & Products"
			item.is_stock_item = 1
			item.insert()
		
		if row.get('milktype') == "COW":
			item_code = "COW Milk"
		elif row.get('milktype') == "BUFFALO":
			item_code = "BUFFALO Milk"

		item_ = frappe.get_doc("Item",item_code)
		if vlcc:
			purchase_rec = frappe.new_doc("Purchase Receipt")
			purchase_rec.supplier =  frappe.db.get_value("Farmer",farmer,'full_name')
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
					"warehouse": frappe.db.get_value("Village Level Collection Centre", vlcc, 'warehouse')
				}
			)
			purchase_rec.flags.ignore_permissions = True
			purchase_rec.submit()

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())