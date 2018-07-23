# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

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
		vlcc_setting_doc = frappe.get_doc("VLCC Settings",vlcc.name)
		vlcc_emails = [vlcc_doc.email_id]
		if vlcc_doc.operator_same_as_agent and vlcc_doc.operator_email_id:
			vlcc_emails.append(vlcc_doc.operator_email_id)
		if vlcc_doc.warehouse and vlcc_setting_doc and vlcc_setting_doc.item_stock_threshold_level:
			bin_list = frappe.db.get_all("Bin", {"warehouse": vlcc_doc.warehouse},"name")
			item_and_actual_qty = {}
			for bin_name in bin_list:
				bin_doc = frappe.get_doc("Bin",bin_name.name)
				if bin_doc.actual_qty < vlcc_setting_doc.item_stock_threshold_level and bin_doc.actual_qty >= 0:
					item_and_actual_qty[bin_doc.item_code] = bin_doc.actual_qty
			send_email_to_vlcc(item_and_actual_qty,vlcc.name,vlcc_emails)


def send_email_to_vlcc(item_and_actual_qty,vlcc_name,vlcc_emails):
	print vlcc_emails,"vlcc_emailssssssssssss"
	if vlcc_emails:
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
