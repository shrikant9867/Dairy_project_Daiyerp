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
		self.create_different_op()

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
			if self.longformatfarmerid or self.longformatsocietyid_e:
				self.check_longformatsocietyid(self.longformatfarmerid.split('_'))
				self.check_longformatsocietyid(self.longformatsocietyid_e.split('_'))

	def check_longformatsocietyid(self,longformat_id_len):
		if len(longformat_id_len) < 4:
			frappe.throw("The Long Format Society Id should be of Format OrgiD_CCID_RouteId_SocietyId")
		if len(longformat_id_len) == 4 and (not longformat_id_len[0] or not longformat_id_len[1] or not longformat_id_len[2] or not longformat_id_len[3]):
			frappe.throw("The Long Format Society Id should be of Format OrgiD_CCID_RouteId_SocietyId")
		if len(longformat_id_len) > 4:
			frappe.throw("The Long Format Society Id should be of Format OrgiD_CCID_RouteId_SocietyId")

	def validate_global_eff_credit_percent(self):
		# global eff-credit % must be between 0-99
		eff_credit_percent = flt(self.global_percent_effective_credit)
		pass
		# if eff_credit_percent and (eff_credit_percent < 0 or eff_credit_percent > 99):
		# 	frappe.throw(_("Global Percent Effective Credit must be between 0 to 99"))

	def after_insert(self):
		"""create company and w/h configure associated company"""
		try:
			company = self.create_company()
			self.create_warehouse()
			self.create_lossgain_warehouse()
			self.create_supplier()
			self.create_customer()
			self.create_user()
			self.create_missing_accounts(company)
			self.create_taxes_templates(company)
			self.add_vlcc_acc_in_dairy_supplier(company)

			#hybrid chilling centre is of own
			self.bmc_chilling_centre = self.name
			self.save()

			# message for address
			if self.is_auto_society_id == 0:
				frappe.msgprint("Please add address details for <b>{0}</b>".format(self.name))
		except Exception as e:
			frappe.db.rollback()
			make_dairy_log(title="Failed attribute for vlcc creation",method="vlcc_creation", status="Error",
			data = "data", message=e, traceback=frappe.get_traceback())
	
	def add_vlcc_acc_in_dairy_supplier(self, company):
		dairy_comp = frappe.db.get_value("Company",{'is_dairy':1},'name')
		if dairy_comp:
			suppl_doc = frappe.get_doc("Supplier",dairy_comp)
			suppl_doc.append("accounts", {
				"company": company,
				"account": frappe.db.get_value("Company", company, 'default_payable_account')
				}
			)
			suppl_doc.flags.ignore_permissions = True
			suppl_doc.save()
	
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

	def create_lossgain_warehouse(self):

		wh_name = self.wh_creation(warehouse="Handling Loss")
		self.handling_loss = wh_name

		wh_name = self.wh_creation(warehouse="Calibration Gain")
		self.calibration_gain = wh_name

		wh_name = self.wh_creation(warehouse="Edited Loss")
		self.edited_loss = wh_name

		wh_name = self.wh_creation(warehouse="Edited Gain")
		self.edited_gain = wh_name

		if self.vlcc_type == 'Hybrid':
			wh_name = self.wh_creation(warehouse="BMC Warehouse")
			self.bmc_warehouse = wh_name

		self.save()

	def wh_creation(self,warehouse):

		wr_hs_doc = frappe.new_doc("Warehouse")
		wr_hs_doc.warehouse_name = warehouse
		wr_hs_doc.company = self.vlcc_name
		wr_hs_doc.flags.ignore_permissions = True
		wr_hs_doc.save()
		return wr_hs_doc.name

	def create_supplier(self):
		"""Supplier specific to company for inter-company transaction(stock and accounts)
		   Reconfigurable camp/plant-check for supplier existence and A/C head	
		"""
		if not frappe.db.exists('Supplier', self.vlcc_name):
			comp = frappe.db.get_value("Company",{"is_dairy":1},
				['name','default_payable_account'],as_dict=1)#frappe.get_doc("Address", self.chilling_centre)
			supl_doc = frappe.new_doc("Supplier")
			supl_doc.supplier_name = self.vlcc_name
			supl_doc.camp_office = self.camp_office
			supl_doc.supplier_type = "Vlcc Type"
			if comp.links:
				# supl_doc.company = comp.links[0].link_name 
				supl_doc.append("accounts",
					{
					"company": comp.get('name'), #comp.links[0].link_name,
					"account": comp.get('default_payable_account') #frappe.db.get_value("Company",comp.links[0].link_name, "default_payable_account")
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
			comp = frappe.db.get_value("Company",{"is_dairy":1},
				['name','default_receivable_account'],as_dict=1)#frappe.get_doc("Address", self.chilling_centre)
			custmer_doc = frappe.new_doc("Customer")
			custmer_doc.customer_name = self.vlcc_name
			custmer_doc.camp_office = self.camp_office
			custmer_doc.customer_group = "Vlcc"
			if comp:
				custmer_doc.company = comp.get('name')
				custmer_doc.append("accounts",
				{
					"company": comp.get('name'), #comp.links[0].link_name,
					"account": comp.get('default_receivable_account')#frappe.db.get_value("Company",comp.links[0].link_name, "default_receivable_account")
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

	def create_different_op(self):
		
		if self.operator_same_as_agent and not frappe.db.exists('User', self.operator_email_id) and not self.is_new():
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
		# local institution
		if not frappe.db.exists('Customer', self.vlcc_name+"-"+"Local Institution"):
			custmer_doc_vlcc = frappe.new_doc("Customer")
			custmer_doc_vlcc.customer_name = self.vlcc_name+"-"+"Local Institution"
			custmer_doc_vlcc.customer_group = "Vlcc Local Institution"
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
				abbr = frappe.db.get_value("Company",{"name":company},"abbr")
				duties_and_taxes_acc = frappe.db.sql("""
					select distinct account_name from `tabAccount` 
					where parent_account like 'Duties and Taxes - %'
					and vlcc is null or vlcc = ''
					""", as_dict=True)
				vlcc_duties_acc = frappe.db.get_value("Account", {
					"company": company,
					"account_name": "Duties and Taxes"
				}, "name")
				
				if not frappe.db.get_value("Account", {"company": company,"account_name": "Feed And Fodder Advance"}, "name"):
					account = frappe.new_doc("Account")
					account.update({
						"company": company,
						"account_name": "Feed And Fodder Advance",
						"parent_account": "Loans and Advances (Assets) - "+abbr,
						"root_type": "Asset",
						"account_type": ""
					})
					account.flags.ignore_permissions = True
					account.save()

				if not frappe.db.get_value("Account", {"company": company,"account_name": "Loans and Advances"}, "name"):
					account = frappe.new_doc("Account")
					account.update({
						"company": company,
						"account_name": "Loans and Advances",
						"parent_account": "Loans and Advances (Assets) - "+abbr,
						"root_type": "Asset",
						"account_type": ""
					})
					account.flags.ignore_permissions = True
					account.save()

				if not frappe.db.get_value("Account", {"company": company,"account_name": "Feed And Fodder Advances Temporary Account"}, "name"):
					account = frappe.new_doc("Account")
					account.update({
						"company": company,
						"account_name": "Feed And Fodder Advances Temporary Account",
						"parent_account": "Temporary Accounts - "+abbr,
						"root_type": "Asset",
						"account_type": ""
					})
					account.flags.ignore_permissions = True
					account.save()

				if not frappe.db.get_value("Account", {"company": company,"account_name": "Interest Income"}, "name"):
					account = frappe.new_doc("Account")
					account.update({
						"company": company,
						"account_name": "Interest Income",
						"parent_account": "Direct Income - "+abbr,
						"root_type": "Income",
						"account_type": ""
					})
					account.flags.ignore_permissions = True
					account.save()
				if not frappe.db.get_value("Account", {"company": company,"account_name": "Loans and Advances Payable"}, "name"):
					account = frappe.new_doc("Account")
					account.update({
						"company": company,
						"account_name": "Loans and Advances Payable",
						"parent_account": "Loans (Liabilities) - "+abbr,
						"root_type": "Income",
						"account_type": ""
					})
					account.flags.ignore_permissions = True
					account.save()
				if not frappe.db.get_value("Account", {"company": company,"account_name": "Interest Expense"}, "name"):
					account = frappe.new_doc("Account")
					account.update({
						"company": company,
						"account_name": "Interest Expense",
						"parent_account": "Indirect Expenses - "+abbr,
						"root_type": "Income",
						"account_type": ""
					})
					account.flags.ignore_permissions = True
					account.save()

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
							account.save()
		except Exception as e:
			raise e

	def create_taxes_templates(self, company):
		try:
			for type_ in ["Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"]:
				dairy_company = frappe.db.get_value("Company", {"is_dairy": 1}, "name")
				tax_temp = frappe.get_all(type_, {"vlcc": "", "company": dairy_company})
				for temp in tax_temp:
					create_taxes_charges_template(type_, temp, company)
		except Exception as e:
			print frappe.get_traceback()

def create_taxes_charges_template(type_, temp, company):
	temp = frappe.get_doc(type_,temp.get('name'))
	cost_center = frappe.db.get_value("Cost Center", {
		"cost_center_name": "Main",
		"company": company
	}, "name")
	if not frappe.db.get_value(type_, {
		"vlcc": company,
		"title": temp.title
		}, "name"):
		vlcc_temp = frappe.new_doc(type_)
		vlcc_temp.company = company
		vlcc_temp.title = temp.title
		vlcc_temp.vlcc = company
		taxes_added = False
		for row in temp.taxes:
			acc_name, parent_acc = frappe.db.get_value("Account", row.get('account_head'), ["account_name", "parent_account"])
			vlcc_acc_head = frappe.db.get_value("Account", {
				"company": company,
				"account_name": acc_name
			}, "name")
			# create missing account if parent account found
			if not vlcc_acc_head:
				if parent_acc:
					parent_acc = frappe.db.sql("""select name from `tabAccount` 
						where account_name like '{0}%' and company = '{1}'
					""".format(parent_acc.split(" -")[0], company))
					if parent_acc:
						vlcc_acc_head = create_account_head(acc_name, parent_acc[0][0], company)
			# if account head add taxes row
			if vlcc_acc_head:
				taxes_added = True
				vlcc_temp.append("taxes", {
					"charge_type": row.get("charge_type"),
					"account_head": vlcc_acc_head,
					"cost_center": cost_center or "",
					"rate": row.get("rate"),
					"tax_amount": row.get("tax_amount"),
					"description": row.get("description")
				})
		# if taxes rows
		if taxes_added:
			vlcc_temp.flags.ignore_permissions = True
			vlcc_temp.flags.ignore_mandatory = True
			vlcc_temp.flags.auto_created = True
			vlcc_temp.save()

def create_account_head(acc_name, parent_acc, company):
	if not acc_name or not parent_acc:
		return
	acc = frappe.new_doc("Account")
	acc.update({
		"company": company,
		"account_name": acc_name,
		"parent_account": parent_acc,
		"vlcc": company
	})
	acc.flags.ignore_permissions = True
	acc.save()
	return acc.name