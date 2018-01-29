# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport
from frappe.utils import getdate, nowdate, flt, cint
from datetime import datetime, timedelta,date
from frappe import _

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
		frappe.msgprint(_("Sales Invoice :'{0}' Created".format("<a href='#Form/Sales Invoice/{0}'>{0}</a>".format(si_obj.name))))

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
def get_farmer(farmer):
	farmer_name = frappe.db.get_value("Farmer", {"farmer_id":farmer}, "full_name")
	# print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",farmer_name
	return farmer_name

@frappe.whitelist()
def get_farmer_details(customer):
	address = frappe.db.get_value("Farmer", {"farmer_id":customer}, "address",debug=1)
	address_details = frappe.db.get_value("Farmer", {"farmer_id":customer}, "address_details",debug=1)
	# print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",farmer_name
	return {"address":address,"address_details":address_details}

@frappe.whitelist()
def get_vet_ai_company(user):
	company = frappe.db.get_value("Veterinary AI Technician", {"email":user}, "vlcc")
	first_name = frappe.db.get_value("Veterinary AI Technician", {"email":user}, "vet_or_ai_name")
	mobile_no = frappe.db.get_value("Veterinary AI Technician", {"email":user}, "contact")
	address = frappe.db.get_value("Veterinary AI Technician", {"email":user}, "address")
	address_details = frappe.db.get_value("Veterinary AI Technician", {"email":user}, "address_details")
	return {"company":company,"first_name":first_name,"mobile_no":mobile_no,"address":address,"address_details":address_details}

@frappe.whitelist()
def get_custom_item(doctype, txt, searchfield, start, page_len, filters):
	query_item = frappe.db.sql("""select item_code,item_group from `tabItem` where item_group in ('Cattle feed','Medicines', 'Artificial Insemination Services','Veterinary Services')""")
	return query_item

@frappe.whitelist()
def get_vlcc_warehouse():
	warehouse = frappe.db.get_value("Village Level Collection Centre", {"email_id": frappe.session.user}, 'warehouse')
	return warehouse

@frappe.whitelist()
def get_price_list_rate(item):
	if item:
		rate = frappe.db.sql("""select price_list_rate from `tabItem Price`
						 		where item_name = '{0}' and 
						 		price_list ='Standard Selling'""".format(item),as_list=1)
		if rate:
			return rate[0][0]
		else:
			return 0


# @frappe.whitelist()
# def get_effective_credit(customer):
# 	company = frappe.db.get_value("User", frappe.session.user, "company")
# 	purchase = frappe.db.get_value("Purchase Invoice", {"title":customer,"company":company}, "sum(grand_total)")
# 	sales = frappe.db.get_value("Sales Invoice", {"title":customer,"company":company}, "sum(grand_total)")
# 	print "----------------------sales",sales
# 	print "======================purchase",purchase
# 	purchase_total = frappe.db.sql("""select name,sum(grand_total) as purchase_total from `tabPurchase Invoice` where title = '{0}' and company = '{1}'""".format(customer,company),as_dict=True) 
# 	sales_total = frappe.db.sql("""select name,sum(grand_total) as sales_total from `tabSales Invoice` where title = '{0}' and company = '{1}'""".format(customer,company),as_dict=True)
# 	if purchase and sales:
# 		eff_amt = purchase - sales
# 		return eff_amt
# 	# elif None in purchase_total[0].get('purchase_total') and sales_total[0].get('sales_total'):
# 	# 	eff_amt = 0.0
# 	# 	return eff_amt
# 	# elif purchase_total[0].get('purchase_total') and None in sales_total[0].get('sales_total'):
# 	# 	eff_amt = purchase_total[0].get('purchase_total')
# 	# 	return eff_amt

# 	# elif any(x is None for x in purchase) and sales:
# 	# 	eff_amt = 0.0
# 	# 	return eff_amt
# 	# elif purchase and any(x is None for x in sales):
# 	# 	eff_amt = purchase
# 	# 	return eff_amt

# 	elif purchase == None and sales:
# 		eff_amt = 0.0
# 		return eff_amt
# 	elif purchase and sales == None:
# 		eff_amt = purchase
# 		return eff_amt
# 	else:
# 		eff_amt = 0.0
# 		return eff_amt