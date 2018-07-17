from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate


@frappe.whitelist()
def get_data(curr_date=None):
	non_member_count,member_count,non_member_qty,member_qty,member_amt,non_member_amt = 0 , 0 , 0, 0,0,0
	curr_date_ = getdate(curr_date) if curr_date else ""
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")
	vlcc_addr = frappe.db.get_value("Village Level Collection Centre",vlcc,"address_display")
	
	fmcr_data = frappe.db.sql("""select farmerid,name,milkquantity,
										clr,fat,snf,rate,amount,societyid
								from
									`tabFarmer Milk Collection Record`
								where 
									docstatus = 1 {0}
								""".format(get_conditions(curr_date_)),as_dict=True)
	data = frappe.db.sql("""select count(name) as count,
								ifnull(sum(milkquantity),0) as qty ,
								ifnull(round(avg(fat),2),0) as avg_fat,
								ifnull(round(avg(clr),2),0) as avg_clr,
								ifnull(round(avg(snf),2),0) as avg_snf,
								ifnull(round(avg(rate),2),0) as avg_rate 
							from 
								`tabFarmer Milk Collection Record`
							where 
								docstatus = 1 {0}
		""".format(get_conditions(curr_date_)),as_dict=True)
	local_sale = frappe.db.sql("""select ifnull(sum(si.qty),0) as qty, 
								ifnull(sum(si.amount),0) as amt 
					from 
						`tabSales Invoice Item` si,
						`tabSales Invoice` s 
					where 
						s.name= si.parent and 
						s.docstatus = 1 and
						si.item_code in ('COW Milk','BUFFALO Milk') and
						s.local_sale = 1 {0}""".format(local_sale_condn(curr_date_)),as_dict=True)
	if len(fmcr_data):
		farmer_list = [i.get('farmerid') for i in fmcr_data]

		if farmer_list:
			for farmer in set(farmer_list):
				farmer_id = frappe.db.get_value("Farmer",farmer,["registration_date","is_member"],as_dict=1)
				months_to_member = frappe.db.get_value("VLCC Settings",{"vlcc":vlcc},"months_to_member")
				if farmer_id and months_to_member:
					date_ = add_months(getdate(farmer_id.get('registration_date')),months_to_member)
					if getdate() < date_  and not farmer_id.get('is_member'):
						non_member_count += 1
						non_member_data = frappe.db.sql("""select ifnull(sum(milkquantity),0) as qty ,
											ifnull(sum(amount),0) as amt 
									from 
										`tabFarmer Milk Collection Record`
									where docstatus = 1 and farmerid = '{0}' {1} 
						""".format(farmer,get_conditions(curr_date_)),as_dict=1)
						non_member_qty += non_member_data[0].get('qty')
						non_member_amt += non_member_data[0].get('amt')
				if farmer_id.get('is_member'):
					member_count += 1
					member_data = frappe.db.sql("""select ifnull(sum(milkquantity),0) as qty ,
											ifnull(sum(amount),0) as amt 
									from 
										`tabFarmer Milk Collection Record`
									where docstatus = 1 and farmerid = '{0}' {1}
						""".format(farmer,get_conditions(curr_date_)),as_dict=1)
					member_qty += member_data[0].get('qty')
					member_amt += member_data[0].get('amt')

	return {
			"fmcr_data":fmcr_data,
			"data":data,
			"local_sale":local_sale,
			"vlcc":vlcc,
			"vlcc_addr":vlcc_addr,
			"non_member_count":non_member_count if non_member_count else 0,
			"member_count":member_count if member_count else 0,
			"non_member_qty":non_member_qty if non_member_qty else 0,
			"member_qty":member_qty if member_qty else 0,
			"member_amt":round(member_amt,2) if member_amt else 0,
			"non_member_amt":round(non_member_amt,2) if non_member_amt else 0
			}

def get_conditions(curr_date=None):
	conditions = " and 1=1"
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")

	if frappe.session.user != 'Administrator':
		conditions += " and associated_vlcc = '{0}'".format(vlcc)
	if curr_date:
		conditions += " and date(rcvdtime) = '{0}'".format(curr_date)

	return conditions

def local_sale_condn(curr_date=None):
	conditions = " and 1=1"
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")

	if frappe.session.user != 'Administrator':
		conditions += " and s.company = '{0}'".format(vlcc)
	if curr_date:
		conditions += " and s.posting_date = '{0}'".format(curr_date)

	return conditions