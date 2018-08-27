# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from frappe import _
from frappe.utils import flt, cstr,nowdate,cint


class VLCCPaymentCycleReport(Document):
	def validate(self):
		# only one vpcr allowed against one vlcc per cycle
		if frappe.db.get_value("VLCC Payment Cycle Report",{'cycle':self.cycle,\
			 'vlcc_name':self.vlcc_name},'name') and self.is_new():
			frappe.throw(_("VPCR has already been generated for this cycle against vlcc <b>{0}</b>".format(self.vlcc_name)))
		if self.collection_to > nowdate() :
			frappe.throw(_("You can generate VPCR after <b>'{0}'</b>".format(self.collection_to)))

	def before_submit(self):
		self.advance_operation()
		self.loan_operation()
		self.update_vpcr()
		if float(self.incentives) != 0:
			self.create_incentive()

	def update_vpcr(self):
		loan_total, loan_si, adavnce_si, advance_total = 0, 0, 0, 0 
		for row in self.vlcc_loan_child:
			si_amt = frappe.get_all("Sales Invoice",fields=['ifnull(sum(grand_total), 0) as amt']\
			,filters={'vlcc_advance_loan':row.loan_id})
			loan_si += si_amt[0].get('amt')
			loan_total += row.principle
		for row in self.vlcc_advance_child:
			si_amt = frappe.get_all("Sales Invoice",fields=['ifnull(sum(grand_total), 0) as amt']\
			,filters={'vlcc_advance_loan':row.adv_id})
			adavnce_si += si_amt[0].get('amt')
			advance_total += row.principle
		self.advance_outstanding = float(advance_total) - float(adavnce_si)
		self.loan_outstanding = float(loan_total) - float(loan_si)
	
	def advance_operation(self):
		flag = False
		for row in self.vlcc_advance_child:
			flag = True
			si_exist = frappe.db.get_value("Sales Invoice",{'cycle_': self.cycle,\
						'vlcc_advance_loan':row.adv_id }, 'name')
			pi_exist = frappe.db.get_value("Purchase Invoice",{'cycle': self.cycle,\
						'vlcc_advance_loan':row.adv_id }, 'name' )
			if not si_exist:
				self.validate_advance(row)
				si = self.create_si(row, "Vlcc Advance", "Advance Emi", row.adv_id)
				pi = self.create_pi(row, "Vlcc Advance", "Advance Emi", row.adv_id)
				self.update_advance(row, si)
			elif si_exist:
				self.update_si(row, self.cycle, si_exist)
				self.update_pi(row, self.cycle, pi_exist)
				self.update_advance_vpcr(row)
		if flag:	
			frappe.msgprint(_("Purchase invoice against incentive AND Sales invoice against loan,advance has been created successfully"))

	def loan_operation(self):
		flag = False
		for row in self.vlcc_loan_child:
			flag = True
			si_exist = frappe.db.get_value("Sales Invoice",{'cycle_': self.cycle,\
						'vlcc_advance_loan':row.loan_id }, 'name')
			pi_exist = frappe.db.get_value("Purchase Invoice",{'cycle': self.cycle,\
						'vlcc_advance_loan':row.loan_id }, 'name')
			if not si_exist:
				self.validate_loan(row)
				si = self.create_si(row,"Vlcc Loan","Loan Emi", row.loan_id)
				pi = self.create_pi(row, "Vlcc Loan", "Loan Emi", row.loan_id)
				self.update_loan(row, si)
			elif si_exist:
				self.update_si(row, self.cycle, si_exist)
				self.update_pi(row, self.cycle, pi_exist)
				self.update_loan_vpcr(row)
		if flag:	
			frappe.msgprint(_("Sales Invoice has been created successfully against Loans"))
	
	def validate_advance(self, row):
		adv_doc = frappe.get_doc("Vlcc Advance",row.adv_id)
		if not row.amount:
			frappe.throw(_("Please Enter amount against <b>{0}</b>".format(row.adv_id)))
		if float(row.amount) > float(row.outstanding):
			frappe.throw(_("Amount can not be greater than  outstanding for <b>{0}</b>".format(row.adv_id)))
		if (int(row.no_of_instalment) + int(adv_doc.extension)) - row.paid_instalment == 1 and \
			(float(row.amount) < float(adv_doc.emi_amount) or float(row.outstanding) != float(adv_doc.emi_amount)):
			frappe.throw(_("Please Use Extension for <b>{0}</b>".format(row.adv_id)))

	def validate_loan(self, row):
		loan_doc = frappe.get_doc("Vlcc Loan",row.loan_id)
		if not row.amount:
			frappe.throw(_("Please Enter amount against <b>{0}</b>".format(row.loan_id)))
		if float(row.amount) > float(row.outstanding):
			frappe.throw(_("Amount can not be greater than  outstanding for <b>{0}</b>".format(row.loan_id)))
		if (int(row.no_of_instalment) + int(loan_doc.extension)) - loan_doc.paid_instalment == 1 and \
			(float(row.amount) < float(loan_doc.emi_amount) or float(row.outstanding) != float(loan_doc.emi_amount)):
			frappe.throw(_("Please Use Extension <b>{0}</b>".format(row.loan_id)))

	def create_si(self, row, type_, item, doc_id):
		company = frappe.db.get_value("Company",{'is_dairy':1},'name')
		si_doc = frappe.new_doc("Sales Invoice")
		si_doc.type = type_
		si_doc.posting_date = self.collection_to
		si_doc.customer = self.vlcc_name
		si_doc.company = company
		si_doc.vlcc_advance_loan = doc_id
		si_doc.cycle_ = self.cycle
		si_doc.append("items",{
			"item_code": item,
			"qty": 1,
			"rate": row.amount,
			"cost_center": frappe.db.get_value("Company", company, "cost_center")
			})
		si_doc.flags.ignore_permissions = True
		si_doc.save()
		si_doc.submit()
		frappe.db.set_value("Sales Invoice", si_doc.name, 'posting_date', self.collection_to)
		gl_stock = frappe.db.get_value("Company", company, 'default_income_account')
		gl_credit = frappe.db.get_value("Company", company, 'default_receivable_account')
		frappe.db.set_value("GL Entry", {"account": gl_stock, "voucher_no": si_doc.name},\
					'posting_date', self.collection_to )
		frappe.db.set_value("GL Entry", {"account": gl_credit, "voucher_no": si_doc.name},\
					'posting_date', self.collection_to )	
		return si_doc.name

	def create_pi(self, row, type_, item, doc_id):
		company = frappe.db.get_value("Company",{'is_dairy':1},'name')
		pi = frappe.new_doc("Purchase Invoice")
		pi.supplier = company
		pi.company = self.vlcc_name
		pi.pi_type = type_
		pi.cycle = self.cycle
		pi.vlcc_advance_loan = doc_id
		pi.append("items",
			{
				"item_code":item,
				"qty": 1,
				"rate": row.amount,
				"cost_center": frappe.db.get_value("Company", company, "cost_center")
			})
		pi.flags.ignore_permissions = True
		pi.save()
		pi.submit()

	def update_si(self, row, cycle, si_no):
		item_row = frappe.db.get_value("Sales Invoice Item", {'parent':si_no}, 'name')
		frappe.db.set_value("Sales Invoice Item", item_row, 'rate', row.amount)
		frappe.db.set_value("Sales Invoice Item", item_row, 'amount', row.amount)
		frappe.db.set_value("Sales Invoice", si_no, 'grand_total', row.amount)
		frappe.db.set_value("Sales Invoice", si_no, 'outstanding_amount', row.amount)
		frappe.db.set_value("Sales Invoice", si_no, 'rounded_total', row.amount)
		frappe.db.set_value("Sales Invoice", si_no, 'posting_date', self.collection_to)
		self.update_gl_entry(si_no, row.amount)

	def update_pi(self, row, cycle, pi_no):
		#overriding PI on vpcr
		item_row = frappe.db.get_value("Purchase Invoice Item", {'parent':pi_no}, 'name')
		frappe.db.set_value("Purchase Invoice Item", item_row, 'rate', row.amount)
		frappe.db.set_value("Purchase Invoice Item", item_row, 'amount', row.amount)
		frappe.db.set_value("Purchase Invoice", pi_no, 'grand_total', row.amount)
		frappe.db.set_value("Purchase Invoice", pi_no, 'outstanding_amount', row.amount)
		frappe.db.set_value("Purchase Invoice", pi_no, 'posting_date', self.collection_to)
		self.update_gl_pi_entry(pi_no, row.amount)

	def update_gl_entry(self, si_no, amount):
		if si_no and amount:
			company = frappe.db.get_value("Company",{'is_dairy':1},'name')
			gl_stock = frappe.db.get_value("Company", company, 'default_income_account')
			gl_credit = frappe.db.get_value("Company", company, 'default_receivable_account')
			frappe.db.set_value("GL Entry", {'account': gl_stock, 'voucher_no': si_no},\
				'credit_in_account_currency', amount)
			frappe.db.set_value("GL Entry", {"account": gl_stock, "voucher_no": si_no},\
					'credit', amount )
			frappe.db.set_value("GL Entry", {"account": gl_credit, "voucher_no": si_no},\
					'debit', amount )
			frappe.db.set_value("GL Entry", {"account": gl_credit, "voucher_no": si_no},\
					'debit_in_account_currency', amount )
			frappe.db.set_value("GL Entry", {"account": gl_stock, "voucher_no": si_no},\
					'posting_date', self.collection_to )
			frappe.db.set_value("GL Entry", {"account": gl_credit, "voucher_no": si_no},\
					'posting_date', self.collection_to )

	def update_gl_pi_entry(self, pi_no, amount):
		if pi_no and amount:
			gl_stock = frappe.db.get_value("Company", self.vlcc_name, 'stock_received_but_not_billed')
			gl_credit = frappe.db.get_value("Company", self.vlcc_name, 'default_payable_account')
			frappe.db.set_value("GL Entry", {'account': gl_stock, 'voucher_no': pi_no},\
				'debit', amount)
			frappe.db.set_value("GL Entry", {'account': gl_stock, 'voucher_no': pi_no},\
				'debit_in_account_currency', amount)
			frappe.db.set_value("GL Entry", {"account": gl_credit, "voucher_no": pi_no},\
					'credit', amount )
			frappe.db.set_value("GL Entry", {"account": gl_credit, "voucher_no": pi_no},\
					'credit_in_account_currency', amount )
			frappe.db.set_value("GL Entry", {"account": gl_stock, "voucher_no": pi_no},\
					'posting_date', self.collection_to )
			frappe.db.set_value("GL Entry", {"account": gl_credit, "voucher_no": pi_no},\
					'posting_date', self.collection_to )
	
	def update_advance_vpcr(self, row):
		instalment = 0
		si_amt = frappe.get_all("Sales Invoice",fields=['ifnull(sum(grand_total), 0) as amt']\
			,filters={'vlcc_advance_loan':row.adv_id})
		adv_doc = frappe.get_doc("Vlcc Advance", row.adv_id)
		adv_doc.outstanding_amount = float(adv_doc.advance_amount) - si_amt[0].get('amt')
		for i in adv_doc.cycle:
			instalment +=1
		adv_doc.paid_instalment = instalment
		if adv_doc.outstanding_amount > 0 :
			adv_doc.emi_amount = (float(adv_doc.outstanding_amount)) / (float(adv_doc.no_of_instalment) + float(adv_doc.extension) - float(adv_doc.paid_instalment))
		if adv_doc.outstanding_amount == 0:
			adv_doc.status = "Paid"
			adv_doc.emi_amount = 0
		adv_doc.flags.ignore_permissions =True
		adv_doc.save()

	def update_loan_vpcr(self, row):
		instalment = 0
		si_amt = frappe.get_all("Sales Invoice",fields=['ifnull(sum(grand_total), 0) as amt']\
			,filters={'vlcc_advance_loan':row.loan_id})
		
		loan_doc = frappe.get_doc("Vlcc Loan", row.loan_id)
		loan_doc.outstanding_amount = float(loan_doc.advance_amount) - si_amt[0].get('amt')
		for i in loan_doc.cycle:
			instalment += 1
		loan_doc.paid_instalment = instalment
		if loan_doc.outstanding_amount > 0:
			loan_doc.emi_amount = (float(loan_doc.outstanding_amount)) / (float(loan_doc.no_of_instalments) + float(loan_doc.extension) - float(loan_doc.paid_instalment))
		if loan_doc.outstanding_amount == 0:
			loan_doc.status = "Paid"
			loan_doc.emi_amount = 0
		loan_doc.flags.ignore_permissions = True
		loan_doc.save()
	
	def update_advance(self, row, si=None):
		instalment = 0
		si_amt = frappe.get_all("Sales Invoice",fields=['ifnull(sum(grand_total), 0) as amt']\
			,filters={'vlcc_advance_loan':row.adv_id})
		adv_doc = frappe.get_doc("Vlcc Advance", row.adv_id)
		adv_doc.append("cycle", {"cycle": self.cycle, "sales_invoice": si})
		adv_doc.outstanding_amount = float(adv_doc.advance_amount) - si_amt[0].get('amt')
		for i in adv_doc.cycle:
			instalment +=1
		adv_doc.paid_instalment = instalment
		if adv_doc.outstanding_amount > 0 :
			adv_doc.emi_amount = (float(adv_doc.outstanding_amount)) / (float(adv_doc.no_of_instalment) + float(adv_doc.extension) - float(adv_doc.paid_instalment))
		if adv_doc.outstanding_amount == 0:
			adv_doc.status = "Paid"
			adv_doc.emi_amount = 0
		adv_doc.flags.ignore_permissions =True
		adv_doc.save()

	def update_loan(self, row, si = None):
		instalment = 0
		si_amt = frappe.get_all("Sales Invoice",fields=['ifnull(sum(grand_total), 0) as amt']\
			,filters={'vlcc_advance_loan':row.loan_id})
		
		loan_doc = frappe.get_doc("Vlcc Loan", row.loan_id)
		loan_doc.append("cycle", {"cycle": self.cycle, "sales_invoice": si})
		loan_doc.outstanding_amount = float(loan_doc.advance_amount) - si_amt[0].get('amt')
		for i in loan_doc.cycle:
			instalment += 1
		loan_doc.paid_instalment = instalment
		if loan_doc.outstanding_amount > 0:
			loan_doc.emi_amount = (float(loan_doc.outstanding_amount)) / (float(loan_doc.no_of_instalments) + float(loan_doc.extension) - float(loan_doc.paid_instalment))
		if loan_doc.outstanding_amount == 0:
			loan_doc.status = "Paid"
			loan_doc.emi_amount = 0
		loan_doc.flags.ignore_permissions = True
		loan_doc.save()

	def create_incentive(self):
		company = frappe.db.get_value("Company",{'is_dairy':1},'name')
		pi = frappe.new_doc("Purchase Invoice")
		pi.supplier = self.vlcc_name
		pi.company = company
		pi.pi_type = "Incentive"
		pi.cycle = self.cycle
		pi.append("items",
			{
				"qty":1,
				"item_code": "Milk Incentives",
				"rate": self.incentives,
				"amount": self.incentives,
				"cost_center": frappe.db.get_value("Company", self.vlcc_name, "cost_center")
			})
		pi.flags.ignore_permissions = True
		pi.save()
		pi.submit()
		
		#updating date for current cycle
		frappe.db.set_value("Purchase Invoice", pi.name, 'posting_date', self.collection_to)
		gl_stock = frappe.db.get_value("Company", company, 'stock_received_but_not_billed')
		gl_credit = frappe.db.get_value("Company", company, 'default_payable_account')
		frappe.db.set_value("GL Entry",{'account': gl_stock,'voucher_no':pi.name}, 'posting_date', self.collection_to)
		frappe.db.set_value("GL Entry",{'account': gl_credit,'voucher_no':pi.name}, 'posting_date', self.collection_to)

