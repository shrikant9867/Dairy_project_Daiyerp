# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stellapps Technologies and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.stock_balance import get_balance_qty_from_sle
from dairy_erp.customization.stock_balance.stock_balance_report import get_actual_qty_from_bin
from dairy_erp.dairy_erp.report.farmer_net_payoff.farmer_net_payoff import get_data
from frappe.utils import flt, now_datetime, cstr,has_common,nowdate

@frappe.whitelist()
def get_local_customer(company):
	data = fetch_balance_qty()
	data.update({'customer':frappe.db.get_value("Customer",company+"-"+"Local",'name')})
	return data

@frappe.whitelist()
def get_local_institution(company):
	data = fetch_balance_qty()
	return data



@frappe.whitelist()
def get_farmer_config(farmer, invoice=None, company =None):
	# check local eff credit % else take global eff credit % defined on vlcc iff not ignored
	if farmer:
		data = fetch_balance_qty()
		doc = frappe.get_doc("Farmer",farmer)
		eff_credit = get_net_off(farmer,company)
		eff_percent = doc.percent_effective_credit if doc.percent_effective_credit and not doc.ignore_effective_credit_percent else 0
		if not eff_percent and not doc.ignore_effective_credit_percent:
			eff_percent = frappe.db.get_value("Village Level Collection Centre", doc.vlcc_name, "global_percent_effective_credit")
		print "$$$$$$$$$$$$$$$$$$$",eff_credit,eff_percent,(eff_credit * eff_percent/100)
		percent_eff_credit = (eff_credit * eff_percent/100) if eff_percent else eff_credit
		data.update({'eff_credit': eff_credit, "percent_eff_credit":flt(percent_eff_credit, 2),'customer': frappe.db.get_value("Farmer",farmer,'full_name')})
		return data


@frappe.whitelist()
def fetch_balance_qty():
	row_ =""
	items_dict = {}
	item = ["COW Milk","BUFFALO Milk"]
	company = frappe.db.get_value("User",frappe.session.user,"company")
	warehouse = frappe.db.get_value("Village Level Collection Centre",company,"warehouse")
	for row in item:
		if row == "COW Milk":
			row_ = "cow_milk"
		elif row == "BUFFALO Milk":
			row_ = "buff_milk"
		items_dict.update({row_ : get_actual_qty_from_bin(row,warehouse)})

	return items_dict

@frappe.whitelist()
def get_effective_credit(customer, invoice=None):
	# SIdhant code for effective credit
	company = frappe.db.get_value("User", frappe.session.user, "company")
	purchase = frappe.db.sql("""select sum(outstanding_amount) as pur_amnt from `tabPurchase Invoice` where company = '{0}' and supplier = '{1}' and status not in ('Paid') and docstatus = '1' and name <> '{2}'""".format(company, customer, invoice),as_dict=1)
	sales = frappe.db.sql("""select sum(outstanding_amount) as si_amnt from `tabSales Invoice` where company = '{0}' and customer = '{1}' and status not in ('Paid') and docstatus = '1' and name <> '{2}'""".format(company, customer, invoice),as_dict=1)
	if purchase[0].get('pur_amnt') == None:
		eff_amt = 0.0
		return round(eff_amt,2)

	if purchase[0].get('pur_amnt') and sales[0].get('si_amnt'):
		eff_amt = flt(purchase[0].get('pur_amnt')) - flt(sales[0].get('si_amnt'))
		return round(eff_amt,2)

	elif purchase[0].get('pur_amnt') == None and sales[0].get('si_amnt'):
		eff_amt = 0.0
		return round(eff_amt,2)
	
	elif purchase[0].get('pur_amnt') and sales[0].get('si_amnt') == None:
		eff_amt = flt(purchase[0].get('pur_amnt'))
		return round(eff_amt,2)
	
	else:
		eff_amt = 0.0
		return round(eff_amt,2)

