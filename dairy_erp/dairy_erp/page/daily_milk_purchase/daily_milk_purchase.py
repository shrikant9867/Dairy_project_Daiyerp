from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,getdate


@frappe.whitelist()
def get_data(curr_date=None):
	if curr_date:
		curr_date_ = getdate(curr_date)
	else:
		curr_date_ = ""
	
	fmcr_data = frappe.db.sql("""select farmerid,name,milkquantity,
										clr,fat,snf,rate,amount
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
								ifnull(sum(s.grand_total),0) as amt 
					from 
						`tabSales Invoice Item` si,
						`tabSales Invoice` s 
					where 
						s.name= si.parent and 
						s.docstatus = 1 and
						si.item_code in ('COW Milk','BUFFALO Milk') and
						s.local_sale = 1 {0}""".format(local_sale_condn(curr_date_)),as_dict=True)
	
	return {"fmcr_data":fmcr_data,"data":data,"local_sale":local_sale}

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