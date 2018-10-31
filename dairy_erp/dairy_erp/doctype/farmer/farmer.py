# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime
from frappe.utils import flt
from frappe.model.document import Document

class Farmer(Document):

	def after_insert(self):
		"""create customer & supplier for A/C head"""
		try:
			self.create_supplier()
			self.create_customer()
		except Exception as e:
			frappe.db.rollback()
			# frappe.msgprint(e)

	def on_update(self):
		pass
		# self.update_date = self.modified
	
	def create_supplier(self):
		if not frappe.db.exists("Supplier", self.full_name):
			supl_doc = frappe.new_doc("Supplier")
			supl_doc.supplier_name = self.full_name
			supl_doc.supplier_type = "Farmer"
			supl_doc.company = self.vlcc_name
			supl_doc.farmer = self.name
			supl_doc.append("accounts",
				{
				"company": self.vlcc_name,
				"account": frappe.db.get_value("Company",self.vlcc_name, "default_payable_account")
				})
			supl_doc.insert()
		else:
			frappe.throw("Supplier name already exist")

	def create_customer(self):
		if not frappe.db.exists("Customer", self.full_name):
			custmer_doc = frappe.new_doc("Customer")
			custmer_doc.customer_name = self.full_name
			custmer_doc.customer_group = "Farmer"
			custmer_doc.company = self.vlcc_name
			custmer_doc.farmer = self.name
			custmer_doc.append("accounts",
				{
				"company": self.vlcc_name,
				"account": frappe.db.get_value("Company",self.vlcc_name, "default_receivable_account")
				})
			custmer_doc.insert()
		else:
			frappe.throw("Customer name already exist")

	def validate(self):
		# validate existing supplier/customer
		farmer_exist = frappe.db.get_value("Farmer", {
			"full_name": self.full_name,
			"name": ["!=", self.name]
		}, "name")
		if farmer_exist:
			frappe.throw("Farmer name already exist")
		# self.registration_date = now_datetime()
		self.validate_eff_credit_percent()
		self.check_reserved_farmer()
		# if len(self.farmer_id) != 4:
		# 	frappe.throw(_("Only <b>4</b> Digits Farmer ID Allowed"))

	def validate_eff_credit_percent(self):
		# eff-credit % must be between 0-99
		eff_credit_percent = flt(self.percent_effective_credit)
		# if not self.ignore_effective_credit_percent and (eff_credit_percent < 0 or eff_credit_percent > 99):
		# 	frappe.throw(_("Percent Of Effective Credit must be between 0 to 99"))

	def check_reserved_farmer(self):
		user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
		vlcc_settings = frappe.db.get_value("VLCC Settings",
			{"vlcc":user_doc.get('company')},['farmer_id1','farmer_id2'],as_dict=1)
		if vlcc_settings:
			if self.farmer_id in [vlcc_settings.get('farmer_id1'),vlcc_settings.get('farmer_id2')]:
				frappe.throw("You can not create farmer id <b>{0}</b> as it is reserved farmer id".format(self.farmer_id))