# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import requests
import json


def make_dairy_log(**kwargs):
	dlog = frappe.get_doc({"doctype":"Dairy Log"})
	dlog.update({
			"title":kwargs.get("title"),
			"method":kwargs.get("method"),
			"status":kwargs.get("status"),
			"data":json.dumps(kwargs.get("data", "")),
			"error_message":kwargs.get("message", ""),
			"traceback":kwargs.get("traceback", "")
		})
	dlog.insert(ignore_permissions=True)
	frappe.db.commit()
	return dlog.name