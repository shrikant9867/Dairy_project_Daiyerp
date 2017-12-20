# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
import dairy_utils as utils
import requests
import json


@frappe.whitelist()
def create_fmrc(data):
	""" API for pushing amcu data over erpnext. mapper must of field type to update doc.
		Lower casing for the same, create farmer milk record if accepted issue Purchase Receipt
		Make Log for sync fail"""
	
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
		make_fmrc(api_data)

	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())


def make_fmrc(data):
	"""record JSON irrespective of status, epoc to timestamp(Op)"""
	
	if data.get('societyid'):
		for i,v in data.items():
			if i == "collectionEntryList":
				for row in v:
					row.update(
						{
							"collectiontime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(data.get('collectiontime'))/1000)),
							"qualitytime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(data.get('qualitytime'))/1000)),
							"quantitytime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(data.get('quantitytime'))/1000))
						}
					)
					fmrc_doc = frappe.new_doc("Farmer Milk Collection Record")
					fmrc_doc.id = data.get('id')
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
			