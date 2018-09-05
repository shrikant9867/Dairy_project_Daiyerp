from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate,date_diff,add_days
from erpnext.hr.doctype.process_payroll.process_payroll import get_month_details
from dairy_erp.dairy_erp.page.dairy_register_one.dairy_register_one import get_fmcr_list,fetch_farmer_data

@frappe.whitelist()
def get_mis_data(month=None,fiscal_year=None):
	fiscal_year_date = frappe.db.get_values("Fiscal Year",{"name":fiscal_year},["year_start_date","year_end_date"],as_dict=1)
	month_mapper = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
					"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
	
	member_non_member = {'non_member_qty':0,
						'member_qty':0,
						'non_member_count':0,
						'member_count':0
						}
							
	milk_purchase_dict = {}
	milk_quality_data = {}
	formated_and_total_milk = {}
	cattle_feed = {}
	sample_sale_data = {}
	expenses_data = {}
	other_income = {}
	financial_data_dict = {}
	vlcc_addr = ""

	if fiscal_year:
		mis_report_log = frappe.db.get_value("MIS Report Log",{"vlcc_name":frappe.db.get_value("User",frappe.session.user,"company"),
											"fiscal_year":fiscal_year,
											"month":month
											},['name'],as_dict=True)
		if mis_report_log:
			mis_report_doc = frappe.get_doc("MIS Report Log",mis_report_log.get('name'))
			formated_and_total_milk.update({
				'total_milk':mis_report_doc.total_milk,
				'formated_milk':mis_report_doc.formated_milk_new
				})
		else:
			formated_and_total_milk.update({
				'total_milk':0,
				'formated_milk':0
				})

		start_date = get_month_details(fiscal_year,month_mapper[month]).month_start_date
		end_date = get_month_details(fiscal_year,month_mapper[month]).month_end_date
		if month_mapper[month]-1 == 0:
			previous_month_end_date = get_month_details(fiscal_year,12).month_end_date
		if month_mapper[month] == 4:
			previous_month_end_date = get_month_details(fiscal_year,4).month_end_date
		else:
			previous_month_end_date = get_month_details(fiscal_year,month_mapper[month]-1).month_end_date
		
		filters = {
			'month_start_date':start_date,
			'month_end_date':end_date,
			'previous_month_end_date':previous_month_end_date,
			'year_start_date':fiscal_year_date[0].get('year_start_date'),
			'vlcc':frappe.db.get_value("User",frappe.session.user,"company"),
			'from_report':"MIS Report"
		}

		vlcc_addr = frappe.db.get_value("Village Level Collection Centre",
				filters.get('vlcc'),"address_display")
		
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

		cattle_feed = {'month':get_cattle_feed(filters,'month'),
						'upto_month':get_cattle_feed(filters,'upto_month')}

		sample_sale_data = {'month':get_sample_sale_data(filters,'month'),
						'upto_month':get_sample_sale_data(filters,'upto_month')}				
		
		expenses_data = {'month':get_expenses(filters,'month','Trade Expenses'),
						'upto_month':get_expenses(filters,'upto_month','Trade Expenses')}

		other_income = {'month':get_other_income(filters,'month'),
						'upto_month':get_other_income(filters,'upto_month')}

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

		vmcr = milk_purchase_dict.get('vmcr_data')
		fmcr = milk_purchase_dict.get('fmcr_data')
		local_sale_data = milk_purchase_dict.get('local_sale')

		total_1_2_3 = [vmcr[1][0].get('revenue_from_dairy_sale')+
												local_sale_data[1][0].get('local_sale_of_milk')+
												sample_sale_data.get("month")[0].get('sample_own_milk_sale'),
												vmcr[0][0].get('revenue_from_dairy_sale')+
												local_sale_data[0][0].get('local_sale_of_milk')+
												sample_sale_data.get("upto_month")[0].get('sample_own_milk_sale')
								]
		total_5_6 = [fmcr[1][0].get('total_amount_of_milk_purchased')+
											get_expenses(filters,'month','Trade Expenses').get('Trade Expenses')+
											get_expenses(filters,'month','Office Expenses').get('Office Expenses'),
											fmcr[0][0].get('total_amount_of_milk_purchased')+
											get_expenses(filters,'upto_month','Trade Expenses').get('Trade Expenses')+
											get_expenses(filters,'upto_month','Office Expenses').get('Office Expenses')
								]
		gross_profit_4_7 = 	[total_1_2_3[0]-total_5_6[0],total_1_2_3[1]-total_5_6[1]]				
		total_income = [other_income.get('month').get('other_income')+gross_profit_4_7[0],other_income.get('upto_month').get('other_income')+gross_profit_4_7[1]]
		s_total = [get_expenses(filters,'month','Salary').get('Salary')+
					get_expenses(filters,'month','Other Expenses').get('Other Expenses'),
					get_expenses(filters,'upto_month','Salary').get('Salary')+
					get_expenses(filters,'upto_month','Other Expenses').get('Other Expenses')]
		net_profit = [total_income[0]-s_total[0],total_income[1]-s_total[1]]
		if total_5_6[0] != 0 and gross_profit_4_7[0] != 0 and total_5_6[1] != 0 and gross_profit_4_7[1] != 0:
			profit_in = [round((gross_profit_4_7[0]/total_5_6[0])*100,2),round((gross_profit_4_7[1]/total_5_6[1])*100,2)]
		else:
			profit_in = [0,0]
		financial_data_dict = {"revenue_from_dairy_sale":[vmcr[1][0].get('revenue_from_dairy_sale'),vmcr[0][0].get('revenue_from_dairy_sale')],
								"local_sale_of_milk":[local_sale_data[1][0].get('local_sale_of_milk'),local_sale_data[0][0].get('local_sale_of_milk')],
								"sample_own_milk_sale":[sample_sale_data.get("month")[0].get('sample_own_milk_sale'),sample_sale_data.get("upto_month")[0].get('sample_own_milk_sale')],
								"total_1_2_3":total_1_2_3,
								"total_amount_of_milk_purchased":[fmcr[1][0].get('total_amount_of_milk_purchased'),fmcr[0][0].get('total_amount_of_milk_purchased')],
								"trade_expenses_or_office_expenses":[get_expenses(filters,'month','Trade Expenses').get('Trade Expenses')+get_expenses(filters,'month','Office Expenses').get('Office Expenses'),get_expenses(filters,'upto_month','Trade Expenses').get('Trade Expenses')+get_expenses(filters,'upto_month','Office Expenses').get('Office Expenses')],
								"total_5_6":total_5_6,
								"gross_profit_4_7":gross_profit_4_7,
								"Blank_3":"",
								"other_income":other_income,
								"total_income":total_income,
								"Blank_4":"",
								"salary":[get_expenses(filters,'month','Salary').get('Salary'),get_expenses(filters,'upto_month','Salary').get('Salary')],
								"other_expenses":[get_expenses(filters,'month','Other Expenses').get('Other Expenses'),get_expenses(filters,'upto_month','Other Expenses').get('Other Expenses')],
								"s_total":s_total,
								"Blank_5":"",
								"net_profit":net_profit,
								"Blank_6":"",
								"profit_in":profit_in}

	return {"milk_purchase_dict":milk_purchase_dict,
	"member_data":member_non_member,
	'milk_quality':milk_quality_data,
	'formated_and_total_milk':formated_and_total_milk,
	'cattle_feed':cattle_feed,
	'sample_sale_data':sample_sale_data,
	'expenses_data':expenses_data,
	'other_income':other_income,
	'financial_data_dict':financial_data_dict,
	'vlcc_addr':vlcc_addr
	}

