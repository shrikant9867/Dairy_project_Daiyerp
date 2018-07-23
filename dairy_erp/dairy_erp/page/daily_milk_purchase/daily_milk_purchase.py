from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate


@frappe.whitelist()
def get_data(curr_date=None):
	non_member_count,member_count,non_member_qty,member_qty,member_amt,non_member_amt = 0 , 0 , 0, 0,0,0
	curr_date_ = getdate(curr_date) if curr_date else ""
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")
	vlcc_addr = frappe.db.get_value("Village Level Collection Centre",
				vlcc,"address_display")

	fmcr_stock_data = []
	
	fmcr_data = frappe.db.sql("""select farmerid,name,round(milkquantity,2) as milkquantity,
										clr,fat,snf,rate,round(amount,2) as amount,societyid
								from
									`tabFarmer Milk Collection Record`
								where 
									docstatus = 1 {0}
								""".format(get_conditions(curr_date_)),as_dict=True,debug=0)

	resv_farmer_data =  frappe.db.sql("""select s.farmer_id as farmerid,
					s.name as name,ifnull(round(se.qty,2),0) as milkquantity,
					s.fat,s.snf,s.clr,se.basic_rate as rate,round(se.amount,2) as amount
					from 
						`tabStock Entry` s, `tabStock Entry Detail` se 
					where 
						s.name = se.parent
						and s.docstatus = 1 and 
						s.is_reserved_farmer = 1 
						{0}""".format(local_sale_condn(curr_date_)),as_dict=True,debug=0)

	fmcr = fmcr_data[0].get('name') if fmcr_data and fmcr_data[0].get('name') else []
	resv_farmer = resv_farmer_data[0].get('name') if resv_farmer_data and resv_farmer_data[0].get('name') else []
	
	if fmcr and resv_farmer:
		for fmcr in fmcr_data:
			fmcr_stock_data.append(fmcr)
		for resv_farmer in resv_farmer_data:
			fmcr_stock_data.append(resv_farmer)
	elif fmcr:
		for fmcr in fmcr_data:
			fmcr_stock_data.append(fmcr)
	elif resv_farmer:
		for resv_farmer in resv_farmer_data:
			fmcr_stock_data.append(resv_farmer)

	avg_data = get_avg_data(fmcr_stock_data)
	local_sale_data = get_local_sale_data(curr_date_)
	dairy_sale_qty = flt(avg_data.get('milkqty')) - flt(local_sale_data.get('qty'))
	return {
			"fmcr_stock_data":fmcr_stock_data,
			"avg_data":avg_data,
			"local_sale_data":local_sale_data,
			"member_data":guess_member(fmcr_stock_data,curr_date_),
			"vlcc":vlcc,
			"vlcc_addr":vlcc_addr,
			"dairy_sale_qty":round(dairy_sale_qty,2)
		}
		
def get_avg_data(fmcr_stock_data):
	avg_data = {}
	count = flt(len(fmcr_stock_data))
	milkqty,fat,snf,clr,rate,avg_fat,avg_snf,avg_clr,avg_rate = 0,0,0,0,0,0,0,0,0
	if fmcr_stock_data:
		for fmcr_stock in fmcr_stock_data:
			milkqty += fmcr_stock.get('milkquantity')
			fat += flt(fmcr_stock.get('fat'))
			snf += flt(fmcr_stock.get('snf'))
			clr += flt(fmcr_stock.get('clr'))
			rate += flt(fmcr_stock.get('rate'))
			avg_fat = flt(fat/count)
			avg_snf = flt(snf/count)
			avg_clr = flt(clr/count)
			avg_rate = flt(rate/count)

		avg_data.update({
			"count":count,"milkqty":round(milkqty,2),
			"avg_fat":round(avg_fat,2),"avg_snf":round(avg_snf,2),
			"avg_clr":round(avg_clr,2),"avg_rate":round(avg_rate,2)})
	return avg_data

def get_local_sale_data(curr_date_):

	local_sale_data = {}
	local_sale =  frappe.db.sql("""select ifnull(sum(si.qty),0) as qty,  
									ifnull(sum(si.amount),0) as amt
			from 
				`tabSales Invoice Item` si,
				`tabSales Invoice` s 
			where 
				s.name= si.parent and 
				s.docstatus = 1 and
				si.item_code in ('COW Milk','BUFFALO Milk') and
				s.local_sale = 1 {0}""".format(local_sale_condn(curr_date_)),as_dict=True)

	if local_sale and local_sale[0].get('qty'):
		local_sale_data.update({"qty":round(local_sale[0].get('qty'),2),
								"amt":round(local_sale[0].get('amt'),2)})
	return local_sale_data

	
def guess_member(fmcr_data,curr_date_):

	member_dict = {}

	non_member_count,member_count,non_member_qty,member_qty,member_amt,non_member_amt = 0 , 0 , 0, 0,0,0
	vlcc = frappe.db.get_value("User",frappe.session.user,"company")
	
	farmer_list = [data.get('farmerid') for data in fmcr_data]

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
					non_member_qty += flt(non_member_data[0].get('qty'))
					non_member_amt += flt(non_member_data[0].get('amt'))
			if farmer_id and farmer_id.get('is_member'):
				member_count += 1
				member_data = frappe.db.sql("""select ifnull(sum(milkquantity),0) as qty ,
										ifnull(sum(amount),0) as amt 
								from 
									`tabFarmer Milk Collection Record`
								where docstatus = 1 and farmerid = '{0}' {1}
					""".format(farmer,get_conditions(curr_date_)),as_dict=1)
				member_qty += flt(member_data[0].get('qty'))
				member_amt += flt(member_data[0].get('amt'))

	 	member_dict.update({"non_member_count":non_member_count,
					"member_count":member_count,
					"non_member_qty":round(non_member_qty,2),
					"member_qty":round(member_qty,2),
					"member_amt":round(member_amt,2),
					"non_member_amt":round(non_member_amt,2)})

	return member_dict

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