from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json
import re
from frappe.utils import money_in_words, has_common

def je_permission(user):
	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	if has_common(['Vlcc Manager',"Vlcc Operator"],roles) and user != 'Administrator':
		return """`tabJournal Entry`.company = '{0}'""".format(user_doc.get('company'))
