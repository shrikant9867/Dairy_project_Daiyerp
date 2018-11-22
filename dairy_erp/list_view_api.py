# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stellapps Technologies Private Ltd.
# For license information, please see license.txt
# Author Khushal Trivedi

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
from frappe import _
import api_utils as utils


@frappe.whitelist()
def get_list_view(data):
	
	response_dict = {}
	
	if data  in ["Material Indent","Delivery Note", "Purchase Order"]:
		list_view = frappe.db.sql()
	else:
		response_dict.update({"status":"error","message":"data can be one of Material Indent, Delivery Note,Purchase Order"})
	return response_dict
