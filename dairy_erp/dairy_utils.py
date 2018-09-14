# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import requests
from frappe.utils import flt, now_datetime, cstr, random_string
import json


def make_dairy_log(**kwargs):
	dlog = frappe.get_doc({"doctype":"Dairy Log"})
	dlog.update({
			"title":kwargs.get("title"),
			"method":kwargs.get("method"),
			"sync_time": now_datetime(),
			"status":kwargs.get("status"),
			"data":json.dumps(kwargs.get("data", "")),
			"error_message":kwargs.get("message", ""),
			"traceback":kwargs.get("traceback", "")
		})
	dlog.insert(ignore_permissions=True)
	frappe.db.commit()
	return dlog.name

def make_agrupay_log(**kwargs):
	ag_log = frappe.get_doc({"doctype": "AgRupay Log"})
	ag_log.update({
		"status": kwargs.get('status'),
		"request_data": kwargs.get('request_data'),
		"sync_time": kwargs.get('sync_time'),
		"response_text": kwargs.get('response_text'),
		"response_code": kwargs.get('response_code')
		})
	ag_log.insert(ignore_permissions=True)
	frappe.db.commit()
	return ag_log.name



