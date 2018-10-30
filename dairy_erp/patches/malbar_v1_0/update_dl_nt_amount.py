from __future__ import unicode_literals
import frappe

def execute():
	vmcr_list = frappe.get_all("Vlcc Milk Collection Record",filters={'docstatus': 1,'societyid':'3000','milkquality':'G'},
		fields=['name','milkquality','rate','amount','posting_date','associated_vlcc'])
	for vmcr in vmcr_list:
		dn_name = frappe.db.get_value("Delivery Note",{"vlcc_milk_collection_record":vmcr.get('name')},'name')
		si_name = frappe.db.get_value("Sales Invoice",{"vlcc_milk_collection_record":vmcr.get('name')},'name')
		if frappe.db.exists("Delivery Note", dn_name):
			update_dn_rate(vmcr,dn_name)
			create_dn()

		if frappe.db.exists("Sales Invoice", si_name):
			update_si_rate(vmcr,si_name)
			create_gl_entry(vmcr, si_name)

def update_dn_rate(vmcr, dn):
	frappe.db.sql("""
			update
				`tabDelivery Note Item`
			set
				rate = {0}, amount = {1}
			where
				parent = '{2}'
		""".format(vmcr.get('rate'),vmcr.get('amount'), dn),debug=0)

	frappe.db.sql("""
			update
				`tabDelivery Note`
			set
				total = {0}, net_total = {0}, base_total = {0}, base_net_total = {0},
				base_grand_total = {0}, base_rounded_total = round({0}), grand_total = {0},
				rounded_total = round({0})
			where
				name = '{1}'
		""".format(vmcr.get('amount'), dn),debug=0)



def update_si_rate(vmcr, si):
	frappe.db.sql("""
			update
				`tabSales Invoice Item`
			set
				rate = {0}, amount = {1}
			where
				parent = '{2}'
		""".format(vmcr.get('rate'),vmcr.get('amount'), si),debug=0)

	frappe.db.sql("""
			update
				`tabSales Invoice`
			set
				total = {0}, net_total = {0}, base_total = {0}, base_net_total = {0},
				base_grand_total = {0}, base_rounded_total = round({0}), grand_total = {0},
				rounded_total = round({0})
			where
				name = '{1}'
		""".format(vmcr.get('amount'), si),debug=0)


def create_gl_entry(vmcr, si_name):
	if vmcr.get('amount'):
		company = frappe.get_doc("Company",vmcr.get("associated_vlcc"))
		plant_office = frappe.db.get_value("Village Level Collection Centre",vmcr.get('associated_vlcc'),'plant_office')
		#  Debit
		gl_doc = frappe.new_doc("GL Entry")
		gl_doc.posting_date = vmcr.posting_date
		gl_doc.account = company.default_receivable_account
		gl_doc.party_type = "Customer"
		gl_doc.party = plant_office
		gl_doc.debit = vmcr.get('amount')
		gl_doc.credit = 0.0
		gl_doc.account_currency = 'INR'
		gl_doc.debit_in_account_currency = vmcr.get('amount')
		gl_doc.credit_in_account_currency = 0.0
		gl_doc.against = company.default_income_account
		gl_doc.against_voucher_type = 'Sales Invoice'
		gl_doc.against_voucher = si_name
		gl_doc.voucher_type = 'Sales Invoice'
		gl_doc.voucher_no = si_name
		gl_doc.remarks = 'No Remarks'
		gl_doc.is_opening = 'No'
		gl_doc.is_advance = 'No'
		gl_doc.fiscal_year = frappe.get_doc("Global Defaults").get('current_fiscal_year')
		gl_doc.company = company.name
		gl_doc.flags.ignore_permissions = True
		gl_doc.submit()

		# Credit
		gl_doc = frappe.new_doc("GL Entry")
		gl_doc.posting_date = vmcr.posting_date
		gl_doc.account = company.default_income_account
		gl_doc.cost_center = company.cost_center
		gl_doc.party_type = "Customer"
		gl_doc.party = frappe.db.get_value("Village Level Collection Centre",vmcr.get('associated_vlcc'),'plant_office')
		gl_doc.debit = 0.0
		gl_doc.credit = vmcr.get('amount')
		gl_doc.account_currency = 'INR'
		gl_doc.debit_in_account_currency = 0.0
		gl_doc.credit_in_account_currency = vmcr.get('amount')
		gl_doc.against = plant_office
		gl_doc.voucher_type = 'Sales Invoice'
		gl_doc.voucher_no = si_name
		gl_doc.remarks = 'No Remarks'
		gl_doc.is_opening = 'No'
		gl_doc.is_advance = 'No'
		gl_doc.fiscal_year = frappe.get_doc("Global Defaults").get('current_fiscal_year')
		gl_doc.company = company.name
		gl_doc.flags.ignore_permissions = True
		gl_doc.submit()

def create_dn():
	vmcr_list = frappe.db.sql("""
			select 
				name,associated_vlcc,milktype,rate,amount,milkquantity 
			from 
				`tabVlcc Milk Collection Record` 
			where 
				milkquality = 'G' and societyid = '3000' 
				and docstatus = 1
				and name not in (select vlcc_milk_collection_record 
									from `tabDelivery Note`)
		""",as_dict=1,debug=0)

	for vmcr in vmcr_list:
		make_dn(vmcr)

def make_dn(vmcr):
	warehouse = frappe.db.get_value("Village Level Collection Centre", vmcr.get('associated_vlcc'), 'warehouse')
	cost_center = frappe.db.get_value("Cost Center", {"company": vmcr.get('associated_vlcc')}, 'name')
	delivry_obj = frappe.new_doc("Delivery Note")
	delivry_obj.customer = frappe.db.get_value("Village Level Collection Centre", vmcr.get('associated_vlcc'), "plant_office")
	delivry_obj.vlcc_milk_collection_record = vmcr.get('name')
	delivry_obj.company = vmcr.get('associated_vlcc')
	delivry_obj.append("items",
	{
		"item_code": vmcr.get('milktype')+ ' Milk',
		"item_name": vmcr.get('milktype')+ ' Milk',
		"description": vmcr.get('milktype'),
		"uom": "Litre",
		"qty": vmcr.get('milkquantity'),
		"rate": vmcr.get('rate'),
		"price_list_rate": vmcr.get('rate'),
		"amount": vmcr.get('amount'),
		"warehouse": warehouse,
		"cost_center": cost_center
	})
	delivry_obj.status = "Completed"
	delivry_obj.flags.ignore_permissions = True
	delivry_obj.submit()
	print "Delivery Note created - ",delivry_obj.name
	create_si(delivry_obj,vmcr.get('associated_vlcc'),vmcr,warehouse,cost_center)


def create_si(dn_doc,vlcc,vmcr,warehouse,cost_center):
	si_obj = frappe.new_doc("Sales Invoice")
	si_obj.customer = dn_doc.customer
	si_obj.company = vlcc
	si_obj.vlcc_milk_collection_record = vmcr.get('name')
	si_obj.append("items",{
		"item_code": vmcr.get('milktype')+ ' Milk',
		"qty":vmcr.get('milkquantity'),
		"rate": vmcr.get('rate'),
		"amount": vmcr.get('amount'),
		"warehouse": warehouse,
		"cost_center": cost_center,
		"delivery_note": dn_doc.name
	})
	si_obj.flags.ignore_permissions = True
	si_obj.submit()
	print "Sales Invoice Created - ",si_obj.name