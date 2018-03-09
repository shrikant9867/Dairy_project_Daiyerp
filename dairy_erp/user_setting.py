from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
from frappe import _
import api_utils as utils
from item_api import get_seesion_company_datails
import json



@frappe.whitelist()
def get_user_data():
	response_dict = {}

	try:
		user_data = frappe.db.sql("""select email,first_name,last_name,gender,mobile_no,company from `tabUser` 
									where name = '{0}' """.format(frappe.session.user),as_dict=1)

		co = frappe.db.get_value("Village Level Collection Centre",{"name":frappe.db.get_value("User",{"name":frappe.session.user},'company')},"camp_office")
		for user_ in user_data:
			user_.update({"camp_office":co,"dairy":frappe.db.get_value("Company",{"is_dairy":1},"name")})
		response_dict.update({"status":"success","data":user_data[0]})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict


@frappe.whitelist()
def set_password(data):

	response_dict = {}
	try:

		data_ = json.loads(data)
		user_doc = frappe.get_doc("User",frappe.session.user)
		user_doc.new_password = data_.get('new_password') if data_.get('new_password') else  \
								frappe.throw("Please provide new password")
		user_doc.send_password_update_notification = data_.get('send_password_update_notification') if data_.get('send_password_update_notification') else 0
		user_doc.flags.ignore_permissions = True
		user_doc.save()
		response_dict.update({"status":"success","data":"Password has been updated successfully"})

	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})

	return response_dict

	
	