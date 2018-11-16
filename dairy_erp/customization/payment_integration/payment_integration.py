# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt
# Author Khushal Trivedi 
from __future__ import unicode_literals
import frappe, requests, json
import frappe
from dairy_erp.dairy_utils import make_agrupay_log,make_dairy_log
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,add_days,random_string,now_datetime
from frappe import _

def pay_to_farmers_account(pe_obj):
	try:
		url = frappe.get_doc("Dairy Setting").get('url')
		payload = {
		  "farmerId": frappe.db.get_value("Farmer",{'full_name': pe_obj.party},'name'),
		  "amount": pe_obj.total_allocated_amount,
		  "remarks": "payment from ERP",
		  "paymentDate": pe_obj.posting_date,
		  "erpRefNo": pe_obj.erp_ref_no
		}
		response = requests.post(url, data=json.dumps(payload), headers = {'content-type': 'application/json'})
		response_ = json.loads(response.content)
		if response_.get('status') == "FAILURE":
			frappe.delete_doc("Payment Entry", pe_obj.name)
		make_agrupay_log(status=json.loads(response.content).get('status'),request_data=json.dumps(payload),
			sync_time=now_datetime(),response_text=json.dumps(response.content),response_code=response.status_code)
	except Exception,e:
		make_dairy_log(title="Sync failed for Farmer payment ",method="pay_to_farmers_account", status="Error",
		data = json.dumps(response.content), message=e, traceback=frappe.get_traceback())

@frappe.whitelist()
def confirm_farmer_payment(**kwargs):
	#callback webservice to confirm payment else rollback
	try:
		response_dict = {}
		pe = frappe.db.get_value("Payment Entry",{'erp_ref_no':kwargs.get('erpRefNo')},'name')
		if pe:
			if kwargs.get('status') == "SUCCESS":
				pe_doc = frappe.get_doc("Payment Entry",pe)
				pe_doc.flags.ignore_permissions = True
				pe_doc.submit()
				response_dict.update({"status": "Success","remarks":"Payment entry submitted successfully","payment_entry": pe_doc.name})
				make_agrupay_log(status="Success",request_data=kwargs,sync_time=now_datetime(),
				response_text=response_dict,response_code="")
			else:
				frappe.delete_doc("Payment Entry", pe)
				response_dict.update({"status":"Error","remarks": "Payment Entry rolled back", "payment_entry": pe})
				make_agrupay_log(status="Error",request_data=kwargs,sync_time=now_datetime(),
				response_text=response_dict,response_code="")
		else:
			response_dict.update({"status":"Error","remarks":"erp_ref_no does not exist"})
			make_agrupay_log(status="Error",request_data=kwargs,sync_time=now_datetime(),
				response_text=response_dict,response_code="")
			frappe.throw("<b>erp_ref_no</b> does not exist")
	except Exception,e:
		make_dairy_log(title="Sync failed for Farmer payment ",method="pay_to_farmers_account", status="Error",
		data = json.dumps(kwargs), message=e, traceback=frappe.get_traceback())
	return response_dict
