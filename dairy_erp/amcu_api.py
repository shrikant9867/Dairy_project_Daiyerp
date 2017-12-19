# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import dairy_utils as utils
import requests
import json


@frappe.whitelist()
def create_fmrc(data):
	""" API for pushing amcu data over erpnext."""
	
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
	
	if data.get('societyid'):
		for i,v in data.items():
			if i == "collectionEntryList":
				pass
			