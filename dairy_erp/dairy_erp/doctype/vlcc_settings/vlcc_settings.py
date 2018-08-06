# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.csvutils import read_csv_content_from_attached_file
from frappe.utils import flt, now_datetime, cstr, random_string
import json
from frappe import _
from erpnext.accounts.utils import unlink_ref_doc_from_payment_entries
from frappe.core.doctype.sms_settings.sms_settings import send_sms
from dairy_erp import dairy_utils as utils
from frappe.utils import cstr
import requests
import json

class VLCCSettings(Document):
	def validate(self):
		user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)
		self.vlcc = user_doc.get('company')
		self.check_farmer_exist()

	def check_farmer_exist(self):
		user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company'], as_dict =1)
		farmer_id = frappe.db.get_value("Farmer",
			{"vlcc_name":user_doc.get('company')},"farmer_id")
		if farmer_id:
			if self.farmer_id1 == farmer_id or self.farmer_id2 == farmer_id:
				frappe.throw("Please enter differnet farmer id as it is linked with farmer <a href='#Form/Farmer/{0}'><b>{0}</b></a>".format(farmer_id))

@frappe.whitelist()
def check_record_exist():
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)
	config = frappe.get_all("VLCC Settings",filters = {"vlcc":user_doc.get('company')})
	if len(config):
		return True
	else:
		return False


def vlcc_setting_permission(user):

	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)

	config_list =['"%s"'%i.get('name') for i in frappe.db.sql("""select name from 
				`tabVLCC Settings` 
				where vlcc = %s""",(user_doc.get('company')),as_dict=True)]

	if config_list:
		if user != 'Administrator' and 'Vlcc Manager' in roles:
			return """`tabVLCC Settings`.name in ({date})""".format(date=','.join(config_list))
	else:
		if user != 'Administrator':
			return """`tabVLCC Settings`.name = 'Guest' """

#send Email and SMS when item in VLCC warehouse reach at item_stock_threshold_level

@frappe.whitelist(allow_guest=True)
def sms_and_email_for_item_stock_threshold_level(allow_guest=True):	
	vlcc_list = frappe.db.get_all("Village Level Collection Centre")
	for vlcc in vlcc_list:
		vlcc_doc = frappe.get_doc("Village Level Collection Centre",vlcc.name)
		vlcc_setting_doc = ""
		if frappe.db.exists("VLCC Settings",vlcc.name):
			vlcc_setting_doc = frappe.get_doc("VLCC Settings",vlcc.name)
		if vlcc_setting_doc:
			vlcc_emails = [vlcc_doc.email_id]
			if vlcc_doc.operator_same_as_agent and vlcc_doc.operator_email_id:
				vlcc_emails.append(vlcc_doc.operator_email_id)
			if vlcc_doc.warehouse and vlcc_setting_doc and vlcc_setting_doc.item_stock_threshold_level:
				bin_list = frappe.db.get_all("Bin", {"warehouse": vlcc_doc.warehouse},"name")
				item_and_actual_qty = {}
				for bin_name in bin_list:
					bin_doc = frappe.get_doc("Bin",bin_name.name)
					if vlcc_setting_doc.item_stock_threshold_level and bin_doc.actual_qty < vlcc_setting_doc.item_stock_threshold_level and bin_doc.actual_qty >= 0:
						item_and_actual_qty[bin_doc.item_code] = bin_doc.actual_qty
				send_email_to_vlcc(item_and_actual_qty,vlcc.name,vlcc_emails)
				send_sms_to_vlcc(item_and_actual_qty,vlcc.name,vlcc.contact_no,vlcc.operator_number)

def send_email_to_vlcc(item_and_actual_qty,vlcc_name,vlcc_emails):
	if vlcc_emails and item_and_actual_qty:
		email_template = frappe.render_template(
			"templates/includes/item_stock_threshold_level.html", {
										"item_and_qty":item_and_actual_qty,
										"vlcc_name":vlcc_name
										}
						)

		frappe.sendmail(
			subject='Creation of Material Indent',
			recipients=vlcc_emails,
			message=email_template,
			now=True
		)

		frappe.db.commit()


def send_sms_to_vlcc(item_and_actual_qty,vlcc_name,vlcc_contact_no,vlcc_operator_number=None):
	contact_nos	= [vlcc_contact_no]
	contact_nos.append(vlcc_operator_number) if vlcc_operator_number else ""
	message = "Dear VLCC Manager,\r\nPlease Raise MI for below items, as these items are having low stock.\r\n"
	for item, qty in item_and_actual_qty.items():
		message = message + str(item)+': '+str(qty)+'\r\n'
	message += '\nSmartERP'
	try:
		send_sms(contact_nos,str(message))
	except Exception,e:
		frappe.db.rollback()
		utils.make_dairy_log(title="SMS Not Send",method="sms_threshold_level", status="Error",
			data = "data", message=e, traceback=frappe.get_traceback())

