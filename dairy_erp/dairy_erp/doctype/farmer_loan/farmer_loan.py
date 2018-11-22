# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stellapps Technologies Private Ltd.
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, getdate, nowdate
from dairy_erp.dairy_utils import make_dairy_log, make_journal_entry


class FarmerLoan(Document):
	def on_submit(self):
		if self.emi_amount > self.outstanding_amount:
			frappe.throw(_("EMI Amount can not be greater than Outstanding amount"))
		self.create_je()

		
	def after_insert(self):
		self.per_cycle_interest = flt(flt(self.interest) / flt(self.no_of_instalments),2)

	def validate(self):
		self.status = "Unpaid"
		self.date_of_disbursement = today()
		self.outstanding_amount = self.advance_amount
		if self.advance_amount <= 0:
			frappe.throw(_("Principal Amount cannot be zero"))
	
	def on_update_after_submit(self):
		frappe.db.set_value("Farmer Loan", self.name, "last_extension_used", self.extension)

	def create_je(self):
		try:
			je_doc = make_journal_entry(voucher_type = "Journal Entry",company = self.vlcc, posting_date = nowdate(),
				debit_account = "Loans and Advances - ",credit_account = "Cash - ", type = "Debit to Loan",
				amount = self.advance_amount, master_no = self.name)
			if je_doc.name:
				frappe.msgprint(_("Journal Entry <b>{0}</b> created successfully against Loan".format(
					'<a href="#Form/Journal Entry/'+je_doc.name+'">'+je_doc.name+'</a>')))
		except Exception,e:
			frappe.db.rollback()
			make_dairy_log(title="JV creation Against Advance Failed",method="make_jv", status="Error",
			data = "data", message=e, traceback=frappe.get_traceback())

def farmer_loan_permission(user):
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	roles = frappe.get_roles(user)
	
	if user != 'Administrator' and "Vlcc Manager" in roles:
		return """(`tabFarmer Loan`.vlcc = '{0}')""".format(user_doc.get('company'))

def get_jv_amount(data):
	sum_ = frappe.db.sql("""
			select ifnull(sum(total_debit),0) as total
		from 
			`tabJournal Entry` 
		where 

		farmer_advance = %s and type = 'Farmer Loan' """,(data),as_dict=1)
	
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
			extension_interest = (flt(kwargs.get('extension')) - flt(kwargs.get('last_extension'))) * flt(kwargs.get('per_cyc_interest'))
			print flt(kwargs.get('principle')), flt(kwargs.get('interest')), flt(extension_interest)
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
			make_dairy_log(title="Extension attribute failed for farmer loan",method="calculate_interest", status="Error",
			data = kwargs, message=e, traceback=frappe.get_traceback())
			frappe.throw("Some thing went wrong please check dairy")