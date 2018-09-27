# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from frappe.utils.csvutils import read_csv_content_from_attached_file
from frappe.utils import flt, now_datetime, cstr, random_string
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
		count=0
		flag = 0
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
						vlcc = frappe.new_doc("Village Level Collection Centre")
						vlcc.vlcc_name = row[0]
						vlcc.abbr = row[1]
						vlcc.name1 = row[2]
						vlcc.email_id = row[3]
						vlcc.contact_no = row[4]
						vlcc.plant_office = row[5]
						vlcc.camp_office = row[6]
						vlcc.amcu_id = row[7]
						vlcc.vlcc_type = row[8]
						vlcc.global_percent_effective_credit = row[9]
						vlcc.chilling_centre =row[10]
						if int(row[11]) == 1:	

							vlcc.operator_same_as_agent = 1
							vlcc.operator_number = row[12]
							vlcc.operator_email_id = row[13]
							vlcc.operator_name = row[14]

						vlcc.flags.ignore_permissions = True	
						vlcc.save()	
						addr = frappe.new_doc("Address")
						addr.address_title = row[15]
						addr.address_type = "Vlcc"
						addr.address_line1 = row[16]
						addr.city = row[17]
						addr.vlcc = row[0]
						addr.append("links", {
									"link_doctype": "Company",
									"link_name": row[0]
								})
						addr.save()
						vlcc.address = row[0]+"-Vlcc"
						vlcc.address_display = row[16]+"\n"+row[17]+"\n"+addr.country
						vlcc.save()
						flag = 1
					else:
						traceback="AMCU ID Alreadry Exists"+str(row[7])
						make_dairy_log(title="Failed attribute for vlcc creation",method="vlcc_creation", status="Error",data = "data", message=traceback, traceback=frappe.get_traceback())

				else:
					traceback="VLCC Alreadry Exists"+str(row[0])
					make_dairy_log(title="Failed attribute for vlcc creation",method="vlcc_creation", status="Error",data = "data", message=traceback, traceback=frappe.get_traceback())
						
			count +=1
		if flag == 1:
			frappe.msgprint("Record Inserted")
			email=frappe.get_doc("User",frappe.session.user).email
			frappe.sendmail(
				recipients = email,
				subject="Bulk VLCC Creation Done ",
				message = "Your Bulk Vlcc Record Created Please Check and If Problem Occurce Call to Support team or Check Dairy Log"
			)			
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


