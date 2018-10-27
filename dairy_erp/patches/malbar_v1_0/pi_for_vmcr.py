# critical patch for creating purchace invoices against created purchase receipts
from __future__ import unicode_literals
import frappe

def execute():
	# created_vmcr_list = frappe.get_all("Vlcc Milk Collection Record", {'societyid': "3000"}, 'name')
	# for vmcr in created_vmcr_list:
	# 	print"\n VMCR \t",vmcr.get('name')
	# 	if frappe.db.exists("Purchase Receipt", {'':})