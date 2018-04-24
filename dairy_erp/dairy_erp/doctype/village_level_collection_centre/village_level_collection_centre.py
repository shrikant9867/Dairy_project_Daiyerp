# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from dairy_erp.dairy_utils import make_dairy_log
import re
from frappe.model.document import Document

class VillageLevelCollectionCentre(Document):
	def validate(self):
		self.validate_vlcc_abbr()
		self.validate_vlcc_id()
		self.validate_email_user()
		self.validate_comp_exist()
		self.validate_global_eff_credit_percent()

	def validate_comp_exist(self):
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

	def validate_global_eff_credit_percent(self):
		# global eff-credit % must be between 0-99
		eff_credit_percent = flt(self.global_percent_effective_credit)
		if eff_credit_percent and (eff_credit_percent < 0 or eff_credit_percent > 99):
			frappe.throw(_("Global Percent Effective Credit must be between 0 to 99"))

	def after_insert(self):
		"""create company and w/h configure associated company"""
		try:
			company = self.create_company()
			self.create_warehouse()
			self.create_supplier()
			self.create_customer()
			self.create_user()
			self.create_missing_accounts(company)
			self.create_taxes_templates(company)
		except Exception as e:
			print frappe.get_traceback()

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
		return comp_doc.name

	def create_warehouse(self):

		wr_hs_doc = frappe.new_doc("Warehouse")
		wr_hs_doc.warehouse_name = self.vlcc_name
		wr_hs_doc.company = self.vlcc_name
		wr_hs_doc.flags.ignore_permissions = True
		wr_hs_doc.save()
		self.warehouse = wr_hs_doc.name
		self.save()

		rej_wr_doc = frappe.new_doc("Warehouse")
		rej_wr_doc.warehouse_name = self.vlcc_name + "-Rejected"
		rej_wr_doc.company = self.vlcc_name 
		rej_wr_doc.flags.ignore_permissions = True
		rej_wr_doc.save()
		self.rejected_warehouse =rej_wr_doc.name
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

		self.create_plant_customer()
		

	def create_plant_customer(self):
		if not frappe.db.exists('Customer', self.plant_office):
			custmer_doc_vlcc = frappe.new_doc("Customer")
			custmer_doc_vlcc.customer_name = self.plant_office
			custmer_doc_vlcc.customer_group = "Dairy"
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

	def create_missing_accounts(self, company):
		try:
			if company:
				duties_and_taxes_acc = frappe.db.sql("""
					select distinct account_name from `tabAccount` 
					where parent_account like 'Duties and Taxes - %'
					and vlcc is null or vlcc = ''
					""", as_dict=True)
				print "duties_and_taxes_acc", duties_and_taxes_acc
				vlcc_duties_acc = frappe.db.get_value("Account", {
					"company": company,
					"account_name": "Duties and Taxes"
				}, "name")
				if vlcc_duties_acc:
					for acc in duties_and_taxes_acc:
						if not frappe.db.get_value("Account", {
							"company": company,
							"account_name": acc.get('account_name')
						}, "name"):
							account = frappe.new_doc("Account")
							account.update({
								"company": company,
								"account_name": acc.get('account_name'),
								"parent_account": vlcc_duties_acc,
								"root_type": "Liability",
								"account_type": "Tax"
							})
							account.flags.ignore_permissions = True
							account.insert()
		except Exception as e:
			raise e

	def create_taxes_templates(self, company):
		try:
			for type_ in ["Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"]:
				tax_temp = frappe.get_all(type_, {"vlcc": ""})
				for temp in tax_temp:
					create_taxes_charges_template(type_, temp, company)
		except Exception as e:
			print frappe.get_traceback()


def create_taxes_charges_template(type_, temp, company):
	temp = frappe.get_doc(type_,temp.get('name'))
	if not frappe.db.get_value(type_, {
		"vlcc": company,
		"title": temp.title
		}, "name"):
		vlcc_temp = frappe.new_doc(type_)
		vlcc_temp.company = company
		vlcc_temp.title = temp.title
		vlcc_temp.vlcc = company
		for row in temp.taxes:
			acc_name = frappe.db.get_value("Account", row.get('account_head'), "account_name")
			vlcc_acc_head = frappe.db.get_value("Account", {
				"company": company,
				"account_name": acc_name
			}, "name")
			if vlcc_acc_head:
				vlcc_temp.append("taxes", {
					"charge_type": row.get("charge_type"),
					"account_head": vlcc_acc_head,
					"rate": row.get("rate"),
					"description": row.get('description')
				})
		vlcc_temp.flags.ignore_permissions = True
		vlcc_temp.flags.ignore_mandatory = True
		vlcc_temp.insert()