@frappe.whitelist()
def validate_local_sale(doc, method):
	"""
	Fetch allow_negative_effective_credit from VLCC
	"""
	if doc.farmer and not doc.local_sale_type:
		frappe.throw("Please Select Local Sale Type Either <b>No Advance</b> or <b>Feed And Fooder Advance</b>")	
	
	if doc.local_sale:
		vlcc = frappe.get_doc("User",frappe.session.user).company
		allow_negative_effective_credit = frappe.get_doc("VLCC Settings",vlcc).get('allow_negative_effective_credit')
		# dairy_setting = frappe.db.get_singles_dict('Dairy Setting').get('allow_negative_effective_credit')
		doc.is_negative = allow_negative_effective_credit
		if doc.effective_credit <= 0.000 and doc.service_note and not doc.by_cash:
			frappe.throw(_("Cannot create Service Note, If <b>Effective Credit</b> is zero, use Multimode Payment option for cash "))
		elif (doc.grand_total > doc.effective_credit and doc.service_note and not doc.by_cash) \
		or (doc.service_note and doc.by_credit and doc.by_credit > doc.grand_total ):
			frappe.throw(_("Service note cannot be created if Outstanding amount is greater than Effective Credit "))

		if doc.customer_or_farmer == "Farmer":
			validate_price_list(doc)
			doc.customer = frappe.db.get_value('Farmer',doc.farmer,'full_name')
		# elif doc.customer_or_farmer == "Vlcc Local Customer":
		# 	doc.customer = frappe.db.get_value("Customer",doc.company+"-"+"Local",'name')
		elif doc.customer_or_farmer == "Vlcc Local Customer":
			doc.customer = frappe.db.get_value("Customer",doc.company+"-"+"Local",'name')
		warehouse = frappe.db.get_value('Village Level Collection Centre',doc.company,'warehouse')
		doc.debit_to = frappe.db.get_value("Company",doc.company, 'default_receivable_account')
		for row in doc.items:
			row.warehouse = warehouse
			row.cost_center = frappe.db.get_value('Company',doc.company,'cost_center')
		validate_warehouse_qty(doc)

def validate_warehouse_qty(doc):
	for item in doc.items:
		warehouse_qty = get_actual_qty_from_bin(item.item_code,item.warehouse)
		if item.item_code not in ['COW Milk','BUFFALO Milk']:
			if item.qty > warehouse_qty:
				frappe.throw(_("Warehouse <b>{0}</b> have insufficient stock for item <b>{1}</b> (Available Qty: <b>{2}</b>)".format(item.warehouse,item.item_code,warehouse_qty)))

@frappe.whitelist()
def payment_entry(doc, method):
	if doc.local_sale  or doc.service_note and doc.local_sale_type == "No Advance":
		input_ = get_farmer_config(doc.farmer,doc.name, doc.company).get('percent_eff_credit') if doc.farmer else 0
		if doc.local_sale and doc.customer_or_farmer == "Farmer":
		# if doc.local_sale and doc.customer_or_farmer == "Farmer" and doc.by_credit and doc.multimode_payment:
			input_ = input_ + doc.grand_total
		if doc.local_sale and doc.customer_or_farmer == "Farmer" and input_ == 0 and not doc.by_cash and not int(doc.is_negative):
			frappe.throw(_("Cannot create local sale, If <b>Effective Credit</b> is zero, use Multimode Payment option for cash "))
		elif doc.local_sale and doc.customer_or_farmer == "Farmer" and doc.by_credit > input_ and doc.by_credit and doc.multimode_payment and not int(doc.is_negative):
			frappe.throw(_("<b>By Credit - {0}</b> Amount must be less than OR equal to <b>Effective Credit</b>.{1}".format(doc.by_credit, input_)))
		elif (doc.local_sale or doc.service_note) and doc.customer_or_farmer == "Farmer" and not doc.multimode_payment and doc.grand_total > input_ and not int(doc.is_negative):
			frappe.throw(_("Outstanding amount should not be greater than Effective Credit"))
		elif (doc.local_sale or doc.service_note) and doc.customer_or_farmer == "Farmer" and doc.by_credit and doc.by_credit > input_ and not int(doc.is_negative):
			frappe.throw(_("By Credit Amount must be less than or equal to Effective Credit."))
		elif doc.local_sale and not doc.update_stock:
			frappe.throw(_("Please set <b>Update Stock</b> checked"))
		elif (doc.local_sale or doc.service_note) and has_common([doc.customer_or_farmer],["Vlcc Local Customer","Vlcc Local Institution"])\
		and (doc.by_cash or not doc.multimode_payment) and (not input_ or doc.by_cash):
			make_payment_entry(doc)
		elif (doc.local_sale or doc.service_note) and has_common([doc.customer_or_farmer],["Farmer"])\
		and (doc.by_cash or doc.multimode_payment):
			make_payment_entry(doc)
		print (doc.local_sale or doc.service_note),has_common([doc.customer_or_farmer],["Farmer", "Vlcc Local Customer","Vlcc Local Institution"]),(doc.by_cash or not doc.multimode_payment),(not doc.effective_credit or doc.by_cash),\
		doc.effective_credit,doc.effective_credit,doc.by_cash,"\n\n\n",input_

