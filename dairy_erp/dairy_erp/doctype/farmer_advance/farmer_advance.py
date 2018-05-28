# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class FarmerAdvance(Document):
	
	def on_submit(self):
		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabFarmer Date Computation`
			where
				'{0}' < start_date order by start_date limit {1}""".
			format(self.date_of_disbursement,self.emi_deduction_start_cycle),as_dict=1)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]

		req_cycle = frappe.db.sql("""
				select name,start_date
			from
				`tabFarmer Date Computation`
			where
				'{date}' < start_date and name not in ({cycle}) order by start_date limit {instalment}
			""".format(date=self.date_of_disbursement, cycle = ','.join(not_req_cycl_list),
				instalment = self.no_of_instalment),as_dict=1,debug=1)
		for row in req_cycle:
			self.create_recur_si(row)

	def create_recur_si(self,data):
		si_rec = frappe.new_doc("Recurring Sales Invoice Log")
		si_rec.start_date = data.get('start_date')
		si_rec.emi_amount = self.emi_amount
		si_rec.type = "Advance"
		si_rec.farmer_id = self.farmer_id
		si_rec.farmer_name = self.farmer_name
		si_rec.vlcc = self.vlcc
		si_rec.farmer_advance = self.name
		si_rec.status = "Pending"
		si_rec.flags.ignore_permissions = True
		si_rec.save()
		si_rec.submit()

	def validate(self):
		if self.advance_amount <= 0:
			frappe.throw(_("Advance Amount cannot be zero"))
