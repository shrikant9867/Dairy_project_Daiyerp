
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
import time
import api_utils as utils
from frappe import _
import dairy_utils as utils
import requests
from item_api import get_seesion_company_datails
import json

@frappe.whitelist()
def create_pr(data):
	response_dict, response_data = {}, []
	try:
		data_ = json.loads(data)
		if data_:
			if data_.get('client_id') and data_.get('supplier'):
				if cint(data_.get('additional_discount_percentage')) < 100:
					pr_exist = frappe.db.get_value("Purchase Receipt",{"client_id":data_.get('client_id')}, 'name')
					if not pr_exist:
						response_dict.update({"status": "success","name": make_pr(data_)})
					else:
						response_dict.update({"status": "success", "name": pr_exist})
				else:
					frappe.throw('Percentage not grater than 100')
			else:
				response_dict.update({"status":"error", "response":"client id, camp office , item are required "})
	except Exception,e:
		frappe.db.rollback()
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
		utils.make_mobile_log(title="Sync failed PR creation",method="create_pr", status="Error",
			data = data, message=e, traceback=frappe.get_traceback())
	return response_dict

def make_pr(data):
	pr_obj = frappe.new_doc("Purchase Receipt")
	pr_obj.update(data)
	for row in pr_obj.items:
		if row.received_qty and row.qty:
			row.rejected_qty = row.received_qty - row.qty
	pr_obj.buying_price_list = get_price_list()
	pr_obj.flags.ignore_permissions = True
	pr_obj.save()
	pr_obj.submit()
	utils.make_mobile_log(title="Sync Passes PR creation",method="make_pr", status="Success",
			data = pr_obj.name, message="NO message", traceback="No traceback")
	update_po(pr_obj)
	return pr_obj.name


@frappe.whitelist()
def get_po_attr(supplier):
	"""Make PR for With PO reference attributes"""	
	try:
		response_dict, response_data = {}, []
		if frappe.db.exists('Supplier',supplier):
			po_list = frappe.db.sql("""select name,schedule_date from `tabPurchase Order` where supplier = '{0}' and status in ('To Receive and Bill') and company = '{1}'""".format(supplier,get_seesion_company_datails().get('company')),as_dict=1)
			for row in po_list:
				row.update({"items": frappe.db.sql("select item_code,rate,(qty - received_qty) as qty,uom from `tabPurchase Order Item` where parent = '{0}'".format(row.get('name')),as_dict=1)})
			response_dict.update({"status":"success", "data": po_list})
		else:
			frappe.throw("Supplier does not exist")
	except Exception,e:
		utils.make_mobile_log(title="Sync failed PO attribute for supplier",method="get_po_attr", status="Error",
			data = supplier, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})

	return response_dict

