# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, getdate


class FarmerLoan(Document):
	def on_submit(self):
		if self.emi_amount > self.outstanding_amount:
			frappe.throw(_("EMI Amount can not be greater than Outstanding amount"))

	def validate(self):
		self.status = "Unpaid"
		self.date_of_disbursement = today()
		self.outstanding_amount = self.advance_amount
		if self.advance_amount <= 0:
			frappe.throw(_("Advance Amount cannot be zero"))
		

	def on_update_after_submit(self):
		pass

def farmer_loan_permission(user):
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	roles = frappe.get_roles(user)
	
	if user != 'Administrator' and "Vlcc Manager" in roles:
		return """(`tabFarmer Loan`.vlcc = '{0}')""".format(user_doc.get('company'))

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

@frappe.whitelist()
def get_emi(name = None, total = None, no_of_instalments = None):
	if name:
		emi = (float(total) - float(get_si_amount(name))) / float(no_of_instalments)
		return emi if emi else 0 