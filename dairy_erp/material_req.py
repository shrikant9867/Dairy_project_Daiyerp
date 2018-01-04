
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
from frappe import _
import dairy_utils as utils
import requests
import json


@frappe.whitelist()
def create_farmer(data):
	"""Separate API(client req), should have been merge in main(future scope) : VLCC"""

	response_dict = {}
	api_data = json.loads(data)
	if api_data:
		for row in api_data:
			response_dict.update({row.get('farmer_id'):[]})
			try:
				if row.get('society_id'):
					vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id": row.get('society_id')},'name')
					if vlcc :
						print"vlcc exist"
						if not frappe.db.sql("select full_name from `tabFarmer` where full_name=%s",(row.get("full_name"))):
							if not frappe.db.exists("Farmer",row.get("farmer_id")):
								farmer_obj = frappe.new_doc("Farmer")
								farmer_obj.full_name = row.get('full_name')
								farmer_obj.farmer_id = row.get('farmer_id')
								farmer_obj.contact_number = row.get('contact_no')
								farmer_obj.vlcc_name = vlcc
								farmer_obj.insert()
								response_dict.get(row.get('farmer_id')).append(farmer_obj.name)
							else:
								frappe.throw(_("Id Exist"))
						else:
							frappe.throw("Farmer Exist with same name")
					else:
						frappe.throw(_("Society does not exist"))
				else:
					frappe.throw(_("Society ID does not exist"))
	
			except Exception,e:
				utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
				data = data, message=e, traceback=frappe.get_traceback())
				print "++++++++++++++++++++",
				response_dict.get(row.get('farmer_id')).append({"Error": frappe.get_traceback()})
				# response_dict.get(row('farmer_id')).append(farmer_obj.name)

	return response_dict