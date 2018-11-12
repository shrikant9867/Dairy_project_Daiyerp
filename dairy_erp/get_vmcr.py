# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint
from frappe.utils.data import to_timedelta
import time
from frappe import _
import datetime
from frappe.utils.data import add_to_date
import dairy_utils as utils
import requests
import json


@frappe.whitelist()
def get_vmcr(data):
	api_data = json.loads(data)
	try:
		posting_date = datetime.datetime.strptime(api_data[0].get("date"),  "%d/%m/%Y").strftime("%Y-%m-%d")
		longformatid = api_data[0].get('soccode')
		res_dict = {'data':[],'mbrt':[{"route":" ","mbrt":"NULL","value":0,"color":"#ffffff","status":" "}]}
		vmcr = frappe.db.sql("""
				select
						associated_vlcc,
						CASE
						    WHEN shift = "MORNING" THEN "AM"
						    WHEN shift = "EVENING" THEN "PM"
						END,
						milkquantity,
						fat,
						snf,
						round(rate,2),
						round(amount,2),
						RIGHT(collectionroute,2)
				from
						`tabVlcc Milk Collection Record`
				where
						posting_date = '{0}'
						and (ifnull(SUBSTRING_INDEX(long_format_farmer_id, '_',-1),' ') like {1}
						or ifnull(SUBSTRING_INDEX(long_format_farmer_id_e, '_',-1),' ') like {1})
			""".format(posting_date,longformatid),as_list=1,debug=1)
		for row in vmcr:
			res_dict.get('data').append({'shift':row[1],'partycode':longformatid,\
			'partyname':row[0],'qty':row[2],'fat':row[3],'snf':row[4],'rate':row[5],\
			'amount':row[6],'status':'BILL PROCESSED','isbmc':1,'routecode':row[7],'prodconnection':' '})
		return res_dict

	except Exception,e:
		utils.make_dairy_log(title="Please Check Dairy Log",method="get_vmcr", status="Error",
		data = data, message=e, traceback=frappe.get_traceback())
		response_dict.update({"status": "Error", "message":e, "traceback": frappe.get_traceback()})

	return response_dict