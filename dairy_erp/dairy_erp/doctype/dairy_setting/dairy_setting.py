# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from frappe.utils.csvutils import read_csv_content_from_attached_file
from frappe.utils import flt, now_datetime, cstr, random_string
import time

class DairySetting(Document):

	def validate(self):
		vlcc_list = [vlcc.get('name') for vlcc in frappe.get_all("Village Level Collection Centre")]
		for vlcc in vlcc_list:
			if frappe.db.exists("VLCC Settings",vlcc):
				vlcc_settings = frappe.get_doc("VLCC Settings",vlcc)
				if vlcc_settings and vlcc_settings.flag_negative_effective_credit == 0:
					frappe.db.set_value("VLCC Settings",vlcc,'allow_negative_effective_credit',\
							self.allow_negative_effective_credit)

@frappe.whitelist()
def get_csv(doc):
	traceback = ""
	try:
		doc = json.loads(doc)
		count, flag, longformat_flag = 0, 0, 0
		fail_vlcc,sucess_vlcc = [],[]
		max_rows = 500
		msg,fmcr_msg = "",""
		rows = read_csv_content_from_attached_file(frappe.get_doc("Dairy Setting",doc.get('name')))

		if not rows:
			frappe.throw(_("Please select a valid csv file with data"))

		if len(rows) > max_rows:
			frappe.throw(_("Maximum {0} rows allowed").format(max_rows))

		for row in rows:

			if count != 0:
				if  not frappe.db.exists("Village Level Collection Centre",row[0]) and row[0] !="":
					if not frappe.db.get_value("Village Level Collection Centre",{"amcu_id":row[7]},"name"):
						if not frappe.db.get_value("Village Level Collection Centre",{"longformatsocietyid_m":row[8]},"name"): #SD 17-10-2018 17:00
							if row[8]:#SD 17-10-2018 17:00
								longformat_id_len = row[8].split('_')#SD 17-10-2018 17:00
								if len(longformat_id_len) < 4: #SD 17-10-2018 17:00
									longformat_flag = 1 #SD 17-10-2018 17:00
								if len(longformat_id_len) == 4 and (not longformat_id_len[0] or not longformat_id_len[1] or not longformat_id_len[2] or not longformat_id_len[3]): #SD 17-10-2018 17:00
									longformat_flag = 1
								if len(longformat_id_len) > 4:
									longformat_flag = 1
									

							if longformat_flag == 0:
								vlcc = frappe.new_doc("Village Level Collection Centre")
								vlcc.vlcc_name = row[0]
								vlcc.abbr = row[1]
								vlcc.name1 = row[2]
								vlcc.email_id = row[3]
								vlcc.contact_no = row[4]
								vlcc.plant_office = row[5]
								vlcc.camp_office = row[6]
								vlcc.vlcc_type = row[9]
								vlcc.global_percent_effective_credit = row[10]
								vlcc.chilling_centre =row[11]
								vlcc.longformatsocietyid_m = row [8] #SD 17-10-2018 17:00
								vlcc.amcu_id = row[7]  #SD 17-10-2018 17:00

								if int(row[12]) == 1:
									vlcc.operator_same_as_agent = 1
									vlcc.operator_number = row[13]
									vlcc.operator_email_id = row[14]
									vlcc.operator_name = row[15]

								vlcc.is_auto_society_id = 1
								vlcc.flags.ignore_permissions = True
								
								vlcc.save()
								address=make_address(address_title=row[16],address_type=row[17],address_line1=row[18],city=row[19],vlcc_name=vlcc.name)
								frappe.db.set_value("Village Level Collection Centre",vlcc.name,"address",address.name)
								address_display = address.address_line1+"\n"+address.city+"\n"+address.country
								frappe.db.set_value("Village Level Collection Centre",vlcc.name,"address_display",address_display)
								sucess_vlcc.append(row[0])
								flag = 1
							else:
								if longformat_flag == 1:#SD 17-10-2018 17:00
									traceback = "The Long Format Society Id should be of Format OrgiD_CCID_RouteId_SocietyId: \t"+str(row[8])
									fail_vlcc.append(row[0])
									make_dairy_log(title="Failed attribute for vlcc creation",method="vlcc_creation", status="Error",data = "data", message=traceback, traceback=frappe.get_traceback())

						else:
							traceback="Long Format Farmer Id Alreadry Exists"+str(row[8])#SD 17-10-2018 17:00
							fail_vlcc.append(row[0])#SD 17-10-2018 17:00
							make_dairy_log(title="Failed attribute for vlcc creation",method="vlcc_creation", status="Error",data = "data", message=traceback, traceback=frappe.get_traceback())#SD 17-10-2018 17:00

					else:
						traceback="AMCU ID Alreadry Exists"+str(row[7])
						fail_vlcc.append(row[0])
						make_dairy_log(title="Failed attribute for vlcc creation",method="vlcc_creation", status="Error",data = "data", message=traceback, traceback=frappe.get_traceback())

				else:
					traceback="VLCC Alreadry Exists"+str(row[0])
					fail_vlcc.append(row[0])
					make_dairy_log(title="Failed attribute for vlcc creation",method="vlcc_creation", status="Error",data = "data", message=traceback, traceback=frappe.get_traceback())
						
			count +=1
		if flag == 1:
			frappe.msgprint("<h4>Record Summary</h4></br> Sucess: <b>{0}</b></br>Failed: <b>{1}</b></br>Vlcc Failed to Create,Please Check Dairy Log".format(len(sucess_vlcc),len(fail_vlcc)))
			email=frappe.get_doc("User",frappe.session.user).email
			frappe.sendmail(
				recipients = email,
				subject="Bulk VLCC Creation Done ",
				message = ("Your Bulk Vlcc Record Created Please Check <br> <b>Record Summary</b></br><b>Sucess: {0}</b></br><b>Failed: {1}</b> If Problem Occurce Call to Support team or Check Dairy Log".format(len(sucess_vlcc),len(fail_vlcc))),
				delayed=False

			)
		else:
			frappe.msgprint("<h4>Record Summary</h4></br>Failed: <b>{0}</b> </br>Vlcc Failed to Create,Please Check Dairy Log".format(len(fail_vlcc)))
						
	except Exception as e:
		frappe.db.rollback()
		make_dairy_log(title="Failed attribute for vlcc creation",method="vlcc_creation", status="Error",data = "data", message=e, traceback=frappe.get_traceback())
			
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

def make_address(**kwargs):
	
	addr = frappe.new_doc("Address")
	addr.address_title = kwargs.get("address_title")
	addr.address_type = kwargs.get("address_type")
	addr.address_line1 = kwargs.get("address_line1")
	addr.city = kwargs.get("city")
	addr.vlcc = kwargs.get("vlcc_name")
	addr.append("links",{
		"link_doctype":"Company",
		"link_name":kwargs.get("vlcc_name")
		})	
	
	addr.save()

	return addr
	

