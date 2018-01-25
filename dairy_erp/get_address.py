# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt



# Author Siddhant Chaudhari

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe import _
import dairy_utils as utils
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
import requests
import json

@frappe.whitelist()
def get_address_query(frm):
	print "++++++++++++++++++++++",frm.doc.links
	query = frappe.db.sql("""select parent from `tabDynamic Link` where link_doctype = 'Company' and link_name = 'khadki_vlcc'""");
	print "***************************",query
	return query

