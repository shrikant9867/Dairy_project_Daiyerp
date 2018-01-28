# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import re
from frappe.model.document import Document

class VeterinaryAITechnician(Document):
	def validate(self):
		self.validate_email_user()

	def after_insert(self):
		self.create_vet_ai_user()

	def validate_email_user(self):
		if self.is_new() and frappe.db.sql("select email from `tabUser` where email =%s",(self.email)):
			frappe.throw(_('User Exist already'))
		
		if re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email) == None:
			frappe.throw(_('Email not valid'))

	def create_vet_ai_user(self):
		if not frappe.db.exists('User', self.email):
			ai_tech_obj = frappe.new_doc("User")
			ai_tech_obj.email = self.email
			ai_tech_obj.first_name = self.vet_or_ai_name
			ai_tech_obj.mobile_no = self.contact
			ai_tech_obj.company = self.vlcc
			ai_tech_obj.operator_type = "Vet AI Technician"
			ai_tech_obj.send_welcome_email = 0
			ai_tech_obj.new_password = "admin"
			ai_tech_obj.flags.ignore_permissions = True
			ai_tech_obj.flags.ignore_mandatory = True
			ai_tech_obj.save()
			ai_tech_obj.add_roles("Vet/AI Technician")
			frappe.msgprint(_("User Created!!!",self.vet_or_ai_name))
		else:
			frappe.msgprint(_("User not Created!!!"))