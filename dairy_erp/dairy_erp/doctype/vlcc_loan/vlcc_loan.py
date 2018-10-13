# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, today, getdate, nowdate
from dairy_erp.dairy_utils import make_dairy_log


class VlccLoan(Document):

	def on_submit(self):
		if self.emi_amount > self.outstanding_amount:
			#future configurability emi amt field is editable
			frappe.throw(_("EMI Amount can not be greater than Outstanding amount"))
		try:
			self.create_jv_at_dairy()
			self.create_jv_at_vlcc()
		except Exception,e:
			make_dairy_log(title="Sync failed for Data push",method="get_items", status="Error",
			data = "data", message=e, traceback=frappe.get_traceback())

	def validate(self):
		self.status = "Unpaid"
		self.date_of_disbursement = today()
		self.outstanding_amount = self.advance_amount
		if self.advance_amount <= 0:
			frappe.throw(_("Advance Amount cannot be zero"))

	def after_insert(self):
		self.per_cycle_interest = flt(flt(self.interest) / flt(self.no_of_instalments),2)

	def on_update_after_submit(self):
		frappe.db.set_value("Vlcc Loan", self.name, "last_extension_used", self.extension)		

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
			# 'party': self.vlcc_id,
			'cost_center': company.get('cost_center')
			})
		je_doc.append('accounts', {
			'account': "Cash - "+ company.get('abbr'),
			'credit_in_account_currency': self.advance_amount,
			'cost_center': company.get('cost_center')
			})
		je_doc.flags.ignore_permissions = True
		je_doc.save()
		je_doc.submit()

	def create_jv_at_vlcc(self):
		company = frappe.db.get_value("Company",self.vlcc_id,['name','abbr','cost_center'],as_dict=1)
		is_dairy = frappe.db.get_value("Company",{'is_dairy':1},'name')
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.voucher_type = "Journal Entry"
		je_doc.company = self.vlcc_id
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
			'account': "Loans and Advances - "+ company.get('abbr'),
			'credit_in_account_currency': self.advance_amount,
			'cost_center': company.get('cost_center')
			})
		je_doc.flags.ignore_permissions = True
		je_doc.save()
		je_doc.submit()

def get_jv_amount(data):
	sum_ = frappe.db.sql("""
			select ifnull(sum(total_debit),0) as total
		from 
			`tabJournal Entry` 
		where 
		vlcc_advance =%s and type = 'Vlcc Loan' """,(data),as_dict=1)
	
	if len(sum_):
		return sum_[0].get('total') if sum_[0].get('total') != None else 0
	else: return 0

@frappe.whitelist()
def get_emi(name = None, total = None, no_of_instalments = None, extension=None, paid_instalment = None):
	if name:
		outstanding_amount = (float(total) - float(get_jv_amount(name)))
		instalment = (float(no_of_instalments) + float(extension)) - float(paid_instalment)
		emi = outstanding_amount / instalment
		return emi if emi else 0

@frappe.whitelist()
def calculate_interest(**kwargs):
	try:
		if kwargs.get('name') and kwargs.get('extension') and kwargs.get('interest') and kwargs.get('no_of_instalments'):
			extension_interest = flt(flt(kwargs.get('extension')) * flt(kwargs.get('per_cyc_interest')),2)
			total_amount = flt(kwargs.get('principle')) + flt(kwargs.get('interest')) + flt(extension_interest)
			outstanding_amount = flt(flt(total_amount) - flt(get_jv_amount(kwargs.get('name'))),2)
			emi_amount = flt(flt(outstanding_amount ) / (flt(kwargs.get('no_of_instalments')) + flt(kwargs.get('extension'))),2)
			return {
					'emi': emi_amount or 0, 
					'outstanding':outstanding_amount, 
					'total':total_amount, 
					'extension_interest':extension_interest
				}
		else: return {}
 	except Exception,e:
			make_dairy_log(title="Extension attribute failed for vlcc loan",method="calculate_interest", status="Error",
			data = kwargs, message=e, traceback=frappe.get_traceback())
			frappe.throw("Some thing went wrong please check dairy")