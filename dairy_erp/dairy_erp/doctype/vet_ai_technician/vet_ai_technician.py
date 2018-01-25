# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class VetAITechnician(Document):
	def validate(self):
		self.create_vet_ai_user()

	# def on_submit(self):
		

	def create_vet_ai_user(self):
		print "**************************",self
		
