# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FarmerPaymentCycleReport(Document):
	pass


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