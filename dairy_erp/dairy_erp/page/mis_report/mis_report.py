from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate,date_diff,add_days
from erpnext.hr.doctype.process_payroll.process_payroll import get_month_details
from dairy_erp.dairy_erp.page.dairy_register_one.dairy_register_one import get_fmcr_list,fetch_farmer_data

@frappe.whitelist()
def get_mis_data(month=None,fiscal_year=None):
	fiscal_year_date = frappe.db.get_values("Fiscal Year",{"name":fiscal_year},["year_start_date","year_end_date"],as_dict=1)
	
	month_mapper = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
					"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
	
	member_non_member = {}
	milk_purchase_dict = {}
	milk_quality_data = {}

	if fiscal_year:
		start_date = get_month_details(fiscal_year,month_mapper[month]).month_start_date
		end_date = get_month_details(fiscal_year,month_mapper[month]).month_end_date
	
		filters = {
			'month_start_date':start_date,
			'month_end_date':end_date,
			'year_start_date':fiscal_year_date[0].get('year_start_date'),
			'vlcc':frappe.db.get_value("User",frappe.session.user,"company"),
			'from_report':"MIS Report"
		}
		
		milk_purchase_dict = {
							'fmcr_data':[
							get_fmcr_data_list(filters,'upto_month'),
							get_fmcr_data_list(filters,'month')],
							'local_sale':[
							get_local_sale_data(filters,'upto_month'),
							get_local_sale_data(filters,'month')],
							'vmcr_data':[
							get_vmcr_data_list(filters,'upto_month'),
							get_vmcr_data_list(filters,'month')]
		}

		fmcr_list = get_fmcr_list(filters)
		member_data = fetch_farmer_data(fmcr_list,filters)
		milk_quality_data = {'good':get_vmcr_milk_quality_data(filters,"Accept").get('milk_quantity'),
							'bad':get_vmcr_milk_quality_data(filters,"Reject").get('milk_quantity')}
		
		for row in member_data:
			if member_non_member.get('non_member_qty'):
				member_non_member['non_member_qty'] += member_data[row]['non_member_qty']

			if member_non_member.get('member_qty'):
				member_non_member['member_qty'] += member_data[row]['member_qty']

			if member_non_member.get('non_member_count'):
				member_non_member['non_member_count'] += member_data[row]['non_member_count']

			if member_non_member.get('member_count'):
				member_non_member['member_count'] += member_data[row]['member_count']

			else:
				member_non_member['non_member_qty'] = member_data[row]['non_member_qty']
				member_non_member['member_qty'] = member_data[row]['member_qty']
				member_non_member['non_member_count'] = member_data[row]['non_member_count']
				member_non_member['member_count'] = member_data[row]['member_count']

	return {"milk_purchase_dict":milk_purchase_dict,"member_data":member_non_member,'milk_quality':milk_quality_data}

def get_fmcr_data_list(filters,date_range):
	filters.update({
		'date_range':date_range,
	})
	fmcr_data = frappe.db.sql("""select
									COALESCE(round(sum(fmcr.milkquantity),2),0) as total_milk_purchase_society,
									COALESCE(round(avg(fmcr.fat),2),0) as society_account_fat,
									COALESCE(round(avg(fmcr.snf),2),0) as society_account_snf,
									COALESCE(round(avg(fmcr.milkquantity),2),0) as daliy_milk_purchase_society
								from
									`tabFarmer Milk Collection Record` fmcr
								where
									docstatus = 1 {1}
								""".format(filters.get('fmcr_cond'),get_fmcr_conditions(filters)),as_dict=True,debug=0)
	return fmcr_data


def get_local_sale_data(filters,date_range):
	filters.update({
		'date_range':date_range
	})
	si_data = frappe.db.sql("""
							select
								COALESCE(round(sum(si_item.qty),2),0) as local_sale
							from 
								`tabSales Invoice` si,
								`tabSales Invoice Item` si_item
							where
								si.local_sale = 1 and
								si_item.item_code in ("COW Milk","BUFFALO Milk") and
								si.customer_or_farmer in ('Vlcc Local Customer','Vlcc Local Institution')
								and si_item.parent = si.name
								and si.docstatus = 1 and si.company = '{0}'
								{1}""".format(filters.get('vlcc'),get_si_conditions(filters)),
								filters,debug=0,as_dict=1)
	return si_data

def get_vmcr_data_list(filters,date_range):
	filters.update({
		'date_range':date_range,
	})
	vmcr_list = frappe.db.sql("""
								select
									COALESCE(round(sum(vmcr.milkquantity),2),0) as total_milk_purchase_dairy,
									COALESCE(round(avg(vmcr.fat),0),2) as dairy_account_fat,
									COALESCE(round(avg(vmcr.snf),0),2) as dairy_account_snf 
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									{1} """.format(filters.get('vmcr_cond'),get_vmcr_conditions(filters)),as_dict=1,debug=0)
	return vmcr_list

def get_fmcr_conditions(filters):
	conditions = " and 1=1"
	if frappe.session.user != 'Administrator':
		conditions += " and fmcr.associated_vlcc = '{0}'".format(filters.get('vlcc'))
	if filters.get('year_start_date') and filters.get('month_end_date') and filters.get('month_start_date') and filters.get('date_range'):
		if filters.get('date_range') == "upto_month":
			conditions += " and date(fmcr.collectiondate) between '{0}' and '{1}' ".format(filters.get('year_start_date'),filters.get('month_end_date'))
		if filters.get('date_range') == "month":
			conditions += " and date(fmcr.collectiondate) between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date'))
	return conditions

def get_si_conditions(filters):
	conditions = " and 1=1"
	if filters.get('year_start_date') and filters.get('month_end_date') and filters.get('month_start_date') and filters.get('date_range'):
		if filters.get('date_range') == "upto_month":
			conditions += " and si.posting_date between '{0}' and '{1}' ".format(filters.get('year_start_date'),filters.get('month_end_date'))
		if filters.get('date_range') == "month":
			conditions += " and si.posting_date between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date'))
	return conditions

def get_vmcr_conditions(filters):
	conditions = "1=1"
	if filters.get('operator_type') == "VLCC":
		conditions += " and vmcr.associated_vlcc = '{0}' """.format(filters.get('vlcc'))
	if filters.get('year_start_date') and filters.get('month_end_date') and filters.get('month_start_date') and filters.get('date_range'):
		if filters.get('date_range') == "upto_month":
			conditions += " and date(vmcr.collectiondate) between '{0}' and '{1}' ".format(filters.get('year_start_date'),filters.get('month_end_date'))
		if filters.get('date_range') == "month":
			conditions += " and date(vmcr.collectiondate) between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date'))
	return conditions


def get_vmcr_milk_quality_data(filters,status):
	milk_quality = frappe.db.sql("""
									select 
										COALESCE(round(sum(vmcr.milkquantity),2),0) as milk_quantity
									from
										`tabVlcc Milk Collection Record` vmcr
									where
										vmcr.status = '{0}' 	
										and date(vmcr.collectiondate) between '{1}' and '{2}'
										""".format(status,filters.get('month_start_date'),filters.get('month_end_date')),as_dict=1,debug=0)
	return milk_quality[0]