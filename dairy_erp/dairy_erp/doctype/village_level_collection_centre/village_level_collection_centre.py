# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from dairy_erp.dairy_utils import make_dairy_log
import re
from frappe.model.document import Document

class VillageLevelCollectionCentre(Document):
	def validate(self):
		self.validate_vlcc_abbr()
		self.validate_vlcc_id()
		self.validate_email_user()
		self.validate_comp_exist()

	def validate_comp_exist(self):
		print  self.name == frappe.db.get_value("Company",{"is_dairy":1},'name')
		if self.name == frappe.db.get_value("Company",{"is_dairy":1},'name'):
			frappe.throw(_("Company Exist already"))
	
	def validate_email_user(self):
		if self.is_new() and frappe.db.sql("select email_id from `tabVillage Level Collection Centre` where email_id =%s",(self.email_id)):
			frappe.throw(_('User Exist already'))
		
		if re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email_id) == None:
			frappe.throw(_('Please enter valid Email Id'))

	def validate_vlcc_abbr(self):
		if frappe.db.sql("select abbr from `tabVillage Level Collection Centre`  where name!=%s and abbr=%s", (self.name, self.abbr)):
			frappe.throw(_("Abbreviation already used for another vlcc,please use another"))

	def validate_vlcc_id(self):
		if self.is_new():		
			if frappe.db.sql("select amcu_id from `tabVillage Level Collection Centre` where amcu_id = %s",(self.amcu_id)):
				frappe.throw(_("Amcu id exist already"))

	def after_insert(self):
		"""create company and w/h configure associated company"""
	
		self.create_company()
		self.create_warehouse()
		self.create_supplier()
		self.create_customer()
		self.create_user()
		self.create_camp_permission()
		
		
	def on_update(self):
		self.create_supplier()
		self.create_customer()

	def create_company(self):
		comp_doc = frappe.new_doc("Company")
		comp_doc.company_name = self.vlcc_name
		comp_doc.abbr = self.abbr
		comp_doc.default_currency = "INR"
		comp_doc.flags.ignore_permissions = True
		comp_doc.save() 

	def create_warehouse(self):
		wr_hs_doc = frappe.new_doc("Warehouse")
		wr_hs_doc.warehouse_name = self.vlcc_name
		wr_hs_doc.company = self.vlcc_name
		wr_hs_doc.flags.ignore_permissions = True
		wr_hs_doc.save()
		self.warehouse = wr_hs_doc.name
		self.save()

	def create_supplier(self):
		"""Supplier specific to company for inter-company transaction(stock and accounts)
		   Reconfigurable camp/plant-check for supplier existence and A/C head	
		"""
		if not frappe.db.exists('Supplier', self.vlcc_name):
			comp = frappe.get_doc("Address", self.chilling_centre)
			supl_doc = frappe.new_doc("Supplier")
			supl_doc.supplier_name = self.vlcc_name
			supl_doc.camp_office = self.camp_office
			supl_doc.supplier_type = "Vlcc Type"
			if comp.links:
				# supl_doc.company = comp.links[0].link_name 
				supl_doc.append("accounts",
					{
					"company": comp.links[0].link_name,
					"account": frappe.db.get_value("Company",comp.links[0].link_name, "default_payable_account")
					}) 
			supl_doc.flags.ignore_permissions = True
			supl_doc.save()

		if not frappe.db.exists('Supplier', self.camp_office):
			suppl_doc_vlcc = frappe.new_doc("Supplier")
			suppl_doc_vlcc.supplier_name = self.camp_office
			suppl_doc_vlcc.supplier_type = "Dairy Type"
			# suppl_doc_vlcc.company = self.vlcc_name
			suppl_doc_vlcc.append("accounts",
				{
					"company": self.vlcc_name,
					"account": frappe.db.get_value("Company", self.vlcc_name, "default_payable_account")
				})
			suppl_doc_vlcc.flags.ignore_permissions = True
			suppl_doc_vlcc.save()
		else:
			flag = True
			suppl_doc_exist = frappe.get_doc("Supplier", self.camp_office)
			for row in suppl_doc_exist.accounts:
				if row.get('company') == self.vlcc_name:
					flag = False
			if flag:
				suppl_doc_exist.append("accounts",{
						"company": self.vlcc_name,
						"account": frappe.db.get_value("Company", self.vlcc_name, "default_payable_account")
					})
				suppl_doc_exist.flags.ignore_permissions = True		
				suppl_doc_exist.save()	




	def create_customer(self):
		"""Vlcc customer for ==>Dairy& vice versa. Reconfigurable customer and A/C head
		   for Plant offices.plant offices > customer ==> for Dairy and vice versa.
		"""
		
		if not frappe.db.exists('Customer', self.vlcc_name):
			comp = frappe.get_doc("Address", self.chilling_centre)
			custmer_doc = frappe.new_doc("Customer")
			custmer_doc.customer_name = self.vlcc_name
			custmer_doc.camp_office = self.camp_office
			custmer_doc.customer_group = "Vlcc"
			if comp.links:
				custmer_doc.company = comp.links[0].link_name
				custmer_doc.append("accounts",
				{
					"company": comp.links[0].link_name,
					"account": frappe.db.get_value("Company",comp.links[0].link_name, "default_receivable_account")
				})
			custmer_doc.flags.ignore_permissions = True		
			custmer_doc.save()
		
		if not frappe.db.exists('Customer', self.plant_office):
			custmer_doc_vlcc = frappe.new_doc("Customer")
			custmer_doc_vlcc.customer_name = self.plant_office
			custmer_doc.customer_group = "Dairy"
			custmer_doc_vlcc.company = self.vlcc_name
			custmer_doc_vlcc.append("accounts",{
					"company": self.vlcc_name,
					"account": frappe.db.get_value("Company", self.vlcc_name, "default_receivable_account")
				})
			custmer_doc_vlcc.flags.ignore_permissions = True		
			custmer_doc_vlcc.save()
		else:
			flag = True
			custmer_doc_exist = frappe.get_doc("Customer",self.plant_office)
			for row in custmer_doc_exist.accounts:
				if row.get('company') == self.vlcc_name:
					flag = False
			if flag:
				custmer_doc_exist.append("accounts",{
						"company": self.vlcc_name,
						"account": frappe.db.get_value("Company", self.vlcc_name, "default_receivable_account")
					})
				custmer_doc_exist.flags.ignore_permissions = True		
				custmer_doc_exist.save()
		self.local_customer_vlcc()

	def create_user(self):
		from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to
		if not frappe.db.exists('User', self.email_id):
			operator = frappe.new_doc("User")
			operator.email = self.email_id
			operator.first_name = self.name1
			operator.operator_type = "VLCC"
			operator.new_password = "admin"
			operator.company = self.name
			operator.send_welcome_email = 0
			operator.flags.ignore_permissions = True
			operator.flags.ignore_mandatory = True
			operator.save()
			# add_all_roles_to(operator.name)
			operator.add_roles("Vlcc Manager")
			create_user_permission(operator.email,self.name)
			
		if self.operator_same_as_agent and not frappe.db.exists('User', self.operator_email_id):
			agent = frappe.new_doc("User")
			agent.email = self.operator_email_id
			agent.first_name = self.operator_name
			agent.operator_type = "VLCC"
			agent.new_password = "admin"
			agent.company = self.name
			agent.send_welcome_email = 0
			agent.flags.ignore_permissions = True
			agent.flags.ignore_mandatory = True
			agent.save()
			agent.add_roles("Vlcc Operator")
			# add_all_roles_to(agent.name)
			create_user_permission(agent.email,self.name)

	def create_camp_permission(self):
		
		camp_operator = frappe.db.get_value("Address",{"name":self.camp_office},"user")
		create_user_permission(camp_operator,self.name)

	def local_customer_vlcc(self):
		#local supplier specification for data analytics
		if not frappe.db.exists('Customer', self.vlcc_name+"-"+"Local"):
			custmer_doc_vlcc = frappe.new_doc("Customer")
			custmer_doc_vlcc.customer_name = self.vlcc_name+"-"+"Local"
			custmer_doc_vlcc.customer_group = "Vlcc Local Customer"
			custmer_doc_vlcc.company = self.vlcc_name
			custmer_doc_vlcc.append("accounts",{
					"company": self.vlcc_name,
					"account": frappe.db.get_value("Company", self.vlcc_name, "default_receivable_account")
				})
			custmer_doc_vlcc.flags.ignore_permissions = True		
			custmer_doc_vlcc.save()

def create_user_permission(user_email,name):
	perm_doc = frappe.new_doc("User Permission")
	perm_doc.user = user_email
	perm_doc.allow = "Company"
	perm_doc.for_value = name
	perm_doc.apply_for_all_roles = 0
	perm_doc.flags.ignore_permissions = True
	perm_doc.flags.ignore_mandatory = True
	perm_doc.save()

			
