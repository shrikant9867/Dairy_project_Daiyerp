from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime
from frappe import _
import dairy_utils as utils
from datetime import timedelta
import amcu_api as amcu_api
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
import requests
import json


def update_fmcr(data, row,response_dict):


	try: 
		vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},"name")
		config_hrs = frappe.db.get_value('VLCC Settings',{'vlcc':vlcc},'hours')
		fmcr = frappe.db.get_value('Farmer Milk Collection Record',
				{"transactionid":row.get('transactionid'),"farmerid":row.get('farmerid')},"name")
		if fmcr:
			fmcr_doc = frappe.get_doc("Farmer Milk Collection Record",fmcr)
			max_time = get_datetime(fmcr_doc.rcvdtime) +  timedelta(hours=int(config_hrs))
			if now_datetime() < max_time: 
				if fmcr_doc.amount <= row.get('amount'):
					update_fmcr_amt(fmcr_doc, data,row,response_dict)
				elif fmcr_doc.amount > row.get('amount'):

					debit_amount = fmcr_doc.amount - row.get('amount')
					je_exist = frappe.db.get_value("Journal Entry",
								{"farmer_milk_collection_record":fmcr_doc.name,
								"docstatus": ["!=", 2]},"name")

					if je_exist:
						je_doc = frappe.get_doc("Journal Entry",je_exist)
						je_doc.cancel()
						je = create_debit_note(data.get('societyid'), row, debit_amount,fmcr_doc)
					else:
						je = create_debit_note(data.get('societyid'), row, debit_amount,fmcr_doc)
						response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "Journal Entry '{0}' created against FMCR '{1}'".format(je,fmcr_doc.name)})
			else:
				response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "You can not update {0}".format(fmcr_doc.name)})
		else:
			response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"Message": "There are no transactions present with the transaction id {0}".format(row.get('transactionid'))})
	except Exception,e:
		frappe.db.rollback()
		utils.make_dairy_log(title="Sync failed for Data push",method="update_fmcr", status="Error",
		data = "data", message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": frappe.get_traceback()})	
	return response_dict
	
def update_fmcr_amt(fmcr_doc,data,row,response_dict):

	pi = frappe.db.get_value("Purchase Invoice",{"farmer_milk_collection_record":fmcr_doc.name},"name")
	pr = frappe.db.get_value("Purchase Receipt",{"farmer_milk_collection_record":fmcr_doc.name},"name")
	je_exist = frappe.db.get_value("Journal Entry",
				{"farmer_milk_collection_record":fmcr_doc.name,
				"docstatus": ["!=", 2]},"name")

	if pi:
		pi_doc = frappe.get_doc("Purchase Invoice",pi)
		pi_doc.cancel()
		frappe.delete_doc("Purchase Invoice", pi_doc.name)
	if pr:
		pr_doc = frappe.get_doc("Purchase Receipt",pr)
		pr_doc.cancel()
		frappe.delete_doc("Purchase Receipt", pr_doc.name)

	if je_exist:
		je_doc = frappe.get_doc("Journal Entry",je_exist)
		je_doc.cancel()

	fmcr_doc.cancel()
	frappe.delete_doc("Farmer Milk Collection Record", fmcr_doc.name)

	make_fmcr(data,row,response_dict)

def make_fmcr(data,row,response_dict):
	
	try:
		if data.get('imeinumber') and data.get('rcvdtime') and data.get('shift') and data.get('collectiondate'):
			if row.get('farmerid') and row.get('milktype') and row.get('collectiontime') \
				and row.get('milkquantity') and row.get('rate') and row.get('status') and row.get('transactionid'):
				if row.get('operation') == 'UPDATE':
					fmrc_entry = amcu_api.validate_fmrc_entry(data,row)
					if not fmrc_entry:
						if amcu_api.validate_society_exist(data):
							if amcu_api.farmer_associate_vlcc(data,row):
								vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
								farmer = frappe.db.get_value("Farmer",{"vlcc_name": vlcc},'name')
								farmer_supplier = frappe.db.get_value("Farmer",row.get('farmerid'),'full_name')
								row.update(
									{
										"collectiontime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('collectiontime'))/1000)),
										"qualitytime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('qualitytime'))/1000)),
										"quantitytime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cint(row.get('quantitytime'))/1000))
									}
								)
								fmrc_doc = frappe.new_doc("Farmer Milk Collection Record")
								fmrc_doc.farmer = farmer_supplier
								fmrc_doc.id = data.get('id')
								fmrc_doc.associated_vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":data.get('societyid')},'name')
								fmrc_doc.imeinumber = data.get('imeinumber')
								fmrc_doc.rcvdtime = data.get('rcvdtime')
								fmrc_doc.processedstatus = data.get('processedstatus')
								fmrc_doc.societyid = data.get('societyid')
								fmrc_doc.collectiondate =  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('collectiondate')/1000))
								fmrc_doc.shift = data.get('shift')
								fmrc_doc.starttime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('starttime')/1000))
								fmrc_doc.endtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('endtime')/1000))
								fmrc_doc.endshift = 1 if data.get('endshift') == True else 0
			 					fmrc_doc.update(row)
								fmrc_doc.flags.ignore_permissions = True
								fmrc_doc.flags.is_api = True
								fmrc_doc.submit()
								response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"fmrc": fmrc_doc.name})
								if row.get('status') == "Accept":
									pr = amcu_api.make_purchase_receipt_vlcc(data, row, vlcc, farmer_supplier, response_dict, fmrc_doc.name )
									amcu_api.purchase_invoice_against_farmer(data, row, vlcc,  farmer_supplier, pr.get('item_'), response_dict, pr.get('pr_obj'), fmrc_doc.name)
							else:
								traceback = "farmer does not exist"
								frappe.throw(_("farmer does not exist"))
						
						else :
							traceback = "vlcc does not exist!" 
							frappe.throw(_("vlcc does not exist!"))					
					else:
						response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"status":"success","response":"Record already created please check on server,if any exception check 'Dairy log'."})
			else:
				traceback = "data missing"
				response_dict.update({"status":"Error","response":"Data Missing","message": "farmerid,milktype,collectiontime,milkquantity,rate, status must be one of Accept or Reject are manadatory"})
		else:
			traceback = "data Missing"
			response_dict.update({"status":"Error","response":"Data Missing","message":"imeinumber,collectionDate,shift,rcvdTime are manadatory"})
	except Exception,e:
		utils.make_dairy_log(title="Sync failed for Data push",method="create_fmrc", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.get(row.get('farmerid')+"-"+row.get('milktype')).append({"error": traceback})		
	return response_dict

	
def create_debit_note(societyid, row, debit_amount, fmcr_doc):

	vlcc = frappe.db.get_value("Village Level Collection Centre",{"amcu_id":societyid},"name")
	def_pay_acc = frappe.db.get_value("Company",{"name":vlcc},['default_payable_account','abbr','cost_center'],as_dict=1)
	
	je_entry = frappe.new_doc("Journal Entry")
	je_entry.company = vlcc
	je_entry.voucher_type = "Debit Note"
	je_entry.farmer_milk_collection_record = fmcr_doc.name
	je_entry.posting_date = nowdate()
	je_entry.append('accounts',
		{
			"account": def_pay_acc.get('default_payable_account'),
			"party_type": "Supplier",
			"cost_center": def_pay_acc.get('cost_center'),
			"party": frappe.db.get_value("Farmer",row.get('farmerid'),'full_name'),
			"debit_in_account_currency": debit_amount,
			"reference_type": "Purchase Invoice",
			"reference_name": frappe.db.get_value("Purchase Invoice",\
							{"farmer_milk_collection_record" : fmcr_doc.name}, 'name')
		})
	#subsequent entry -credetors
	je_entry.append('accounts',
		{
			"account": "Sales Expenses"+" - "+def_pay_acc.get('abbr'),
			"cost_center":def_pay_acc.get('cost_center'),
			"credit_in_account_currency": debit_amount
		})
	je_entry.flags.ignore_permissions = True
	je_entry.flags.ignore_mandatory = True
	je_entry.save()
	je_entry.submit()
	return je_entry.name