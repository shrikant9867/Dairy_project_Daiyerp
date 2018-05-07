# Copyright (c) 2015, Indictrans Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import print_function, unicode_literals
import frappe

def get_associated_vlcc(doctype,text,searchfields,start,pagelen,filters):
	branch_office = frappe.db.get_value("User", frappe.session.user, 'branch_office')
	
	return frappe.db.sql("""
				select name
					from
				`tabVillage Level Collection Centre`
					where
				camp_office = %s
		""",(branch_office))



def get_filtered_warehouse(doctype,text,searchfields,start,pagelen,filters):
	branch_office = frappe.db.get_value("User", frappe.session.user, 'branch_office')
	
	return frappe.db.sql("""
				select name 
					from
				`tabWarehouse`
					where
				 company in (
				 		select name 
				 			from
				 		`tabVillage Level Collection Centre`
				 			where
				 		camp_office = %s
			 	)
		""",(branch_office))



