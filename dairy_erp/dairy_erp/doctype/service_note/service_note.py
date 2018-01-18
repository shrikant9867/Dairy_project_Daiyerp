# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport
from frappe.utils import getdate, nowdate, flt, cint
from datetime import datetime, timedelta,date

class ServiceNote(Document):
	def validate(self):
		self.total_weight()

	def on_submit(self):
		self.sales_invoice_against_dairy()

	def sales_invoice_against_dairy(self):
		customer = frappe.db.get_value("Farmer",self.customer,"full_name")
		si_obj = frappe.new_doc("Sales Invoice")
		si_obj.customer = frappe.db.get_value("Farmer",self.customer,"full_name")
		si_obj.company = self.company
		si_obj_cost_center = frappe.db.get_value("Company",si_obj.company,'cost_center')
		for row in self.items:
			si_obj.append("items",
			{
				"item_code": row.get('item_code'),
				"item_name": row.get('item_code'),
				"description": row.get('item_code'),
				"uom": "Litre",
				"qty": row.get('qty'),
				"rate": row.get('rate'),
				"amount": row.get('amount'),
				"warehouse": row.get("warehouse"),
				"cost_center": si_obj_cost_center
			})
		si_obj.flags.ignore_permissions = True
		si_obj.service_note = self.name
		si_obj.submit()

	def total_weight(self):
		total = 0
		for i in self.items:
			total += i.get('amount')
		self.total = total
		self.base_total = total
		self.base_net_total = total
		self.net_total = total
		self.grand_total = total

@frappe.whitelist()
def get_effective_credit(customer):
	company = frappe.db.get_value("User", frappe.session.user, "company")
	purchase_total = frappe.db.sql("""select name,sum(grand_total) as purchase_total from `tabPurchase Invoice` where title = '{0}' and company = '{1}'""".format(customer,company),as_dict=True) 
	sales_total = frappe.db.sql("""select name,sum(grand_total) as sales_total from `tabSales Invoice` where title = '{0}' and company = '{1}'""".format(customer,company),as_dict=True)
	if purchase_total[0].get('purchase_total') and sales_total[0].get('sales_total'):
		eff_amt = purchase_total[0].get('purchase_total') - sales_total[0].get('sales_total')
		return eff_amt
	elif sales_total[0].get('sales_total'):
		eff_amt = 0.0
		return eff_amt
	else:
		eff_amt = 0.0
		return eff_amt