@frappe.whitelist()
def get_vmcr(start_date, end_date, vlcc, cycle=None):
	
	vmcr =  frappe.db.sql("""
			select rcvdtime,shift,milkquantity,fat,snf,rate,amount
		from 
			`tabVlcc Milk Collection Record`
		where 
			associated_vlcc = '{0}' and date(rcvdtime) between '{1}' and '{2}'
			""".format(vlcc, start_date, end_date),as_dict=1,debug=0)
	amount = 0
	qty = 0
	for i in vmcr:
		amount += i.get('amount')
		qty += i.get('milkquantity')
	return {
		"vmcr":vmcr, 
		"incentive": get_incentives(amount, qty, vlcc) or 0, 
		"vlcc_child_loan": get_vlcc_loans_child(start_date, end_date, vlcc, cycle),
		"vlcc_child_advance": get_vlcc_advance_child(start_date, end_date, vlcc, cycle),
		"feed_and_fodder": get_mi_raised(start_date, end_date, vlcc)
	}

def get_incentives(amount, qty, vlcc=None):
	if vlcc and amount and qty:
		incentive = 0
		dairy_setting = frappe.get_doc("Dairy Setting")
		if  dairy_setting.enable_per_litre and dairy_setting.per_litre:
			incentive = (float(dairy_setting.per_litre) * float(qty))
		elif not dairy_setting.enable_per_litre and dairy_setting.vlcc_incentives:
			incentive = (float(dairy_setting.vlcc_incentives) * float(amount)) / 100
		return incentive


