# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class VLCCSettings(Document):
	def validate(self):
		user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)
		self.vlcc = user_doc.get('company')

@frappe.whitelist()
def check_record_exist():
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)
	config = frappe.get_all("VLCC Settings",filters = {"vlcc":user_doc.get('company')})
	if len(config):
		return True
	else:
		return False


def vlcc_setting_permission(user):

	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)

	config_list =['"%s"'%i.get('name') for i in frappe.db.sql("""select name from 
				`tabVLCC Settings` 
				where vlcc = %s""",(user_doc.get('company')),as_dict=True)]

	if config_list:
		if user != 'Administrator' and 'Vlcc Manager' in roles:
			return """`tabVLCC Settings`.name in ({date})""".format(date=','.join(config_list))
	else:
		if user != 'Administrator':
			return """`tabVLCC Settings`.name = 'Guest' """
