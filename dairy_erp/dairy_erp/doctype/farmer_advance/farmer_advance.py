# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, today, getdate, nowdate
from dairy_erp.dairy_utils import make_journal_entry
from frappe.model.document import Document

class FarmerAdvance(Document):
	
	def on_submit(self):
		if flt(self.emi_amount) > flt(self.outstanding_amount):
			frappe.throw(_("EMI Amount can not be greater than Outstanding amount"))
		self.create_je()

	def validate(self):
		self.status = "Unpaid"
		self.outstanding_amount = self.advance_amount
		self.date_of_disbursement = today()
		if self.advance_amount <= 0:
			frappe.throw(_("Advance Amount cannot be zero"))

	def create_je(self):
		if self.advance_type == "Money Advance":
			je_doc = make_journal_entry(voucher_type = "Journal Entry",company = self.vlcc,posting_date = nowdate(),
				debit_account = "Loans and Advances - ",credit_account = "Cash - ", type = "Debit to Advance",
				amount = self.advance_amount, master_no = self.name,advance_type=self.advance_type)
		elif self.advance_type == "Feed And Fodder Advance":
			je_doc = make_journal_entry(voucher_type = "Journal Entry",company = self.vlcc,posting_date = nowdate(),
				debit_account = "Feed And Fodder Advance - ",credit_account = "Cash - ", type = "Debit to Advance",
				amount = self.advance_amount, master_no = self.name,advance_type=self.advance_type)

		frappe.msgprint(_("Farmer Advance <b>{0}</b> and Journal Entry <b>{1}</b> created successfully against Loans".format(
					'<a href="#Form/Farmer Advance/'+self.name+'">'+self.name+'</a>',
					'<a href="#Form/Journal Entry/'+je_doc.name+'">'+je_doc.name+'</a>'
				)))

def farmer_advance_permission(user):
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	roles = frappe.get_roles(user)
	
	if user != 'Administrator' and "Vlcc Manager" in roles:
		return """(`tabFarmer Advance`.vlcc = '{0}')""".format(user_doc.get('company'))
	
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