def get_vlcc_loans_child(start_date, end_date, vlcc, cycle=None):
	loans_ = frappe.db.sql("""
				select name,outstanding_amount,
				emi_amount,no_of_instalments,paid_instalment,advance_amount,
				emi_deduction_start_cycle,extension,date_of_disbursement,vlcc_id
			from 
				`tabVlcc Loan`
			where
				outstanding_amount != 0
				and vlcc_id = '{0}'
				and date_of_disbursement < now() and docstatus =1
				""".format(vlcc),as_dict=1,debug=0)
	loans = []
	for row in loans_:
		req_cycle = req_cycle_computation(row)
		if cycle in req_cycle_computation(row):
			loans.append(row)
	return loans


def get_vlcc_advance_child(start_date, end_date, vlcc, cycle=None):
	advance_ = frappe.db.sql("""
				select name,outstanding_amount,emi_amount,advance_amount,
				no_of_instalment,paid_instalment,emi_deduction_start_cycle,
				extension,date_of_disbursement,vlcc
			from 
				`tabVlcc Advance`
			where
				outstanding_amount != 0
				and vlcc = '{0}'
				and date_of_disbursement < now() and docstatus =1
			""".format(vlcc),as_dict=1,debug=0)
	advance = []
	for row in advance_:
		if cycle in req_cycle_computation_advance(row):
			advance.append(row)
	return advance


