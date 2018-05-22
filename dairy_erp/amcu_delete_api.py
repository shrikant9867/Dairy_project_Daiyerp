from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe.utils import flt, cstr,nowdate,cint
from frappe import _
import dairy_utils as utils
import amcu_api as amcu_api
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
import requests
import json

def delete_fmcr(data, row,response_dict):
	
	try:
		fmcr = frappe.db.get_value('Farmer Milk Collection Record',
				{"transactionid":row.get('transactionid')},"name")
		if fmcr:
			fmcr_doc = frappe.get_doc("Farmer Milk Collection Record",fmcr)
			delete_linked_doc(fmcr_doc)
			response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "Documents against FMCR '{0}' are deleted".format(fmcr_doc.name)})
		else:
			response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "There are no documents present with the transaction id {0} for deletion".format(row.get('transactionid'))})

	except Exception,e:
		frappe.db.rollback()
		utils.make_dairy_log(title="Sync failed for Data push",method="delete_fmcr", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": traceback})	
	return response_dict


def delete_linked_doc(fmcr_doc):

	pi = frappe.db.get_value("Purchase Invoice",{"farmer_milk_collection_record":fmcr_doc.name},"name")
	pr = frappe.db.get_value("Purchase Receipt",{"farmer_milk_collection_record":fmcr_doc.name},"name")

	if pi:
		pi_doc = frappe.get_doc("Purchase Invoice",pi)
		pi_doc.cancel()
		frappe.delete_doc("Purchase Invoice", pi_doc.name)
	if pr:
		pr_doc = frappe.get_doc("Purchase Receipt",pr)
		pr_doc.cancel()
		frappe.delete_doc("Purchase Receipt", pr_doc.name)

	fmcr_doc.cancel()
	frappe.delete_doc("Farmer Milk Collection Record", fmcr_doc.name)