def get_fmcr_data_list(filters,date_range):
	filters.update({
		'date_range':date_range,
	})
	fmcr_data = frappe.db.sql("""select
									COALESCE(round(sum(fmcr.milkquantity),2),0) as total_milk_purchase_society,
									COALESCE(round(sum(fmcr.fat*fmcr.milkquantity)/sum(fmcr.milkquantity),2),0) as society_account_fat,
									COALESCE(round(sum(fmcr.snf*fmcr.milkquantity)/sum(fmcr.milkquantity),2),0) as society_account_snf,
									COALESCE(round(avg(fmcr.milkquantity),2),0) as daliy_milk_purchase_society,
									COALESCE(round(sum(fmcr.amount),2),0) as total_amount_of_milk_purchased
								from
									`tabFarmer Milk Collection Record` fmcr
								where
									docstatus = 1 {1}
								""".format(filters.get('fmcr_cond'),get_fmcr_conditions(filters)),as_dict=True,debug=1)
	return fmcr_data


# def get_fmcr_data_list(filters,date_range):
# 	filters.update({
# 		'date_range':date_range,
# 	})
# 	fmcr_data = frappe.db.sql("""select
# 									COALESCE(round(sum(fmcr.milkquantity),2),0) as total_milk_purchase_society,
# 									COALESCE(round(avg(fmcr.fat),2),0) as society_account_fat,
# 									COALESCE(round(avg(fmcr.snf),2),0) as society_account_snf,
# 									COALESCE(round(avg(fmcr.milkquantity),2),0) as daliy_milk_purchase_society,
# 									COALESCE(round(sum(fmcr.amount),2),0) as total_amount_of_milk_purchased
# 								from
# 									`tabFarmer Milk Collection Record` fmcr
# 								where
# 									docstatus = 1 {1}
# 								""".format(filters.get('fmcr_cond'),get_fmcr_conditions(filters)),as_dict=True,debug=0)
# 	return fmcr_data


