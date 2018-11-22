# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stellapps Technologies Private Ltd.
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FarmerPaymentLog(Document):
	pass

def log_permission_query(user):
	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},
			  ['operator_type','company','branch_office'], as_dict =1)

	date_list =['"%s"'%i.get('name') for i in frappe.db.sql("""select name from 
				`tabFarmer Payment Log` 
				where vlcc = %s""",(user_doc.get('company')),as_dict=True)]

	if date_list:
		if user != 'Administrator' and 'Vlcc Manager' in roles:
			return """`tabFarmer Payment Log`.name in ({date})""".format(date=','.join(date_list))
	else:
		if user != 'Administrator':
			return """`tabFarmer Payment Log`.name = 'Guest' """
