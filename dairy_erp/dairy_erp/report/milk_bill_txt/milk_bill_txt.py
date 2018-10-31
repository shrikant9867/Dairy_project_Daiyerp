# Copyright (c) 2013, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import has_common
import json
import datetime
from dairy_erp import dairy_utils as utils
import os

def execute(filters=None):
	user_email = frappe.get_doc("User",frappe.session.user).email
	societyid = frappe.db.get_value('Address',{'manager_email':user_email,'address_type':'Chilling Centre'},'centre_id')
	filters.update({
		'societyid':societyid
		})
	columns, data = get_columns(), get_data(filters)
	return columns ,data 

def get_columns():

	columns = [
		_("Dairy") + ":Data:100",
		_("Date") + ":Date:100",
		_("S") + ":Data:100",
		_("Type") + ":Data:100", 
		_("Party") + ":Data:100",
		_("Route") + ":Data:100",
		_("Qty") + ":Data:100",
		_("FAT") + ":Data:100",
		_("SNF") + ":Data:100",
		_("Q") + ":Data:100"
	]

	return columns

def get_data(filters=None):
	vmcr_data = frappe.db.sql("""
							select
								" 009",
								date(collectiontime),
								CASE
								    WHEN shift = "MORNING" THEN "1"
								    WHEN shift = "EVENING" THEN "2"
								END,
								" 001",
								RIGHT(
									if(shift = "MORNING",
										long_format_farmer_id,
										long_format_farmer_id_e),
								 	5),
								RIGHT(collectionroute,3),
								round(milkquantity,1),
								round(fat,1),
								round(snf,1),
								ifnull(milkquality,'')
							from
								`tabVlcc Milk Collection Record`
							where
							{0} and docstatus = 1 order by date(collectiontime)""".format(get_conditions(filters)),as_list=1,debug=0)
	for row in vmcr_data:
		if row[4]:
			farmerid = row[4].split("_")
			if len(farmerid) == 2 and farmerid[1] and len(farmerid[1]) < 5:
				row[4] = (5 - len(farmerid[1]))*"0"+str(farmerid[1])
			if len(farmerid) == 1 and farmerid[0] and len(farmerid[0]) < 5:
				row[4] = (5 - len(farmerid[0]))*"0"+str(farmerid[0])
		if len(row[5]) < 3:
			row[5] = (3 - len(row[5]))*"0"+row[5]

		qty = str(row[6]).split(".")
		fat = str(row[7]).split(".")
		snf = str(row[8]).split(".")
		if len(str(row[6])) < 10 and len(qty) == 2:
			row[6] = (10 - len(str(row[6])))*"0"+qty[0]+"."+qty[1][0]
		if len(str(row[7])) < 6 and len(fat) == 2:
			row[7] = (6 - len(str(row[7])))*"0"+fat[0]+"."+fat[1][0]	
		if len(str(row[8])) < 6 and len(snf) == 2:
			row[8] = (6 - len(str(row[8])))*"0"+snf[0]+"."+snf[1][0]
	return vmcr_data

def get_conditions(filters=None):
	cond = "date(collectiontime) between '{0}' and '{1}'".format(filters.get('start_date'),filters.get('end_date'))
	user = frappe.session.user
	roles = frappe.get_roles()
	if ('Chilling Center Manager' in roles or 'Chilling Center Operator' in roles) and \
		user != 'Administrator':
		if filters.get("societyid"):
			cond += " and societyid = '{0}'".format(filters.get("societyid"))

	return cond
		
@frappe.whitelist()
def add_txt_in_file(filters=None):
	try:
		filters = json.loads(filters)
		file_path = frappe.local.site_path+"/public/files"
		user_email = frappe.get_doc("User",frappe.session.user).email
		societyid = frappe.db.get_value('Address',{'manager_email':user_email,'address_type':'Chilling Centre'},'centre_id')
		filters.update({
			'societyid':societyid
		})
		data = get_data(filters)
		if data:
			start_date = datetime.datetime.strptime(filters.get('start_date'),  "%Y-%m-%d").strftime("%d-%b-%Y")
			end_date = datetime.datetime.strptime(filters.get('end_date'),  "%Y-%m-%d").strftime("%d-%b-%Y")
			txt_data = "#TS From "+start_date+" to "+end_date+"\n"
			txt_data += " DRY|Date      |S|Type|Party|Rout|        Qty|    Fat|    SNF|Q"+"\n"
			txt_data += "#----------------------------------------------------------------"+"\n"
			for row in data:
				my_date = str(row[1])
				my_date = my_date[8:10]+'-'+my_date[5:7]+'-'+my_date[0:4]	
				
				row_str = str(row[0])+"|"+str(my_date)+"|"+str(row[2])+"|"+str(row[3])+"| "+str(row[4])+"| "+str(row[5])+"| "+str(row[6])+"| "+str(row[7])+"| "+str(row[8])+"|"+str(row[9])+"\n"
				
				txt_data += row_str
			file_name = "milk_bill_"+filters.get('start_date')+"_"+filters.get('end_date')+".txt"
			completeName = os.path.join(file_path, file_name)
			f = open(completeName,"w+")
			f.write(txt_data)
			f.close()
			statinfo = os.stat(file_path+"/"+file_name)
			file_doc = ""
			file_doc_name = frappe.db.get_value("File",{"file_name":file_name},"name")
			if file_doc_name:
				file_doc = frappe.get_doc("File",file_doc_name)
			if not file_doc:
				file_doc = frappe.new_doc("File")
				file_doc.file_name = file_name
				file_doc.file_size = statinfo.st_size
				file_doc.file_url = "/files/"+file_name
				file_doc.folder =  "Home/Attachments"
				file_doc.save()
			return {'file_url':file_doc.file_url,'file_name':file_doc.file_name}

	except Exception,e:
		frappe.db.rollback()
		utils.make_dairy_log(title="make_milk_bill_txt",method="make_mill_bill_txt", status="Error",
			data = "data", message=e, traceback=frappe.get_traceback())