def get_local_sale_data(filters,date_range):
	filters.update({
		'date_range':date_range
	})
	si_data = frappe.db.sql("""
							select
								COALESCE(round(sum(si_item.qty),2),0) as local_sale,
								COALESCE(round(sum(si.grand_total),2),0) as local_sale_of_milk
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
									COALESCE(round(avg(vmcr.fat),2),0) as dairy_account_fat,
									COALESCE(round(avg(vmcr.snf),2),0) as dairy_account_snf,
									COALESCE(round(sum(vmcr.amount),2),0) as revenue_from_dairy_sale 
								from
									`tabVlcc Milk Collection Record` vmcr
								where
									vmcr.docstatus = 1 and
									{1} """.format(filters.get('vmcr_cond'),get_vmcr_conditions(filters)),as_dict=1,debug=0)
	return vmcr_list

def get_fmcr_conditions(filters):
	print "filters\n\n\n",filters.get('previous_month_end_date')
	conditions = " and 1=1"
	if frappe.session.user != 'Administrator':
		conditions += " and fmcr.associated_vlcc = '{0}'".format(filters.get('vlcc'))
	if filters.get('year_start_date') and filters.get('month_end_date') and filters.get('month_start_date') and filters.get('date_range'):
		if filters.get('date_range') == "upto_month":
			conditions += " and date(fmcr.collectiontime) between '{0}' and '{1}' ".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))
		if filters.get('date_range') == "month":
			conditions += " and date(fmcr.collectiontime) between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date'))
	return conditions

def get_si_conditions(filters):
	conditions = " and 1=1"
	if filters.get('year_start_date') and filters.get('month_end_date') and filters.get('month_start_date') and filters.get('date_range'):
		if filters.get('date_range') == "upto_month":
			conditions += " and si.posting_date between '{0}' and '{1}' ".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))
		if filters.get('date_range') == "month":
			conditions += " and si.posting_date between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date'))
	return conditions

