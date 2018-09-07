from __future__ import unicode_literals
import frappe
import json
from six import string_types

@frappe.whitelist()
def get_data(filters=None):
	filters = json.loads(filters)
	cc_vlcc_details = {}
	cc = frappe.db.get_value("Address",{'name':filters.get('cc')},['centre_id','manager_name'],as_dict=1)
	vlcc = frappe.db.get_value("Village Level Collection Centre",{'name':filters.get('vlcc')},['amcu_id','name1'],as_dict=1)
	# print vlcc,"vlc\n\n\n\n"
	# print cc,"cc\n\n\n\n"
	if cc and vlcc:
		cc_vlcc_details = {'vlcc_name':vlcc.get('name1'),
							'vlcc_id':vlcc.get('amcu_id'),
							"cc_name":cc.get('manager_name'),
							"cc_id":cc.get('centre_id')
		}
	
	return cc_vlcc_details

# @frappe.whitelist()
# def get_xlsx(filters=None):
# 	from frappe.utils.xlsxutils import make_xlsx
# 	data = [[]]
# 	xlsx_file = make_xlsx(data, "Admin Report")
# 	print xlsx_file.getvalue()