# @frappe.whitelist(allow_guest=True)
# def sms_threshold_level(allow_guest=True):
# 	# contact_nos	= [vlcc_contact_no].append(vlcc_operator_number) if vlcc_operator_number else ""
# 	message = "Dear VLCC Manager,\r\nPlease Raise MI for below items, as these items are having low stock.\r\n"
# 	item_and_qty = {"CHAI":12}
# 	for item, qty in item_and_qty.items():
# 		message = message + str(item)+': '+str(qty)+'\r\n'
# 	message += '\nSmartERP'
# 	try:
# 		send_sms(["917976680164"],str(message))
# 	except Exception,e:
# 		frappe.db.rollback()
# 		utils.make_dairy_log(title="SMS Not Send",method="sms_threshold_level", status="Error",
# 			data = "data", message=e, traceback=frappe.get_traceback())

@frappe.whitelist()
def get_item_by_customer_type(doctype, txt, searchfield, start, page_len, filters):
	item_list = [item.get('item') for item in filters.get('items_dict') if item.get('customer_type') == filters.get('customer_type')]
	if item_list[0]:
		final_item_list = "(" + ",".join("'{0}'".format(item) for item in item_list[0:-1]) + ")"
		if final_item_list  != '()':
			final_item_list = " and name not in"+ final_item_list
		else:
			final_item_list = ""
		item = frappe.db.sql("""
			select name,item_group 
		from 
			tabItem 
		where 
			item_group != 'Stationary' and name not 
			in ('Advance Emi', 'Loan Emi', 'Milk Incentives')
			{final_item_list} and name like '{txt}' """.format(final_item_list=final_item_list,txt= "%%%s%%" % txt),as_list=1,debug=1)
	else:
		item = frappe.db.sql("""
			select name,item_group 
		from 
			tabItem 
		where 
			item_group != 'Stationary' and name not 
				in ('Advance Emi', 'Loan Emi', 'Milk Incentives') and name like '{txt}' """.format(txt= "%%%s%%" % txt),as_list=1)
	return item

@frappe.whitelist()
def get_csv(doc):
	doc = json.loads(doc)
	max_rows = 500
	msg,fmcr_msg = "",""
	rows = read_csv_content_from_attached_file(frappe.get_doc("VLCC Settings",doc.get('name')))

	if not rows:
		frappe.throw(_("Please select a valid csv file with data"))

	if len(rows) > max_rows:
		frappe.throw(_("Maximum {0} rows allowed").format(max_rows))

	for row in rows:
		try:
			if row[0] and frappe.db.exists("Farmer Milk Collection Record",row[0]):
				fmcr = frappe.get_doc("Farmer Milk Collection Record",row[0])
				if fmcr and fmcr.docstatus == 1 and fmcr.associated_vlcc == doc.get('name'):
					delete_linked_doc(fmcr)
					msg = _("Records Deleted Successfully,for more info please check 'Dairy log' on server")
					make_dairy_log(title="FMCR Deleted Successfully" ,method="delete_fmcr", status="Success",
					data = fmcr.as_dict(),doc_name=fmcr.name)
				elif fmcr and fmcr.docstatus == 2 and fmcr.associated_vlcc == doc.get('name'):
					make_dairy_log(title="Cancelled FMCR Deleted Successfully" ,method="delete_fmcr", status="Success",
					data = fmcr.as_dict(),doc_name=fmcr.name)
					frappe.db.sql("""delete from `tabFarmer Milk Collection Record` where name = %s""",(fmcr.name))
				elif fmcr.associated_vlcc != doc.get('name'):
					fmcr_msg += fmcr.name + " ,"
		except Exception as e:
			frappe.db.rollback()
			msg = _("** Records Deletion Failed, for more info please check 'Dairy log' on server")
			make_dairy_log(title="FMCR Deletion Failed",method="delete_fmcr", status="Error",
			data = fmcr.as_dict(), message=e, traceback=frappe.get_traceback())
	if fmcr_msg:
		make_dairy_log(title="FMCR Not Mapped With VLCC",method="delete_fmcr", status="Success",
		data = fmcr_msg)
		frappe.msgprint("Please enter FMCR associated with vlcc,for more info please check 'Dairy log' on server")
	if msg:
		frappe.msgprint(msg)

def delete_linked_doc(fmcr_doc):

	pi = frappe.db.get_value("Purchase Invoice",{"farmer_milk_collection_record":fmcr_doc.name},"name")
	pr = frappe.db.get_value("Purchase Receipt",{"farmer_milk_collection_record":fmcr_doc.name},"name")

	unlink_ref_doc_from_payment_entries(frappe.get_doc("Purchase Invoice",pi))
	frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(pi))
	frappe.db.sql("""delete from `tabGL Entry` where voucher_no = %s""",(pr))
	frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_no = %s""",(pr))
	frappe.db.sql("""delete from `tabPurchase Invoice` where name = %s""",(pi))
	frappe.db.sql("""delete from `tabPurchase Receipt` where name = %s""",(pr))
	frappe.db.sql("""delete from `tabFarmer Milk Collection Record` where name = %s""",(fmcr_doc.name))

def make_dairy_log(**kwargs):
	dlog = frappe.get_doc({"doctype":"Dairy Log"})
	dlog.update({
			"title":kwargs.get("title"),
			"method":kwargs.get("method"),
			"sync_time": now_datetime(),
			"status":kwargs.get("status"),
			"data":kwargs.get("data", ""),
			"error_message":kwargs.get("message", ""),
			"traceback":kwargs.get("traceback", ""),
			"doc_name": kwargs.get("doc_name", "")
		})
	dlog.insert(ignore_permissions=True)
	frappe.db.commit()
	return dlog.name