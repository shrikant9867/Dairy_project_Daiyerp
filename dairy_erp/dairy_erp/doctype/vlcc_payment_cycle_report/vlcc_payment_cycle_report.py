# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stellapps Technologies Private Ltd.
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from dairy_erp.dairy_utils import make_dairy_log
from frappe import _
from frappe.utils import flt, cstr,nowdate,cint
import json


class VLCCPaymentCycleReport(Document):
	def validate(self):
		# only one vpcr allowed against one vlcc per cycle
		if frappe.db.get_value("VLCC Payment Cycle Report",{'cycle':self.cycle,\
			 'vlcc_name':self.vlcc_name},'name') and self.is_new():
			frappe.throw(_("VPCR has already been generated for this cycle against vlcc <b>{0}</b>".format(self.vlcc_name)))
		if self.collection_to >= nowdate() :
			frappe.throw(_("You can generate VPCR after <b>'{0}'</b>".format(self.collection_to)))

	def before_submit(self):
		try:
			self.advance_operation()
			self.loan_operation()
			self.update_vpcr()
			if float(self.incentives) != 0:
				if not frappe.db.get_value("Purchase Invoice", {'cycle': self.cycle,\
					 'supplier': self.vlcc_name},'name'): 
					self.create_incentive()
					frappe.msgprint(_("Purchase invoice created successfully against Incentives"))
				else: frappe.msgprint(_("Purchase invoice Already created successfully against Incentives"))
		except Exception,e:
			frappe.db.rollback()
			make_dairy_log(title="JV creation Against Advance Failed",method="make_jv", status="Error",
				data = "data", message=e, traceback=frappe.get_traceback())		
			frappe.throw("Something Went Wrong Please check dairy log")
				
	def update_vpcr(self):
		loan_total, loan_je, adavnce_je, advance_total = 0, 0, 0, 0 
		for row in self.vlcc_loan_child:
			company = frappe.db.get_value("Company",{'is_dairy':1},'name',as_dict=1)
			je_amt = frappe.get_all("Journal Entry",fields=['ifnull(sum(total_debit), 0) as amt']\
			,filters={'vlcc_advance':row.loan_id,'type':'Vlcc Loan', 'company': self.vlcc_name})
			loan_je += je_amt[0].get('amt')
			loan_total += row.principle
		for row in self.vlcc_advance_child:
			company = frappe.db.get_value("Company",{'is_dairy':1},'name',as_dict=1)
			je_amt = frappe.get_all("Journal Entry",fields=['ifnull(sum(total_debit), 0) as amt']\
			,filters={'vlcc_advance':row.adv_id,'type':'Vlcc Advance', 'company': self.vlcc_name})
			adavnce_je += je_amt[0].get('amt')
			advance_total += row.principle
		self.advance_outstanding = float(advance_total) - float(adavnce_je)
		self.loan_outstanding = float(loan_total) - float(loan_je)
	
	def advance_operation(self):
		flag = False
		for row in self.vlcc_advance_child:
			flag = True
			company = frappe.db.get_value("Company",{'is_dairy':1},'name')
			dairy_je_exist = frappe.db.get_value("Journal Entry",{'cycle': self.cycle,\
						'vlcc_advance':row.adv_id,'type':'Vlcc Advance', 'company': company }, 'name')
			vlcc_je_exist = frappe.db.get_value("Journal Entry",{'cycle': self.cycle,\
						'vlcc_advance':row.adv_id,'type':'Vlcc Advance', 'company': self.vlcc_name }, 'name' )
			
			if not dairy_je_exist:
				self.validate_advance(row)
				dairy_je = self.create_dairy_advance_je(row)
				vlcc_je = self.create_vlcc_advance_je(row)
				self.update_advance_doc(row, dairy_je)
			elif dairy_je_exist:
				self.update_dairy_je_for_advance(row, self.cycle, dairy_je_exist)
				self.update_vlcc_je_for_advance(row, self.cycle, vlcc_je_exist)
				self.update_advance_after_vpcr(row)
		if flag:	
			frappe.msgprint(_("Journal Entries have been created successfully against Advances"))

	def loan_operation(self):
		flag = False
		for row in self.vlcc_loan_child:
			flag = True
			company = frappe.db.get_value("Company",{'is_dairy':1},'name')
			dairy_je_exist = frappe.db.get_value("Journal Entry",{'cycle': self.cycle,\
						'vlcc_advance':row.loan_id,'type':'Vlcc Loan', 'company': company }, 'name')
			vlcc_je_exist = frappe.db.get_value("Journal Entry",{'cycle': self.cycle,\
						'vlcc_advance':row.loan_id,'type':'Vlcc Loan', 'company': self.vlcc_name }, 'name' )
			if not dairy_je_exist:
				self.validate_loan(row)
				dairy_je = self.create_dairy_loan_je(row)
				vlcc_je = self.create_vlcc_loan_je(row)
				self.update_loan_je(row, dairy_je)
			elif dairy_je_exist:
				self.update_dairy_je_for_loan(row, self.cycle, dairy_je_exist)
				self.update_vlcc_je_for_loan(row, self.cycle, vlcc_je_exist)
				self.update_loan_vpcr_je(row)
		if flag:	
			frappe.msgprint(_("Journal Entries have been created successfully against Loans"))
	
	def validate_advance(self, row):
		adv_doc = frappe.get_doc("Vlcc Advance",row.adv_id)
		if not row.amount:
			frappe.throw(_("Please Enter amount against <b>{0}</b>".format(row.adv_id)))
		if float(row.amount) > float(row.outstanding):
			frappe.throw(_("Amount can not be greater than  outstanding for <b>{0}</b>".format(row.adv_id)))
		if (int(row.no_of_instalment) + int(adv_doc.extension)) - row.paid_instalment == 1 and \
			(float(row.amount) < float(adv_doc.emi_amount) or float(row.outstanding) != float(adv_doc.emi_amount)):
			frappe.throw(_("Please Use Extension for <b>{0}</b>".format(row.adv_id)))

	def validate_loan(self, row):
		loan_doc = frappe.get_doc("Vlcc Loan",row.loan_id)
		if not row.amount:
			frappe.throw(_("Please Enter amount against <b>{0}</b>".format(row.loan_id)))
		if float(row.amount) > float(row.outstanding):
			frappe.throw(_("Amount can not be greater than  outstanding for <b>{0}</b>".format(row.loan_id)))
		if (int(row.no_of_instalment) + int(loan_doc.extension)) - loan_doc.paid_instalment == 1 and \
			(float(row.amount) < float(loan_doc.emi_amount) or float(row.outstanding) != float(loan_doc.emi_amount)):
			frappe.throw(_("Please Use Extension <b>{0}</b>".format(row.loan_id)))

	def create_si(self, row, type_, item, doc_id):
		company = frappe.db.get_value("Company",{'is_dairy':1},'name')
		si_doc = frappe.new_doc("Sales Invoice")
		si_doc.type = type_
		si_doc.posting_date = self.collection_to
		si_doc.customer = self.vlcc_name
		si_doc.company = company
		si_doc.vlcc_advance_loan = doc_id
		si_doc.cycle_ = self.cycle
		si_doc.append("items",{
			"item_code": item,
			"qty": 1,
			"rate": row.amount,
			"cost_center": frappe.db.get_value("Company", company, "cost_center")
			})
		si_doc.flags.ignore_permissions = True
		si_doc.save()
		si_doc.submit()
		frappe.db.set_value("Sales Invoice", si_doc.name, 'posting_date', self.collection_to)
		gl_stock = frappe.db.get_value("Company", company, 'default_income_account')
		gl_credit = frappe.db.get_value("Company", company, 'default_receivable_account')
		frappe.db.set_value("GL Entry", {"account": gl_stock, "voucher_no": si_doc.name},\
					'posting_date', self.collection_to )
		frappe.db.set_value("GL Entry", {"account": gl_credit, "voucher_no": si_doc.name},\
					'posting_date', self.collection_to )	
		return si_doc.name

	def create_dairy_advance_je(self, row):
		company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.voucher_type = "Journal Entry"
		je_doc.company = company.get('name')
		je_doc.type = "Vlcc Advance"
		je_doc.cycle = self.cycle
		je_doc.reference_party = self.vlcc_name
		je_doc.vlcc_advance = row.adv_id
		je_doc.reference_party = self.vlcc_name
		je_doc.posting_date = nowdate()
		je_doc.append('accounts', {
			'account': "Debtors - "+ company.get('abbr'),
			'debit_in_account_currency': row.amount,
			'party_type': "Customer",
			'party': self.vlcc_name,
			'cost_center': company.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Loans and Advances - "+ company.get('abbr'),
			'credit_in_account_currency':  row.amount,
			'cost_center': company.get('cost_center')
			})
		je_doc.flags.ignore_permissions = True
		je_doc.save()
		je_doc.submit()
		return je_doc.name

	def create_dairy_loan_je(self, row):
		company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
		principal_interest = get_interest_amount(row.amount, row.loan_id)
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.voucher_type = "Journal Entry"
		je_doc.company = company.get('name')
		je_doc.reference_party = self.vlcc_name
		je_doc.type = "Vlcc Loan"
		je_doc.cycle = self.cycle
		je_doc.farmer_advance = row.loan_id
		je_doc.reference_party = self.vlcc_name
		je_doc.posting_date = nowdate()
		je_doc.append('accounts', {
			'account': "Debtors - "+ company.get('abbr'),
			'party_type': "Customer",
			'party': self.vlcc_name,
			'debit_in_account_currency': principal_interest.get('principal') + principal_interest.get('interest'),
			'cost_center': company.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Loans and Advances - "+ company.get('abbr'),
			'credit_in_account_currency':  principal_interest.get('principal'),
			'cost_center': company.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Interest Income - "+ company.get('abbr'),
			'credit_in_account_currency':  principal_interest.get('interest'),
			'cost_center': company.get('cost_center')
			})
		je_doc.flags.ignore_permissions = True
		je_doc.save()
		je_doc.submit()

		frappe.db.set_value("Journal Entry", je_doc.name, 'posting_date', self.collection_to)
		gl_stock = frappe.db.get_value("Company", company, 'default_income_account')
		gl_credit = frappe.db.get_value("Company", company, 'default_receivable_account')
		frappe.db.set_value("GL Entry", {"account": "Debtors - "+ company.get('abbr'), "voucher_no": je_doc.name},\
					'posting_date', self.collection_to )
		frappe.db.set_value("GL Entry", {"account": "Loans and Advances - "+ company.get('abbr'), "voucher_no": je_doc.name},\
					'posting_date', self.collection_to )
		frappe.db.set_value("GL Entry", {"account": "Interest Income - "+ company.get('abbr'), "voucher_no": je_doc.name},\
					'posting_date', self.collection_to )	
		return je_doc.name

	def create_pi(self, row, type_, item, doc_id):
		company = frappe.db.get_value("Company",{'is_dairy':1},'name')
		pi = frappe.new_doc("Purchase Invoice")
		pi.supplier = company
		pi.company = self.vlcc_name
		pi.pi_type = type_
		pi.cycle = self.cycle
		pi.vlcc_advance_loan = doc_id
		pi.append("items",
			{
				"item_code":item,
				"qty": 1,
				"rate": row.amount,
				"cost_center": frappe.db.get_value("Company", company, "cost_center")
			})
		pi.flags.ignore_permissions = True
		pi.save()
		pi.submit()

	def create_vlcc_advance_je(self, row):
		company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
		vlcc_attr = frappe.db.get_value("Company", self.vlcc_name, ['abbr','cost_center'],as_dict=1)
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.voucher_type = "Journal Entry"
		je_doc.company = self.vlcc_name
		je_doc.type = "Vlcc Advance"
		je_doc.cycle = self.cycle
		je_doc.reference_party = company.get('name')
		je_doc.vlcc_advance = row.adv_id
		je_doc.posting_date = nowdate()
		je_doc.append('accounts', {
			'account': "Loans and Advances Payable - "+ vlcc_attr.get('abbr'),
			'debit_in_account_currency': row.amount,
			'cost_center': vlcc_attr.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Creditors - "+ vlcc_attr.get('abbr'),
			'credit_in_account_currency': row.amount,
			'party_type': "Supplier",
			'party': company.get('name'),
			'cost_center': vlcc_attr.get('cost_center')
			})
		je_doc.flags.ignore_permissions = True
		je_doc.save()
		je_doc.submit()

	def create_vlcc_loan_je(self, row):
		company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
		vlcc_attr = frappe.db.get_value("Company", self.vlcc_name, ['abbr','cost_center'],as_dict=1)
		principal_interest = get_interest_amount(row.amount, row.loan_id)
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.voucher_type = "Journal Entry"
		je_doc.company = self.vlcc_name
		je_doc.type = "Vlcc Loan"
		je_doc.reference_party = company.get('name')
		je_doc.cycle = self.cycle
		je_doc.vlcc_advance = row.loan_id
		je_doc.posting_date = nowdate()
		je_doc.append('accounts', {
			'account': "Loans and Advances Payable - "+ vlcc_attr.get('abbr'),
			'debit_in_account_currency': principal_interest.get('principal'),
			'cost_center': vlcc_attr.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Interest Expense - "+ vlcc_attr.get('abbr'),
			'debit_in_account_currency':  principal_interest.get('interest'),
			'cost_center': vlcc_attr.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Creditors - "+ vlcc_attr.get('abbr'),
			'credit_in_account_currency': principal_interest.get('principal') + principal_interest.get('interest'),
			'party_type': "Supplier",
			'party': company.get('name'),
			'cost_center': vlcc_attr.get('cost_center'),
			})
		je_doc.flags.ignore_permissions = True
		je_doc.save()
		je_doc.submit()

	def update_dairy_je_for_advance(self, row, cycle, je_no):
		company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
		accounts_row_debit = frappe.db.get_value("Journal Entry Account", \
			{'parent':je_no,'account':'Debtors - '+company.get('abbr')}, 'name')
		accounts_row_credit = frappe.db.get_value("Journal Entry Account", \
			{'parent':je_no,'account':'Loans and Advances - '+company.get('abbr')}, 'name')
		# Child update
		frappe.db.set_value("Journal Entry Account",{'name':accounts_row_debit, \
			'account':"Debtors - "+company.get('abbr')}, 'debit_in_account_currency', row.amount)
		frappe.db.set_value("Journal Entry Account",{'name':accounts_row_credit, \
			'account':'Loans and Advances - '+company.get('abbr')}, 'credit_in_account_currency', row.amount)		
		#total credit and debit update
		frappe.db.set_value("Journal Entry", je_no, 'total_credit', row.amount)
		frappe.db.set_value("Journal Entry", je_no, 'total_debit', row.amount)
		frappe.db.set_value("Journal Entry", je_no, 'posting_date', self.collection_to)
		self.update_gl_entry_dairy_advance(je_no, row.amount)

	def update_vlcc_je_for_advance(self, row, cycle, je_no):
		company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
		vlcc_attr = frappe.db.get_value("Company", self.vlcc_name, ['abbr','cost_center'],as_dict=1)
		accounts_row_debit = frappe.db.get_value("Journal Entry Account", {'parent':je_no,"account":\
			'Loans and Advances Payable - '+vlcc_attr.get('abbr')}, 'name')

		accounts_row_credit = frappe.db.get_value("Journal Entry Account", {'parent':je_no,"account":\
			'Creditors - '+vlcc_attr.get('abbr')}, 'name')

		frappe.db.set_value("Journal Entry Account",{'name':accounts_row_debit, 'account':"Loans and Advances Payable - "+vlcc_attr.get('abbr')}, 'debit_in_account_currency', row.amount)
		frappe.db.set_value("Journal Entry Account",{'name':accounts_row_credit, 'account':"Creditors - "+vlcc_attr.get('abbr')}, 'credit_in_account_currency', row.amount)
		
		frappe.db.set_value("Journal Entry", je_no, 'total_credit', row.amount)
		frappe.db.set_value("Journal Entry", je_no, 'total_debit', row.amount)
		frappe.db.set_value("Journal Entry", je_no, 'posting_date', self.collection_to)
		self.update_gl_entry_vlcc_advance(je_no, row.amount)

	def update_dairy_je_for_loan(self, row, cycle, je_no):
		principal_interest = get_interest_amount(row.amount, row.loan_id)
		company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
		accounts_credit = frappe.db.get_value("Journal Entry Account", {'parent':je_no,'account':"Debtors - "+company.get('abbr')}, 'name')
		accounts_debit_principal = frappe.db.get_value("Journal Entry Account", {'parent':je_no,'account':"Loans and Advances - "+company.get('abbr')}, 'name')
		accounts_debit_interest = frappe.db.get_value("Journal Entry Account", {'parent':je_no,'account':"Interest Income - "+company.get('abbr')}, 'name')

		frappe.db.set_value("Journal Entry Account",accounts_credit, 'debit_in_account_currency', flt(principal_interest.get('principal') + principal_interest.get('interest'),2))
		frappe.db.set_value("Journal Entry Account",accounts_debit_principal, 'credit_in_account_currency', flt(principal_interest.get('principal'),2))
		frappe.db.set_value("Journal Entry Account",accounts_debit_interest, 'credit_in_account_currency', flt(principal_interest.get('interest'),2))
		frappe.db.set_value("Journal Entry", je_no, 'total_credit', row.amount)
		frappe.db.set_value("Journal Entry", je_no, 'total_debit', row.amount)
		frappe.db.set_value("Journal Entry", je_no, 'posting_date', self.collection_to)
		self.update_gl_entry_dairy_loan(je_no, principal_interest)

	def update_vlcc_je_for_loan(self, row, cycle, je_no):
		principal_interest = get_interest_amount(row.amount, row.loan_id)
		vlcc_attr = frappe.db.get_value("Company", self.vlcc_name, ['abbr','cost_center'],as_dict=1)
		
		accounts_credit = frappe.db.get_value("Journal Entry Account", {'parent':je_no,'account':"Creditors - "+vlcc_attr.get('abbr')}, 'name')
		accounts_debit_principal = frappe.db.get_value("Journal Entry Account", {'parent':je_no,'account':"Loans and Advances Payable - "+vlcc_attr.get('abbr')}, 'name')
		accounts_debit_interest = frappe.db.get_value("Journal Entry Account", {'parent':je_no,'account':"Interest Expense - "+vlcc_attr.get('abbr')}, 'name')

		frappe.db.set_value("Journal Entry Account",accounts_debit_principal, 'debit_in_account_currency', principal_interest.get('principal'))
		frappe.db.set_value("Journal Entry Account",accounts_debit_interest, 'debit_in_account_currency', principal_interest.get('interest'))
		frappe.db.set_value("Journal Entry Account",accounts_credit, 'credit_in_account_currency', principal_interest.get('principal') + principal_interest.get('interest'))
		frappe.db.set_value("Journal Entry", je_no, 'total_credit', row.amount)
		frappe.db.set_value("Journal Entry", je_no, 'total_debit', row.amount)
		frappe.db.set_value("Journal Entry", je_no, 'posting_date', self.collection_to)
		self.update_gl_entry_vlcc_loan(je_no, principal_interest)

	def update_gl_entry_dairy_advance(self, je_no, amount):
		if je_no:
			company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr'],as_dict=1)
			gl_debit = frappe.db.get_value("GL Entry", {"account": 'Loans and Advances - '+company.get('abbr'), "voucher_no": je_no},"name")
			gl_credit = frappe.db.get_value("GL Entry", {"account": "Debtors - "+company.get('abbr'), "voucher_no": je_no},"name")
			#For Debitors
			frappe.db.set_value("GL Entry", gl_debit, "debit", 0)
			frappe.db.set_value("GL Entry", gl_debit, "credit", amount)
			frappe.db.set_value("GL Entry", gl_debit, "credit_in_account_currency", amount)
			frappe.db.set_value("GL Entry", gl_debit, "debit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_debit, "posting_date", self.collection_to)
			#For Creditor			
			frappe.db.set_value("GL Entry", gl_credit, "debit", amount)
			frappe.db.set_value("GL Entry", gl_credit, "credit", 0)
			frappe.db.set_value("GL Entry", gl_credit, "credit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_credit, "debit_in_account_currency", amount)
			frappe.db.set_value("GL Entry", gl_credit, "posting_date", self.collection_to)
			#For receive pay and net payoff reports

			
	def update_gl_entry_dairy_loan(self, je_no, principal_interest):
		if je_no and principal_interest:
			company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr'],as_dict=1)
			gl_debit_principal = frappe.db.get_value("GL Entry", {"account": "Debtors - "+company.get('abbr'), "voucher_no": je_no},"name")
			gl_credit = frappe.db.get_value("GL Entry", {"account": "Loans and Advances - "+company.get('abbr'), "voucher_no": je_no},"name")
			gl_debit_interest = frappe.db.get_value("GL Entry", {"account": "Interest Income - "+company.get('abbr'), "voucher_no": je_no},"name")
			
			total_amount = flt(principal_interest.get('principal')+principal_interest.get('interest'),2)
			print gl_debit_principal,gl_credit,gl_debit_interest,total_amount,principal_interest.get('principal'),principal_interest.get('interest'),je_no
			# sdfsdfdsfksfksdjfskdfjsdkf
			#For Debitors
			frappe.db.set_value("GL Entry", gl_debit_principal, "debit", total_amount)
			frappe.db.set_value("GL Entry", gl_debit_principal, "credit", 0)
			frappe.db.set_value("GL Entry", gl_debit_principal, "credit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_debit_principal, "debit_in_account_currency", total_amount)
			frappe.db.set_value("GL Entry", gl_debit_principal,"posting_date", self.collection_to)

			frappe.db.set_value("GL Entry", gl_credit, "credit", flt(principal_interest.get('principal'),2))
			frappe.db.set_value("GL Entry", gl_credit, "debit", 0)
			frappe.db.set_value("GL Entry", gl_credit, "credit_in_account_currency", flt(principal_interest.get('principal'),2))
			frappe.db.set_value("GL Entry", gl_credit, "debit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_credit,"posting_date", self.collection_to)

			frappe.db.set_value("GL Entry", gl_debit_interest, "credit", flt(principal_interest.get('interest'),2))
			frappe.db.set_value("GL Entry", gl_debit_interest, "debit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_debit_interest, "credit_in_account_currency", flt(principal_interest.get('interest'),2))
			frappe.db.set_value("GL Entry", gl_debit_interest, "debit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_debit_interest, "posting_date", self.collection_to)

	def update_gl_entry_vlcc_advance(self, je_no, amount):
		if je_no:
			vlcc_attr = frappe.db.get_value("Company", self.vlcc_name, 'abbr')
			gl_debit = frappe.db.get_value("GL Entry", {"account": 'Creditors - '+vlcc_attr, "voucher_no": je_no},"name")
			gl_credit = frappe.db.get_value("GL Entry", {"account": "Loans and Advances Payable - "+vlcc_attr, \
				"voucher_no": je_no},"name")
			print gl_debit,"vlcc******",gl_credit,je_no
			#For Debitors
			frappe.db.set_value("GL Entry",gl_debit,"debit", 0)
			frappe.db.set_value("GL Entry",gl_debit,"credit", amount)
			frappe.db.set_value("GL Entry",gl_debit,"credit_in_account_currency", amount)
			frappe.db.set_value("GL Entry",gl_debit,"debit_in_account_currency", 0)
			frappe.db.set_value("GL Entry",gl_debit,"posting_date", self.collection_to)
			#For Creditor			
			frappe.db.set_value("GL Entry",gl_credit,"debit", amount)
			frappe.db.set_value("GL Entry",gl_credit,"credit", 0)
			frappe.db.set_value("GL Entry",gl_credit,"credit_in_account_currency", 0)
			frappe.db.set_value("GL Entry",gl_credit,"debit_in_account_currency", amount)
			#For receive pay and net payoff reports
			frappe.db.set_value("GL Entry",gl_credit,"posting_date", self.collection_to)

	def update_gl_entry_vlcc_loan(self, je_no, principal_interest):
		if je_no and principal_interest:
			vlcc_attr = frappe.db.get_value("Company", self.vlcc_name, ['abbr','name'],as_dict=1)
			
			gl_debit_principal = frappe.db.get_value("GL Entry", {"account": "Loans and Advances Payable - "+vlcc_attr.get('abbr'), "voucher_no": je_no},"name")
			gl_credit = frappe.db.get_value("GL Entry", {"account": "Creditors - "+vlcc_attr.get('abbr'), "voucher_no": je_no},"name")
			gl_debit_interest = frappe.db.get_value("GL Entry", {"account":"Interest Expense - "+vlcc_attr.get('abbr'), "voucher_no": je_no},"name")
			total_amount = flt(principal_interest.get('principal')+principal_interest.get('interest'),2)

			print gl_debit_principal,gl_credit,gl_debit_interest,total_amount,principal_interest.get('principal'),principal_interest.get('interest')
			# sdfsdfdsfksfksdjfskdfjsdkf
			frappe.db.set_value("GL Entry", gl_debit_principal,"debit", flt(principal_interest.get('principal'),2))
			frappe.db.set_value("GL Entry", gl_debit_principal,"credit", 0)
			frappe.db.set_value("GL Entry", gl_debit_principal,"credit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_debit_principal,"debit_in_account_currency", flt(principal_interest.get('principal'),2))
			frappe.db.set_value("GL Entry", gl_debit_principal,"posting_date", self.collection_to)

			frappe.db.set_value("GL Entry", gl_credit,"debit", 0)
			frappe.db.set_value("GL Entry", gl_credit,"credit", total_amount)
			frappe.db.set_value("GL Entry", gl_credit,"credit_in_account_currency", total_amount)
			frappe.db.set_value("GL Entry", gl_credit,"debit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_credit,"posting_date", self.collection_to)

			frappe.db.set_value("GL Entry",gl_debit_interest,"debit", 0)
			frappe.db.set_value("GL Entry", gl_debit_interest,"credit", flt(principal_interest.get('interest'),2))
			frappe.db.set_value("GL Entry", gl_debit_interest,"credit_in_account_currency", flt(principal_interest.get('interest'),2))
			frappe.db.set_value("GL Entry", gl_debit_interest,"debit_in_account_currency", 0)
			frappe.db.set_value("GL Entry", gl_debit_interest,"posting_date", self.collection_to)		
	
	def update_advance_after_vpcr(self, row):
		instalment = 0
		je_amt = frappe.get_all("Journal Entry",fields=['ifnull(sum(total_debit), 0) as amt']\
			,filters={'vlcc_advance':row.adv_id, 'type': 'Vlcc Advance', 'company': self.vlcc_name})
		adv_doc = frappe.get_doc("Vlcc Advance", row.adv_id)
		adv_doc.outstanding_amount = float(adv_doc.advance_amount) - je_amt[0].get('amt')
		for i in adv_doc.cycle:
			instalment +=1
		adv_doc.paid_instalment = instalment
		if adv_doc.outstanding_amount > 0 :
			adv_doc.emi_amount = (float(adv_doc.outstanding_amount)) / (float(adv_doc.no_of_instalment) + float(adv_doc.extension) - float(adv_doc.paid_instalment))
		if adv_doc.outstanding_amount == 0:
			adv_doc.status = "Paid"
			adv_doc.emi_amount = 0
		adv_doc.flags.ignore_permissions =True
		adv_doc.save()

	def update_loan_vpcr_je(self, row):
		instalment = 0
		je_amt = frappe.get_all("Journal Entry",fields=['ifnull(sum(total_debit), 0) as amt']\
			,filters={'vlcc_advance':row.loan_id, 'type': 'Vlcc Loan', 'company': self.vlcc_name})
		
		loan_doc = frappe.get_doc("Vlcc Loan", row.loan_id)
		loan_doc.outstanding_amount = float(loan_doc.advance_amount) - je_amt[0].get('amt')
		for i in loan_doc.cycle:
			instalment += 1
		loan_doc.paid_instalment = instalment
		if loan_doc.outstanding_amount > 0:
			loan_doc.emi_amount = (float(loan_doc.outstanding_amount)) / (float(loan_doc.no_of_instalments) + float(loan_doc.extension) - float(loan_doc.paid_instalment))
		if loan_doc.outstanding_amount == 0:
			loan_doc.status = "Paid"
			loan_doc.emi_amount = 0
		loan_doc.flags.ignore_permissions = True
		loan_doc.save()

	def update_advance_doc(self, row, je=None):
		instalment = 0
		je_amt = frappe.get_all("Journal Entry",fields=['ifnull(sum(total_debit), 0) as amt']\
			,filters={'vlcc_advance':row.adv_id, 'type': 'Vlcc Advance', 'company': self.vlcc_name})
		adv_doc = frappe.get_doc("Vlcc Advance", row.adv_id)
		adv_doc.append("cycle", {"cycle": self.cycle, "sales_invoice": je})
		adv_doc.outstanding_amount = float(adv_doc.advance_amount) - je_amt[0].get('amt')
		for i in adv_doc.cycle:
			instalment +=1
		adv_doc.paid_instalment = instalment
		if adv_doc.outstanding_amount > 0 :
			print (float(adv_doc.no_of_instalment),"no_of_instalment",float(adv_doc.extension),"extension", float(adv_doc.paid_instalment)),"paid_instalment********************"
			adv_doc.emi_amount = (float(adv_doc.outstanding_amount)) / (float(adv_doc.no_of_instalment) + float(adv_doc.extension) - float(adv_doc.paid_instalment))
		if adv_doc.outstanding_amount == 0:
			adv_doc.status = "Paid"
			adv_doc.emi_amount = 0
		adv_doc.flags.ignore_permissions =True
		adv_doc.save()

	def update_loan_je(self, row, je = None):
		instalment = 0
		je_amt = frappe.get_all("Journal Entry",fields=['ifnull(sum(total_debit), 0) as amt']\
			,filters={'vlcc_advance':row.loan_id, 'type': 'Vlcc Loan', 'company': self.vlcc_name})
		
		loan_doc = frappe.get_doc("Vlcc Loan", row.loan_id)
		loan_doc.append("cycle", {"cycle": self.cycle, "sales_invoice": je})
		loan_doc.outstanding_amount = float(loan_doc.advance_amount) - je_amt[0].get('amt')
		for i in loan_doc.cycle:
			instalment += 1
		loan_doc.paid_instalment = instalment
		if loan_doc.outstanding_amount > 0:
			loan_doc.emi_amount = (float(loan_doc.outstanding_amount)) / (float(loan_doc.no_of_instalments) + float(loan_doc.extension) - float(loan_doc.paid_instalment))
		if loan_doc.outstanding_amount == 0:
			loan_doc.status = "Paid"
			loan_doc.emi_amount = 0
		loan_doc.flags.ignore_permissions = True
		loan_doc.save()

	def create_incentive(self):
		company = frappe.db.get_value("Company",{'is_dairy':1},'name')
		pi = frappe.new_doc("Purchase Invoice")
		pi.supplier = self.vlcc_name
		pi.company = company
		pi.pi_type = "Incentive"
		pi.cycle = self.cycle
		pi.append("items",
			{
				"qty":1,
				"item_code": "Milk Incentives",
				"rate": self.incentives,
				"amount": self.incentives,
				"cost_center": frappe.db.get_value("Company", self.vlcc_name, "cost_center")
			})
		pi.flags.ignore_permissions = True
		pi.save()
		pi.submit()
		
		#updating date for current cycle
		frappe.db.set_value("Purchase Invoice", pi.name, 'posting_date', self.collection_to)
		gl_stock = frappe.db.get_value("Company", company, 'stock_received_but_not_billed')
		gl_credit = frappe.db.get_value("Company", company, 'default_payable_account')
		frappe.db.set_value("GL Entry",{'account': gl_stock,'voucher_no':pi.name}, 'posting_date', self.collection_to)
		frappe.db.set_value("GL Entry",{'account': gl_credit,'voucher_no':pi.name}, 'posting_date', self.collection_to)

def get_interest_amount(amount, data):
	loan_doc = frappe.get_all("Vlcc Loan",fields=['interest','no_of_instalments','emi_amount'],filters={'name':data})
	interest_per_cycle = loan_doc[0].get('interest') / loan_doc[0].get('no_of_instalments')
	if amount <= interest_per_cycle:
		interest_per_cycle = flt(amount,2)
		principal_per_cycle = 0
	else:
		interest_per_cycle = flt(interest_per_cycle,2)
		principal_per_cycle = flt((amount - interest_per_cycle),2)

	return { 'interest': interest_per_cycle , 'principal': principal_per_cycle}

@frappe.whitelist()
def get_vmcr(start_date, end_date, vlcc, cycle=None):
	
	vmcr =  frappe.db.sql("""
			select rcvdtime,shift,milkquantity,fat,snf,rate,amount
		from 
			`tabVlcc Milk Collection Record`
		where 
			associated_vlcc = '{0}' and date(rcvdtime) between '{1}' and '{2}'
			""".format(vlcc, start_date, end_date),as_dict=1,debug=0)
	amount = 0
	qty = 0
	for i in vmcr:
		amount += i.get('amount')
		qty += i.get('milkquantity')
		
	amount = flt(amount,2)
	return {
		"vmcr":vmcr, 
		"incentive": get_incentives(amount, qty, vlcc) or 0, 
		"vlcc_child_loan": get_vlcc_loans_child(start_date, end_date, vlcc, cycle),
		"vlcc_child_advance": get_vlcc_advance_child(start_date, end_date, vlcc, cycle),
		"feed_and_fodder": get_mi_raised(start_date, end_date, vlcc)
	}

def get_incentives(amount, qty, vlcc=None):
	if vlcc and amount and qty:
		incentive = 0
		dairy_setting = frappe.get_doc("Dairy Setting")
		if  dairy_setting.enable_per_litre and dairy_setting.per_litre:
			incentive = (float(dairy_setting.per_litre) * float(qty))
		elif not dairy_setting.enable_per_litre and dairy_setting.vlcc_incentives:
			incentive = (float(dairy_setting.vlcc_incentives) * float(amount)) / 100
		return incentive


def get_vlcc_loans_child(start_date, end_date, vlcc, cycle=None):
	loans_ = frappe.db.sql("""
				select name,outstanding_amount,
				emi_amount,no_of_instalments,paid_instalment,advance_amount,
				emi_deduction_start_cycle,extension,date_of_disbursement,vlcc_id
			from 
				`tabVlcc Loan`
			where
				outstanding_amount != 0
				and vlcc_id = '{0}'
				and date_of_disbursement < now() and docstatus =1
				""".format(vlcc),as_dict=1,debug=0)
	loans = []
	for row in loans_:
		req_cycle = req_cycle_computation(row)
		if cycle in req_cycle_computation(row):
			loans.append(row)
	return loans


def get_vlcc_advance_child(start_date, end_date, vlcc, cycle=None):
	advance_ = frappe.db.sql("""
				select name,outstanding_amount,emi_amount,advance_amount,
				no_of_instalment,paid_instalment,emi_deduction_start_cycle,
				extension,date_of_disbursement,vlcc
			from 
				`tabVlcc Advance`
			where
				outstanding_amount != 0
				and vlcc = '{0}'
				and date_of_disbursement < now() and docstatus =1
			""".format(vlcc),as_dict=1,debug=0)
	advance = []
	for row in advance_:
		if cycle in req_cycle_computation_advance(row):
			advance.append(row)
	return advance


def req_cycle_computation(data):
	if data.get('emi_deduction_start_cycle') > 0:

		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabCyclewise Date Computation`
			where
				'{0}' < start_date 
				or date('{0}') between start_date and end_date
				order by start_date limit {2}""".
			format(data.get('date_of_disbursement'),data.get('vlcc_id'),data.get('emi_deduction_start_cycle')),as_dict=1,debug=0)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		instalment = int(data.get('no_of_instalments')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select name
				from
					`tabCyclewise Date Computation`
				where
					'{date}' <= end_date and name not in ({cycle}) order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),vlcc = data.get('vlcc_id'),
					instalment = instalment),as_dict=1,debug=1)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list
	
	elif data.get('emi_deduction_start_cycle') == 0:
		instalment = int(data.get('no_of_instalments')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select
						name
					from
						`tabCyclewise Date Computation`
					where
					'{date}' <= end_date
						order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'),instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list
	return []


def req_cycle_computation_advance(data):
	
	if data.get('emi_deduction_start_cycle') > 0:
		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabCyclewise Date Computation`
			where
				'{0}' < start_date  
				or date('{0}') between start_date and end_date
				order by start_date limit {1}""".
			format(data.get('date_of_disbursement'),data.get('emi_deduction_start_cycle')),as_dict=1,debug=0)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		if len(not_req_cycl):
			req_cycle = frappe.db.sql("""
					select name
				from
					`tabCyclewise Date Computation`
				where
					'{date}' <= end_date and name not in ({cycle}) order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),
					instalment = instalment),as_dict=1)
			
			req_cycl_list = [i.get('name') for i in req_cycle]
			return req_cycl_list
	
	elif data.get('emi_deduction_start_cycle') == 0:
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select
						name
					from
						`tabCyclewise Date Computation`
					where
					'{date}' <= end_date
						order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'),instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list

	return []
	
def get_mi_raised(start_date, end_date, vlcc):
	grand_total = 0
	sales_invoice = frappe.db.sql("""
					select
						sum(grand_total)
					from
						`tabSales Invoice` si
					where
						si.customer = '{0}'
						and si.posting_date between '{1}' and '{2}'
						and si.type not in ('Vlcc Advance','Vlcc Loan')
						""".format(vlcc,start_date,end_date),as_list=1,debug=0)
	if sales_invoice:
		grand_total = sales_invoice[0][0]
	return grand_total

@frappe.whitelist()
def get_updated_loan(cycle, data, loan_id=None, amount=None, total = None, vlcc = None):
	data, total_paid, total_amount, overriding_amount = json.loads(data), 0, 0, 0
	for row in data.get('vlcc_loan_child'):
		total_amount += row.get('principle')
		overriding_amount += row.get('amount')
	return flt((total_amount - overriding_amount),2) or 0

@frappe.whitelist()
def get_updated_advance(cycle, data, adv_id=None, amount=None, total = None,vlcc = None):
	data, total_paid, total_amount, overriding_amount = json.loads(data), 0, 0, 0
	for row in data.get('vlcc_advance_child'):
		total_amount += row.get('principle')
		overriding_amount += row.get('amount')
	return flt((total_amount - overriding_amount),2) or 0


@frappe.whitelist()
def get_vpcr_flag():
	return frappe.get_doc("Dairy Setting").as_dict().get('is_vpcr')

@frappe.whitelist()
def get_cycle(doctype,text,searchfields,start,pagelen,filters):
	return frappe.db.sql("""
			select name 
		from
			`tabCyclewise Date Computation`
		where
			 end_date < now() and name like '{txt}'
		""".format(txt= "%%%s%%" % text,as_list=True))