@frappe.whitelist()
def get_mi_attr(supplier):
	response_dict = {}
	try:
		mr_list = frappe.db.sql("""select name,schedule_date from `tabMaterial Request` where company = '{0}' and status = 'Ordered' and camp_office = '{1}' and is_dropship =1""".format(get_seesion_company_datails().get('company'),supplier),as_dict=1)
		for row in mr_list:
			row.update({"items": frappe.db.sql("select item_code,qty,uom from `tabMaterial Request Item` where parent = '{0}'".format(row.get('name')),as_dict=1)})
		response_dict.update({"status":"success","data": mr_list})
	except Exception,e:
		utils.make_mobile_log(title="Sync failed MI attribute for supplier",method="get_mi_attr", status="Error",
			data = supplier, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict


@frappe.whitelist()
def get_pr_list():
	response_dict = {}
	try:
		pr_list = frappe.db.sql("""select status,company,name,posting_date,additional_discount_percentage,supplier,taxes_and_charges,discount_amount,grand_total,apply_discount_on from `tabPurchase Receipt` where company = '{0}' and status in ('To Bill','Draft') order by creation desc limit 10 """.format(get_seesion_company_datails().get('company')),as_dict=1)
		for row in pr_list:
			row.update({"items": frappe.db.sql("select item_code,item_name,qty,rate,uom,original_qty, received_qty, rejected_qty from `tabPurchase Receipt Item` where parent = '{0}' order by idx".format(row.get('name')),as_dict=1)})
			if row.get('taxes_and_charges'):
				row.update({row.get('taxes_and_charges'): frappe.db.sql("""select charge_type,description,rate from `tabPurchase Taxes and Charges` where parent = '{0}'""".format(row.get('name')),as_dict=1)})
			else:
				del row['taxes_and_charges']
		response_dict.update({"status":"success","data":pr_list})
	except Exception,e:
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
	return response_dict



@frappe.whitelist()
def draft_pr(data):
	response_dict = {}
	dn_reference = ''
	try:
		data = json.loads(data)
		if data.get('name'):
			pr_doc = frappe.get_doc("Purchase Receipt",data.get('name'))
			dn_reference =  pr_doc.items[0].get('delivery_note')
			pr_doc.update(data)
			for row in pr_doc.items:
				row.delivery_note = dn_reference
				row.rejected_qty = row.received_qty - row.qty
			pr_doc.buying_price_list = get_price_list()
			pr_doc.flags.ignore_permissions = True
			pr_doc.flags.ignore_mandatory = True
			pr_doc.save()
			pr_doc.submit()
			response_dict.update({"status": "success","name":pr_doc.name})
			utils.make_mobile_log(title="Sync passed Draft PR",method="draft_pr", status="Success",
			data = pr_doc.name, message= "No message", traceback= "No traceback")
		else:
			frappe.throw(_("Name Parameter Missing"))

	except Exception,e:
		frappe.db.rollback()
		response_dict.update({"status":"error","message":e,"traceback":frappe.get_traceback()})
		utils.make_mobile_log(title="Sync failed Draft PR",method="draft_pr", status="Error",
			data = data, message=e, traceback=frappe.get_traceback())
	return response_dict


def update_po(pr_obj):
	update_received_qty(pr_obj)
	po_nos = frappe.db.get_all("Purchase Receipt Item", { "parent": pr_obj.name }, "purchase_order as po")

	for po in po_nos:
		if po.get('po'):
			po = frappe.get_doc("Purchase Order", po.get('po'))
			all_received = True
			for i in po.items:
				if i.qty != i.received_qty:
					all_received = False
			po_status = "To Bill" if all_received else "To Receive and Bill"
			frappe.db.sql("update `tabPurchase Order` set status = '{0}' \
				where name = '{1}'".format(po_status, po.name))
			# po.flags.ignore_permissions = True
			# po.save()

def update_received_qty(doc):
	for pr_i in doc.items:
		if pr_i.get('purchase_order'):
			po = frappe.get_doc("Purchase Order", pr_i.get('purchase_order'))
			for po_i in po.items:
				if pr_i.item_code == po_i.item_code and po_i.parent == pr_i.purchase_order:
					received_qty = po_i.received_qty + pr_i.qty
					frappe.db.sql("update `tabPurchase Order Item` set received_qty = {0} \
						where name = '{1}'".format(received_qty, po_i.name))

def get_price_list():
	user_doc = frappe.db.get_value("User",frappe.session.user,\
			['company','operator_type','branch_office'],as_dict=1)
	camp = frappe.db.get_value("Village Level Collection Centre",\
		user_doc.get('company'),'camp_office') if user_doc.get('operator_type') == "VLCC" else ""
	
	if user_doc.get('operator_type') == "VLCC" and frappe.db.get_value("Price List",\
											"LCOVLCCB-"+ camp, 'name'):
		return "LCOVLCCB-"+ camp

	elif user_doc.get('operator_type') == "VLCC" and frappe.db.get_value("Price List",\
													"GTCOVLCCB", 'name'):
		return "GTCOVLCCB"

	else:
		frappe.throw(_("Please Create Material Price List First"))