# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from dairy_erp.dairy_utils import make_dairy_log

class FarmerPaymentCycleReport(Document):
	
	def validate(self):
		pass
		# if frappe.db.get_value("Farmer Payment Cycle Report",{'cycle':self.cycle,\
		# 	 'vlcc_name':self.vlcc_name, 'farmer_id':self.farmer_id},'name'):
		# 	frappe.throw(_("FPCR has been generated for this cycle"))
		
	
	def before_submit(self):
		self.advance_operation()
		self.loan_operation()

	
	def advance_operation(self):
		for row in self.advance_child:
			pass
	
	def loan_operation(self):
		for row in self.loan_child:
			if not frappe.db.get_value("Sales Invoice",{'cycle_': self.cycle,\
						'farmer_advance':row.loan_id }, 'name')
				self.create_si(row,)

	def create_si(self, data):
		si_doc = frappe.new_doc("Sales Invoice")
		si_doc.type = "Loan"
		si_doc.customer = self.farmer_name
		si_doc.company = self.vlcc_name
		si_doc.farmer_advance = row.get('name')
		si_doc.cycle_ = self.cycle
		si_doc.append("items",{
			"item_code":"Milk Incentives",
			"qty": 1,
			"rate": amount,
			"cost_center": frappe.db.get_value("Company", self.vlcc_name, "cost_center")
			})
		si_doc.flags.ignore_permissions = True
		si_doc.save()
		si_doc.submit()


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
		"vet": vet_service_amnt(start_date, end_date, farmer_id, vlcc) or 0,
		"child_loan": get_loans_child(start_date, end_date, vlcc, farmer_id,cycle),
		"child_advance": get_advance_child(start_date, end_date, vlcc, farmer_id, cycle)
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
		 """.format(start_date, end_date, farmer_id), as_dict=1)
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
		 """.format(start_date, end_date, farmer_id), as_dict=1)
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


#### Advance Part ##########

def get_total_emi_advance(self,advance):
	total_emi = frappe.db.sql("""
				select ifnull(sum(emi_amount),0) as total_emi
			from 
				`tabFarmer Advance`
			where
				farmer_id = '{0}' and outstanding_amount != 0		
			""".format(self.farmer_id),as_dict=1)
	total = 0
	for row in advance:
		total += float(row.get('emi_amount'))
	# if len(total_emi):
	# 	return total_emi[0].get('total_emi') if total_emi[0].get('total_emi') != None else 0
	return total


@frappe.whitelist()
def get_cycle(doctype,text,searchfields,start,pagelen,filters):
	return frappe.db.sql("""
			select name 
		from
			`tabFarmer Date Computation`
		where
			 now() between start_date and end_date and vlcc = '{0}'
		""".format(filters.get('vlcc')))

def req_cycle_computation(data):
	
	not_req_cycl = frappe.db.sql("""
			select name
		from
			`tabFarmer Date Computation`
		where
			'{0}' < start_date and vlcc = '{1}' order by start_date limit {2}""".
		format(data.get('date_of_disbursement'),data.get('vlcc'),data.get('emi_deduction_start_cycle')),as_dict=1)
	not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
	instalment = int(data.get('no_of_instalments')) + int(data.get('extension'))
	if len(not_req_cycl):
		req_cycle = frappe.db.sql("""
				select name
			from
				`tabFarmer Date Computation`
			where
				'{date}' < start_date and name not in ({cycle}) and vlcc = '{vlcc}' order by start_date limit {instalment}
			""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),vlcc = data.get('vlcc'),
				instalment = instalment),as_dict=1)
		
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list
	return []

def get_current_cycle(data):
	return frappe.db.sql("""
			select name 
		from
			`tabFarmer Date Computation`
		where
			vlcc = %s and now() between start_date and end_date
		""",(data.get('vlcc')),as_dict=1)

def req_cycle_computation_advance(data):
	
	not_req_cycl = frappe.db.sql("""
			select name
		from
			`tabFarmer Date Computation`
		where
			'{0}' < start_date and vlcc = '{1}' order by start_date limit {2}""".
		format(data.get('date_of_disbursement'),data.get('vlcc'),data.get('emi_deduction_start_cycle')),as_dict=1)
	not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
	
	instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
	if len(not_req_cycl):
		req_cycle = frappe.db.sql("""
				select name
			from
				`tabFarmer Date Computation`
			where
				'{date}' < start_date and name not in ({cycle}) and vlcc = '{vlcc}' order by start_date limit {instalment}
			""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),vlcc = data.get('vlcc'),
				instalment = instalment),as_dict=1)
		
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list
	return []


def get_loans_child(start_date, end_date, vlcc, farmer_id, cycle=None):
	loans_ = frappe.db.sql("""
				select name,farmer_id,outstanding_amount,
				emi_amount,no_of_instalments,paid_instalment,advance_amount,
				emi_deduction_start_cycle,extension,date_of_disbursement,vlcc
			from 
				`tabFarmer Loan`
			where
				farmer_id = '{0}' and outstanding_amount != 0 and date_of_disbursement < now()	
				""".format(farmer_id),as_dict=1)
	loans = []
	for row in loans_:
		req_cycle = req_cycle_computation(row)
		if cycle in req_cycle_computation(row):
			loans.append(row)
	return loans


def get_advance_child(start_date, end_date, vlcc, farmer_id, cycle=None):
	advance_ = frappe.db.sql("""
				select name,farmer_id,outstanding_amount,emi_amount,advance_amount,
				no_of_instalment,paid_instalment,paid_instalment,emi_deduction_start_cycle,
				extension,date_of_disbursement,vlcc
			from 
				`tabFarmer Advance`
			where
				farmer_id = '{0}' and outstanding_amount != 0 and date_of_disbursement < now()	
			""".format(farmer_id),as_dict=1)
	advance = []
	for row in advance_:
		if cycle in req_cycle_computation_advance(row):
			advance.append(row)
	return advance