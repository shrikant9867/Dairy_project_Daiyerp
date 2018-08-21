# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate,get_time
import time
from frappe import _
import json