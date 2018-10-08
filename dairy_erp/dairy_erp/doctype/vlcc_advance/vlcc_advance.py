# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, today, getdate, nowdate
from frappe import _
from frappe.model.document import Document

class VlccAdvance(Document):
	def on_submit(self):
		if flt(self.emi_amount) > flt(self.outstanding_amount):
			frappe.throw(_("EMI Amount can not be greater than Outstanding amount"))
		self.create_jv_at_dairy()
		self.create_jv_at_vlcc()

	def validate(self):
		self.status = "Unpaid"
		self.outstanding_amount = self.advance_amount
		self.date_of_disbursement = today()
		if self.advance_amount <= 0:
			frappe.throw(_("Advance Amount cannot be zero or negative"))
		if self.no_of_instalment == 0:
			frappe.throw(_("No of instalment can not be zero"))

	def create_jv_at_dairy(self):
		company = frappe.db.get_value("Company",{'is_dairy':1},['name','abbr','cost_center'],as_dict=1)
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.voucher_type = "Journal Entry"
		je_doc.company = company.get('name')
		je_doc.type = "Debit to Advance vlcc"
		je_doc.vlcc_advance =self.name
		je_doc.posting_date = nowdate()
		je_doc.append('accounts', {
			'account': "Loans and Advances - "+ company.get('abbr'),
			'debit_in_account_currency': self.advance_amount,
			# 'party_type': "Customer",
			# 'party': self.vlcc,
			'cost_center': company.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Cash - "+ company.get('abbr'),
			'credit_in_account_currency': self.advance_amount,
			# 'party_type': "Customer",
			# 'party': self.vlcc,
			'cost_center': company.get('cost_center')
			})
		je_doc.flags.ignore_permissions = True
		je_doc.save()
		je_doc.submit()


	def create_jv_at_vlcc(self):
		company = frappe.db.get_value("Company",self.vlcc,['name','abbr','cost_center'],as_dict=1)
		is_dairy = frappe.db.get_value("Company",{'is_dairy':1},'name')
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.voucher_type = "Journal Entry"
		je_doc.company = self.vlcc
		je_doc.vlcc_advance =self.name
		je_doc.posting_date = nowdate()
		je_doc.append('accounts', {
			'account': "Cash - "+ company.get('abbr'),
			'debit_in_account_currency': self.advance_amount,
			# 'party_type': "Supplier",
			# 'party': is_dairy,
			'cost_center': company.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Loans and Advances Payable - "+ company.get('abbr'),
			'credit_in_account_currency': self.advance_amount,
			'cost_center': company.get('cost_center'),
			# 'party_type': "Supplier",
			# 'party': is_dairy
			})
		je_doc.flags.ignore_permissions = True
		je_doc.save()
		je_doc.submit()



@frappe.whitelist()
def get_emi(name = None, total = None, no_of_instalments = None,extension = None, paid_instalment=None):
	if name:
		outstanding_amount = (float(total) - float(get_si_amount(name)))
		instalment = (float(no_of_instalments) + float(extension)) - float(paid_instalment)
		emi = outstanding_amount / instalment
		return emi if emi else 0 

def get_si_amount(data):
	sum_ = frappe.db.sql("""
			select ifnull(sum(grand_total),0) as total
		from 
			`tabSales Invoice` 
		where 
		farmer_advance =%s and total is not null""",(data),as_dict=1)
	
	if len(sum_):
		return sum_[0].get('total') if sum_[0].get('total') != None else 0
	else: return 0