def get_vmcr_conditions(filters):
	conditions = "1=1"
	if filters.get('vlcc'):
		conditions += " and vmcr.associated_vlcc = '{0}' """.format(filters.get('vlcc'))
	if filters.get('year_start_date') and filters.get('month_end_date') and filters.get('month_start_date') and filters.get('date_range'):
		if filters.get('date_range') == "upto_month":
			conditions += " and date(vmcr.collectiontime) between '{0}' and '{1}' ".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))
		if filters.get('date_range') == "month":
			conditions += " and date(vmcr.collectiontime) between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date'))
	return conditions


def get_vmcr_milk_quality_data(filters,status):
	milk_quality = frappe.db.sql("""
									select 
										COALESCE(round(sum(vmcr.milkquantity),2),0) as milk_quantity
									from
										`tabVlcc Milk Collection Record` vmcr
									where
										vmcr.status = '{0}' 	
										and date(vmcr.collectiontime) between '{1}' and '{2}'
										""".format(status,filters.get('month_start_date'),filters.get('month_end_date')),as_dict=1,debug=0)
	return milk_quality[0]

@frappe.whitelist()
def add_formated_milk(filters=None):
	filters = json.loads(filters)
	milk_data = filters.get('milk_data')
	doc = frappe.db.get_value("MIS Report Log",{"vlcc_name":filters.get("vlcc"),
											"fiscal_year":filters.get("fiscal_year"),
											"month":filters.get("month")
											},['name','formated_milk_new'],as_dict=True)
	if doc:
		mis_report_log = frappe.get_doc("MIS Report Log",doc.get('name'))
		if mis_report_log.formated_milk_new != milk_data.get('formated_milk'):
			mis_report_log.formated_milk_old = mis_report_log.formated_milk_new
			mis_report_log.formated_milk_new = milk_data.get('formated_milk')
			mis_report_log.good_milk = milk_data.get('good_milk')
			mis_report_log.bad_milk = milk_data.get('bad_milk')
			mis_report_log.total_milk = milk_data.get('bad_milk') + milk_data.get('good_milk') + milk_data.get('formated_milk')
			mis_report_log.save()
	else:
		mis_report_log = frappe.new_doc("MIS Report Log")
		mis_report_log.vlcc_name = filters.get('vlcc')
		mis_report_log.fiscal_year = filters.get('fiscal_year')
		mis_report_log.month = filters.get('month')
		mis_report_log.formated_milk_new = milk_data.get('formated_milk')
		mis_report_log.formated_milk_old = milk_data.get('formated_milk')
		mis_report_log.good_milk = milk_data.get('good_milk')
		mis_report_log.bad_milk = milk_data.get('bad_milk')
		mis_report_log.total_milk = milk_data.get('bad_milk') + milk_data.get('good_milk') + milk_data.get('formated_milk')
		mis_report_log.save()
	return mis_report_log.name

def get_cattle_feed(filters,cond):
	conditions_pr = " 1=1 and "
	conditions_si = "1=1 and "
	if cond == "month":
		conditions_pr = "pr.posting_date between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date')) 
		conditions_si = "si.posting_date between '{0}' and '{1}'".format(filters.get('month_start_date'),filters.get('month_end_date'))
	if cond == "upto_month":
		conditions_pr += "pr.posting_date between '{0}' and '{1}' ".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))
		conditions_si += "si.posting_date between '{0}' and '{1}'".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))

	pr_data_list = frappe.db.sql("""
			select 
				COALESCE(sum(pr_item.qty),0) as procured
			from
				`tabPurchase Receipt` pr,
				`tabPurchase Receipt Item` pr_item,
				`tabItem Group` item_g
			where
				pr_item.parent = pr.name and
				{0}
				and pr.company = '{1}'
				and item_g.name = "Cattle feed"
				and pr.docstatus = 1
				and	pr.supplier_type in ("Dairy Type","VLCC Local")
		""".format(conditions_pr,filters.get('vlcc')),as_dict=1,debug=0)
	
	cattle_si_data = frappe.db.sql("""
							select
								COALESCE(round(sum(si_item.qty),2),0) as sold_to_farmers
							from 
								`tabSales Invoice` si,
								`tabSales Invoice Item` si_item
							where
								si.customer_or_farmer <> 'Vlcc Local Institution'
								and si_item.parent = si.name
								and si.docstatus = 1 and si.company = '{0}' and
								{1} 
								""".format(filters.get('vlcc'),conditions_si),debug=0,as_dict=1)

	return {'procured':pr_data_list[0]['procured'],'sold_to_farmers':cattle_si_data[0]['sold_to_farmers']}

