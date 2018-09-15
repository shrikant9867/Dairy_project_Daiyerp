# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe import _
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate,get_time
from frappe.utils.data import add_to_date
import dairy_utils as utils
import json



def auto_cycle_create():
	pass