@frappe.whitelist()
def feed_fooder_advance(doc, method):
	roles = frappe.get_roles()
	user = frappe.db.get_value("User",frappe.session.user,'company')
	if ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
		if doc.local_sale and doc.local_sale_type == "Feed And Fooder Advance" and doc.farmer and doc.no_of_instalment:
			make_payment_entry(doc)
			farmer_advance = frappe.new_doc("Farmer Advance")
			farmer_advance.advance_type = "Feed And Fodder Advance"
			farmer_advance.farmer_id = doc.farmer
			farmer_advance.farmer_name = doc.customer
			farmer_advance.no_of_instalment = doc.no_of_instalment
			farmer_advance.advance_amount = doc.grand_total
			farmer_advance.emi_amount = flt(doc.grand_total/doc.no_of_instalment,2)
			farmer_advance.vlcc = user
			farmer_advance.emi_deduction_start_cycle = doc.emi_start_cycle
			farmer_advance.feed_and_fodder_si = '<a href="#Form/Sales Invoice/'+doc.name+'">'+doc.name+'</a>'
			farmer_advance.save(ignore_permissions=True)
			farmer_advance.submit()



@frappe.whitelist()
def make_payment_entry(si_doc):
	si_payment = frappe.new_doc("Payment Entry")
	si_payment.paid_to = frappe.db.get_value("Account",{"company":si_doc.company,"account_type":'Cash'},"name")
	si_payment.posting_date = si_doc.posting_date
	si_payment.company = si_doc.company
	si_payment.mode_of_payment = "Cash"
	si_payment.payment_type = "Receive"
	si_payment.party_type = "Customer"
	si_payment.party_name = si_doc.customer
	si_payment.party = si_doc.customer

	si_payment.append("references",
		{
			"reference_doctype": si_doc.doctype,
			"reference_name": si_doc.name,
			"allocated_amount": si_doc.by_cash or si_doc.grand_total,
			"due_date": si_doc.due_date
		})

	si_payment.paid_amount = si_payment.references[0].allocated_amount
	si_payment.received_amount = si_payment.paid_amount
	# si_payment.party_balance = si_doc.grand_total
	si_payment.outstanding_amount = 0
	si_payment.flags.ignore_permissions = True
	si_payment.flags.ignore_credit_validation = True
	si_payment.flags.ignore_mandatory = True
	si_payment.submit()
	frappe.msgprint(_("Payment Entry : {0} Created!!!".format("<a href='#Form/Payment Entry/{0}'>{0}</a>".format(si_payment.name))))


@frappe.whitelist()
def get_wrhous():
	warehouse = frappe.db.get_value("Village Level Collection Centre", {"email_id": frappe.session.user}, 'warehouse')
	return warehouse


@frappe.whitelist()
def get_service_note_item(doctype, txt, searchfield, start, page_len, filters):
	if filters.service_note:
		query_item = frappe.db.sql(""" select item_code from `tabItem` where item_group in ('Medicines', 'Services')""")
		return query_item
	else:
		query_item = frappe.db.sql("""select item_code from `tabItem`""")
		return query_item

@frappe.whitelist()
def get_servicenote_item():
	query_item = frappe.db.sql(""" select item_code from `tabItem` where item_group in ('Medicines', 'Services')""",as_list=1)
	return query_item

@frappe.whitelist()
def get_account_invoice(for_cc=None):
	user = frappe.session.user
	user_data = frappe.db.get_value("User", user, ["operator_type", "branch_office"], as_dict=True)
	if (user_data.get('operator_type') == "Camp Office" and user_data.get('branch_office')) \
		or (user_data.get('operator_type') == "Chilling Centre" and user_data.get('branch_office') and for_cc):
		camp_office_data = frappe.db.get_value("Address", user_data.get('branch_office'),
			["income_account", "expense_account", "stock_account", "warehouse"], as_dict=True)
		return camp_office_data
	return {}