def req_cycle_computation(data):
	if data.get('emi_deduction_start_cycle') > 0:

		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabCyclewise Date Computation`
			where
				'{0}' < start_date order by start_date limit {2}""".
			format(data.get('date_of_disbursement'),data.get('vlcc_id'),data.get('emi_deduction_start_cycle')),as_dict=1,debug=0)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		instalment = int(data.get('no_of_instalments')) + int(data.get('extension'))
		if len(not_req_cycl):
			req_cycle = frappe.db.sql("""
					select name
				from
					`tabCyclewise Date Computation`
				where
					'{date}' < start_date and name not in ({cycle}) order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),vlcc = data.get('vlcc_id'),
					instalment = instalment),as_dict=1,debug=0)
			
			req_cycl_list = [i.get('name') for i in req_cycle]
			return req_cycl_list
	elif data.get('emi_deduction_start_cycle') == 0:
		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabCyclewise Date Computation`
			where
				'{0}' < start_date order by start_date limit {2}""".
			format(data.get('date_of_disbursement'),data.get('vlcc_id'),data.get('emi_deduction_start_cycle')),as_dict=1,debug=0)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		
		instalment = int(data.get('no_of_instalments')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select name
				from
					`tabCyclewise Date Computation`
				where
					'{date}' < start_date  order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),vlcc = data.get('vlcc_id'),
					instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list

	elif data.get('emi_deduction_start_cycle') == -1:
		instalment = int(data.get('no_of_instalments')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select
						name
					from
						`tabCyclewise Date Computation`
					where
					'{date}' < end_date
						order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'),instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list
	return []


def req_cycle_computation_advance(data):
	
	if data.get('emi_deduction_start_cycle') > 0:
		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabCyclewise Date Computation`
			where
				'{0}' < start_date  order by start_date limit {1}""".
			format(data.get('date_of_disbursement'),data.get('emi_deduction_start_cycle')),as_dict=1,debug=0)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		if len(not_req_cycl):
			req_cycle = frappe.db.sql("""
					select name
				from
					`tabCyclewise Date Computation`
				where
					'{date}' < start_date and name not in ({cycle}) order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),
					instalment = instalment),as_dict=1)
			
			req_cycl_list = [i.get('name') for i in req_cycle]
			return req_cycl_list

	elif data.get('emi_deduction_start_cycle') == 0:

		not_req_cycl = frappe.db.sql("""
				select name
			from
				`tabCyclewise Date Computation`
			where
				'{0}' < start_date  order by start_date limit {1}""".
			format(data.get('date_of_disbursement'),data.get('emi_deduction_start_cycle')),as_dict=1,debug=0)
		not_req_cycl_list = [ '"%s"'%i.get('name') for i in not_req_cycl ]
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select name
				from
					`tabCyclewise Date Computation`
				where
					'{date}' < start_date  order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'), cycle = ','.join(not_req_cycl_list),
					instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list

	elif data.get('emi_deduction_start_cycle') == -1:
		instalment = int(data.get('no_of_instalment')) + int(data.get('extension'))
		req_cycle = frappe.db.sql("""
					select
						name
					from
						`tabCyclewise Date Computation`
					where
					'{date}' < end_date
						order by start_date limit {instalment}
				""".format(date=data.get('date_of_disbursement'),instalment = instalment),as_dict=1,debug=0)
		req_cycl_list = [i.get('name') for i in req_cycle]
		return req_cycl_list

	return []



def get_mi_raised(start_date, end_date, vlcc):
	grand_total = 0
	sales_invoice = frappe.db.sql("""
					select
						sum(grand_total)
					from
						`tabSales Invoice` si
					where
						si.customer = '{0}'
						and si.posting_date between '{1}' and '{2}'
						and si.type not in ('Vlcc Advance','Vlcc Loan')
						""".format(vlcc,start_date,end_date),as_list=1,debug=0)
	if sales_invoice:
		grand_total = sales_invoice[0][0]
	return grand_total

@frappe.whitelist()
def get_updated_loan(cycle, loan_id=None, amount=None, total = None):
	sum_ = frappe.db.sql("""
				select ifnull(sum(grand_total),0) as total
			from 
				`tabSales Invoice` 
			where 
			vlcc_advance_loan =%s  and cycle_ !=%s""",(loan_id,cycle),as_dict=1,debug=1)
	if len(sum_):
		loan_amount =  float(total) - float(sum_[0].get('total')) - float(amount)
		return loan_amount
	else: return 0

@frappe.whitelist()
def get_updated_advance(cycle, adv_id=None, amount=None, total = None):
	sum_ = frappe.db.sql("""
			select ifnull(sum(grand_total),0) as total
		from 
			`tabSales Invoice` 
		where 
		vlcc_advance_loan =%s  and cycle_ !=%s""",(adv_id,cycle),as_dict=1,debug=1)
	if len(sum_):
		adv_amount =  float(total) - float(sum_[0].get('total')) - float(amount)
		return adv_amount
	else: return 0


@frappe.whitelist()
def get_vpcr_flag():
	return frappe.get_doc("Dairy Setting").as_dict().get('is_vpcr')

@frappe.whitelist()
def get_cycle(doctype,text,searchfields,start,pagelen,filters):
	return frappe.db.sql("""
			select name 
		from
			`tabCyclewise Date Computation`
		where
			 end_date < now() and name like '{txt}'
		""".format(txt= "%%%s%%" % text,as_list=True))