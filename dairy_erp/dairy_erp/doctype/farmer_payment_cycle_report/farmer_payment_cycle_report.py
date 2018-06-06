# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from dairy_erp.dairy_utils import make_dairy_log

class FarmerPaymentCycleReport(Document):
	def on_submit(self):
		try:
			loans = frappe.db.sql("""
					select name,farmer_id,outstanding_amount,emi_amount,no_of_instalments,paid_instalment
				from 
					`tabFarmer Loan`
				where
					farmer_id = '{0}' and outstanding_amount != 0 and date_of_disbursement < now()	
				""".format(self.farmer_id),as_dict=1,debug=1)
			total_emi = self.get_total_emi()
			self.calc_proportinate_emi(total_emi, loans)

		except Exception,e:
			make_dairy_log(title="Sync failed for Data push",method="get_items", status="Error",
			data = "data", message=e, traceback=frappe.get_traceback())
			

	
	def get_total_emi(self):
		
		total_emi = frappe.db.sql("""
				select ifnull(sum(emi_amount),0) as total_emi
			from 
				`tabFarmer Loan`
			where
				farmer_id = '{0}' and outstanding_amount != 0		
			""".format(self.farmer_id),as_dict=1)
		if len(total_emi):
			return total_emi[0].get('total_emi') if total_emi[0].get('total_emi') != None else 0
		else: return 0

	
	def calc_proportinate_emi(self, total_emi, loans):
		for row in loans:
			prop_ratio = (float(row.get('emi_amount')) / float(total_emi)) * 100
			is_si_exist = frappe.db.get_value("Sales Invoice",{'cycle_': self.cycle}, 'name')
			if is_si_exist:
				update_si(self, is_si_exist, row, prop_ratio)
				update_loan(self, is_si_exist, row, prop_ratio)



def update_si(self, si_no, row, amount):
	si_doc = frappe.get_doc("Sales Invoice", si_no)
	for i in si_doc.items:
		i.rate = amount
		i.amount = amount
	si_doc.grand_total = amount
	si_doc.flags.ignore_validate_update_after_submit = True
	si_doc.save()


def update_loan(self, is_si_exist, row, prop_ratio):
	total_loan = frappe.db.get_value("Farmer Loan",row.get('name'),'advance_amount')
	sum_ = frappe.db.sql("""
			select ifnull(sum(grand_total),0) as total
		from 
			`tabSales Invoice` 
		where 
		farmer_advance =%s """,(row.get('name')),as_dict=1)
	
	if len(sum_):
		loan_doc = frappe.get_doc("Farmer Loan", row.get('name'))
		instlment = float(row.get('no_of_instalments') - float(row.get('paid_instalment')))
		loan_doc.outstanding_amount = float(total_loan) - sum_[0].get('total')
		loan_doc.emi_amount =  float(loan_doc.outstanding_amount) / instlment
		if loan_doc.outstanding_amount == 0:
			loan_doc.status = "Paid"
		loan_doc.flags.ignore_permissions = True
		loan_doc.save()



@frappe.whitelist()
def get_fmcr(start_date, end_date, vlcc, farmer_id, cycle=None):
	
	fmcr =  frappe.db.sql("""
			select rcvdtime,shift,milkquantity,fat,snf,rate,amount
		from 
			`tabFarmer Milk Collection Record`
		where 
			associated_vlcc = '{0}' and rcvdtime between '{1}' and '{2}' and farmerid= '{3}'
			""".format(vlcc, start_date, end_date, farmer_id),as_dict=1)
	amount = 0
	qty = 0
	for i in fmcr:
		amount += i.get('amount')
		qty += i.get('milkquantity')
	
	return {
		"fmcr":fmcr, 
		"incentive": get_incentives(amount, qty, vlcc) or 0, 
		"advance": get_advances(start_date, end_date, vlcc, farmer_id, cycle) or 0,
		"loan": get_loans(start_date, end_date, vlcc, farmer_id, cycle) or 0,
		"fodder": get_fodder_amount(start_date, end_date, farmer_id, vlcc) or 0,
		"vet": vet_service_amnt(start_date, end_date, farmer_id, vlcc) or 0
	}


def get_incentives(amount, qty, vlcc=None):
	if vlcc and amount and qty:
		incentive = 0
		name = frappe.db.get_value("Farmer Settings", {'vlcc':vlcc}, 'name')
		farmer_settings = frappe.get_doc("Farmer Settings",name)
		if farmer_settings.enable_local_setting and not farmer_settings.enable_per_litre:
			incentive = (float(farmer_settings.local_farmer_incentive ) * float(amount)) / 100	
		if farmer_settings.enable_local_setting and farmer_settings.enable_per_litre:
			incentive = (float(farmer_settings.local_per_litre) * float(qty))
		if not farmer_settings.enable_local_setting and not farmer_settings.enable_per_litre:
			incentive = (float(farmer_settings.farmer_incentives) * float(farmer_settings)) / 100
		if not farmer_settings.enable_local_setting and farmer_settings.enable_per_litre:
			incentive = (float(farmer_settings.per_litre) * float(qty))
		return incentive


def get_advances(start_date, end_date, vlcc, farmer_id, cycle = None):
	
	advance  = frappe.db.sql("""
			select ifnull(sum(outstanding_amount),0) as oustanding
		from 
			`tabFarmer Advance` 
		where
			creation < now() and  farmer_id = '{2}' and status = 'Unpaid'
		 """.format(start_date, end_date, farmer_id), as_dict=1, debug=1)
	if len(advance):
		return advance[0].get('oustanding') if advance[0].get('oustanding') != None else 0
	else: return 0


def get_loans(start_date, end_date, vlcc, farmer_id, cycle = None):

	loan  = frappe.db.sql("""
			select ifnull(sum(outstanding_amount),0) as oustanding
		from 
			`tabFarmer Loan` 
		where
			creation < now() and  farmer_id = '{2}' and status = 'Unpaid'
		 """.format(start_date, end_date, farmer_id), as_dict=1, debug=1)
	if len(loan):
		return loan[0].get('oustanding') if loan[0].get('oustanding') != None else 0
	else: return 0


def get_fodder_amount(start_date, end_date, farmer_id, vlcc=None):
	
	fodder = frappe.db.sql("""
			select ifnull(sum(s.grand_total),0) as amt 
		from 
			`tabSales Invoice Item` si,
			`tabSales Invoice` s 
		where 
			s.name= si.parent and 
			s.docstatus = 1 and
			si.item_group in ('Cattle Feed') and s.local_sale = 1  and 
			s.farmer = '{0}'and
			s.posting_date between '{1}' and '{2}'
			""".format(farmer_id, start_date, end_date),as_dict=1)
	if len(fodder):
		return fodder[0].get('amt') if fodder[0].get('amt') != None else 0
	else: return 0


def vet_service_amnt(start_date, end_date, farmer_id, vlcc=None): 
	
	vet_amnt = frappe.db.sql("""
			select ifnull(sum(s.grand_total),0) as amt 
		from 
			`tabSales Invoice Item` si,
			`tabSales Invoice` s 
		where 
			s.name= si.parent and 
			s.docstatus = 1 and
			si.item_group in ('Veterinary Services') and s.service_note = 1  and 
			s.farmer = '{0}'and
			s.posting_date between '{1}' and '{2}'
			""".format(farmer_id, start_date, end_date),as_dict=1)
	if len(vet_amnt):
		return vet_amnt[0].get('amt') if vet_amnt[0].get('amt') != None else 0
	else: return 0