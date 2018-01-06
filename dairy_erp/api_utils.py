# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt
# Author Khushal Trivedi

from __future__ import unicode_literals
import frappe
import time
from frappe.utils import flt, now_datetime, cstr
from frappe import _
import json


@frappe.whitelist()
def log_out():
	response_dict = {}
	try:
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

def make_mobile_log(**kwargs):
	mlog = frappe.get_doc({"doctype":"Mobile App Log"})
	mlog.update({
			"title":kwargs.get("title"),
			"method":kwargs.get("method"),
			"sync_time": now_datetime(),
			"status":kwargs.get("status"),
			"data":json.dumps(kwargs.get("data", "")),
			"error_message":kwargs.get("message", ""),
			"traceback":kwargs.get("traceback", "")
		})
	mlog.insert(ignore_permissions=True)
	frappe.db.commit()
	return mlog.name
