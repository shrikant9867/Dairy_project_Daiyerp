# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FarmerSettings(Document):
	def validate(self):
		pass	
	
	def after_insert(self):
		self.create_vlcc_copy()

	def create_vlcc_copy(self):
		roles = frappe.get_roles()
		vlcc = frappe.get_all("Village Level Collection Centre")
		if len(vlcc):
			for row in vlcc:
				farmer_setting = frappe.db.get_value("Farmer Settings",{'vlcc':row.get('name')},'name')
				if not farmer_setting and "Dairy Manager" in roles:
					farmer_setting = frappe.new_doc("Farmer Settings")
					farmer_setting.vlcc = row.get('name')
					farmer_setting.farmer_incentives = self.farmer_incentives
					farmer_setting.per_litre = self.per_litre
					farmer_setting.flags.ignore_permissions = True
					farmer_setting.save()
				
				elif farmer_setting and "Dairy Manager" in roles:
					doc_obj = frappe.get_doc("Farmer Settings",farmer_setting)
					doc_obj.update(self.__dict__)
					doc_obj.flags.ignore_permissions = True
					doc_obj.save()
		
		if 'Dairy Manager' in roles:
			self.is_global = 1



def farmer_settings_permission(user):
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	roles = frappe.get_roles(user)
	
	if user != 'Administrator' and "Vlcc Manager" in roles:
		return """(`tabFarmer Settings`.vlcc = '{0}')""".format(user_doc.get('company'))
	
	if user != 'Administrator' and "Dairy Manager" in roles:
		return """(`tabFarmer Settings`.is_global = 1)"""