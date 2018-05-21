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
		self.check_farmer_exist()

	def check_farmer_exist(self):
		user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
		farmer_id = frappe.db.get_value("Farmer",
			{"vlcc_name":user_doc.get('company')},"farmer_id")
		if farmer_id:
			if self.farmer_id1 == farmer_id or self.farmer_id2 == farmer_id:
				frappe.throw("Please enter differnet farmer id as it is linked with farmer <a href='#Form/Farmer/{0}'><b>{0}</b></a>".format(farmer_id))

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