def set_camp_office_accounts(doc, method=None):
	# set income/expense account in item grid & also as remarks to filter it as account in reports.
	# fix - for chilling centre accounts
	for_cc = False
	if doc.flags.for_cc:
		for_cc = True
	accounts = get_account_invoice(for_cc=for_cc)
	if accounts:
		for i in doc.items:
			if doc.doctype == "Purchase Invoice" and accounts.get('expense_account'):
				i.expense_account = accounts.get('expense_account')
			elif doc.doctype == "Sales Invoice" and accounts.get('income_account'):
				i.income_account = accounts.get('income_account')
				i.warehouse = accounts.get('warehouse')
		account = accounts.get('expense_account') if doc.doctype == "Purchase Invoice" else accounts.get('income_account')
		if account and doc.remarks.find("[#"+account+"#]") == -1:
			doc.remarks = doc.remarks + " [#"+account+"#]"

	set_missing_po_accounts(doc)
	set_missing_cost_centers(doc)

def set_missing_po_accounts(doc):
	if doc.doctype == "Purchase Invoice" and doc.remarks:
		remark_split = doc.remarks.split('#')
		expense_account = remark_split[1] if len(remark_split) == 3 else ""
		if expense_account and frappe.db.exists("Account", expense_account):
			for i in doc.items:
				if expense_account != i.expense_account:
					i.expense_account = expense_account

def set_missing_cost_centers(doc):
	# validate taxes_and_charges template & set cost center
	if doc.company and doc.taxes_and_charges:
		for tax in doc.taxes:
			cost_center = frappe.db.get_value("Cost Center", {
				"company": doc.company,
				"cost_center_name": "Main"
			}, "name")
			if(cost_center and not tax.cost_center) or (cost_center and cost_center != tax.cost_center):
				tax.cost_center = cost_center


def get_taxes_and_charges_template(doc, template):
	if doc.company and template:
		tax_temp_map = {
			"Purchase Invoice":"Purchase Taxes and Charges Template",
			"Purchase Receipt": "Purchase Taxes and Charges Template",
			"Sales Invoice": "Sales Taxes and Charges Template",
			"Delivery Note": "Sales Taxes and Charges Template"
		}
		tax_template = frappe.db.sql("select name from `tab{0}` \
			where name like '%{1}%' and company = '{2}'".format(tax_temp_map[doc.doctype], template.split(' - ')[0], doc.company))	
		if tax_template:
			return tax_template[0][0]
	return ''

def validate_price_list(doc):
	user_doc = frappe.db.get_value("User",frappe.session.user,'company')
	if doc.customer_or_farmer == "Farmer" and doc.selling_price_list not in ["GTFS","LFS"+"-"+user_doc]:
		frappe.throw(_("First Create Material Price list for <b>VLCC Local Farmer</b>"))
	
	if doc.customer_or_farmer in ["Vlcc Local Customer","Vlcc Local Institution"] and doc.selling_price_list not in ["GTCS","LCS"+"-"+user_doc]:
		frappe.throw(_("Please Create Material price List First for <b>Customer</b>"))


@frappe.whitelist()
def get_item_by_customer_type(doctype, txt, searchfield, start, page_len, filters):
	vlcc_settings = frappe.get_doc("VLCC Settings",filters.get('vlcc'))
	items_dict = {}
	item_list = []
	for item in vlcc_settings.vlcc_item:
		if items_dict and item.customer_type in items_dict:
			items_dict[item.customer_type].append(item.item)
		else:
			items_dict[item.customer_type] = [item.item]
	if items_dict and filters.get('customer_type') in items_dict:
		final_item_list = "(" + ",".join("'{0}'".format(item) for item in items_dict[filters.get('customer_type').encode('utf-8')]) + ")"
		item_list = frappe.db.sql("""select name,item_group from tabItem 
			where name in {final_item_list} and name like '{txt}' """.format(final_item_list=final_item_list,txt= "%%%s%%" % txt),as_list=1,debug=0)
	
	p_item = [item.get('item_name') for item in filters.get("items_dict")]
	item_list_update = item_list
	if p_item[0]:
		item_list_update = [item for item in item_list if item[0] not in p_item]
	return item_list_update


def get_net_off(farmer, company):
	#filters are must as it is net off report data retrival
	fliters = {
	"ageing_based_on": "Posting Date",
	"report_date": nowdate(),
	"company": company,
	"farmer": farmer
	}
	if len(get_data(fliters)):
		return round(get_data(fliters)[0][10],2)
	else: return 0