def get_sample_sale_data(filters,cond):
	conditions_sample_sale = " 1=1 and "
	if cond == "month":
		conditions_sample_sale = "se.posting_date between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date')) 
	if cond == "upto_month":
		conditions_sample_sale += "se.posting_date between '{0}' and '{1}'".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))
	stock_entry = frappe.db.sql("""
								select
									ifnull(round(sum(sed.qty*sed.basic_rate),2),0) as sample_own_milk_sale
								from	
									`tabStock Entry` se,
									`tabStock Entry Detail` sed
								where
									sed.parent = se.name
									and se.is_reserved_farmer = 1
									and se.docstatus = 1
									and se.company = '{0}' and
									{1}
									and se.shift in ('MORNING','EVENING') """.format(filters.get('vlcc'),conditions_sample_sale),as_dict=1,debug=0)
	return stock_entry
	
def get_expenses(filters,cond,expenses_account):
	company_abbr = frappe.db.get_value("Company",{"name":filters.get('vlcc')},"abbr")
	conditions_exp = " 1=1 and "
	if cond == "month":
		conditions_exp = "je.posting_date between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date')) 
	if cond == "upto_month":
		conditions_exp += "je.posting_date between '{0}' and '{1}'".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))

	je_data = frappe.db.sql("""
			select
				ifnull(round(sum(je_item.debit_in_account_currency),2),0) as '{0}'
			from
				`tabJournal Entry` je, `tabJournal Entry Account` je_item
			where
				je.name = je_item.parent and je_item.account = '{1}'
				and je.company = '{2}'
				and je.docstatus = 1 and
				{3}
				""".format(expenses_account,expenses_account+" - "+company_abbr,filters.get('vlcc'),conditions_exp),as_dict=1,debug=0)

	return je_data[0]

def get_other_income(filters,cond):
	camp_office = frappe.db.get_value("Village Level Collection Centre",{'name':filters.get('vlcc')},"camp_office")
	conditions_pi = " 1=1 and "
	conditions_si = " 1=1 and "
	if cond == "month":
		conditions_pi = "pi.posting_date between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date'))
		conditions_si = "si.posting_date between '{0}' and '{1}' ".format(filters.get('month_start_date'),filters.get('month_end_date'))
	if cond == "upto_month":
		conditions_pi += "pi.posting_date between '{0}' and '{1}'".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))
		conditions_si += "si.posting_date between '{0}' and '{1}'".format(filters.get('year_start_date'),filters.get('previous_month_end_date'))
	
	pi_data = frappe.db.sql("""
			select
				ifnull(round(sum(pi.grand_total),2),0)
			from
				`tabPurchase Invoice` pi
			where
				pi.docstatus = 1 and
				pi.supplier_type = "Dairy Type" and
				pi.supplier = '{0}' and
				pi.company = '{1}'
				and {2}
		""".format(camp_office,filters.get('vlcc'),conditions_pi),as_list=1,debug=0)

	si_data = frappe.db.sql("""
				select
					ifnull(round(sum(si.grand_total),2),0)	
				from
					`tabSales Invoice` si
				where
					si.docstatus = 1 and
					si.company = '{0}' and
					si.local_sale = 1 and
					si.customer_or_farmer = 'Farmer' and
					{1}	
		""".format(filters.get('vlcc'),conditions_si),as_list=1,debug=1)

	return {"other_income":si_data[0][0] - pi_data[0][0]}