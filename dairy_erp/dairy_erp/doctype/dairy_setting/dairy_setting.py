# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class DairySetting(Document):

	def validate(self):
		vlcc_list = [vlcc.get('name') for vlcc in frappe.get_all("Village Level Collection Centre")]
		for vlcc in vlcc_list:
			if frappe.db.exists("VLCC Settings",vlcc):
				vlcc_settings = frappe.get_doc("VLCC Settings",vlcc)
				if vlcc_settings and vlcc_settings.flag_negative_effective_credit == 0:
					frappe.db.set_value("VLCC Settings",vlcc,'allow_negative_effective_credit',\
							self.allow_negative_effective_credit)