from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr,nowdate,cint,get_datetime, now_datetime,add_months,getdate,date_diff,add_days

@frappe.whitelist()
def get_fmcr_data(vlcc=None,cycle=None,farmer=None):
	cyclewise_computation = frappe.db.get_values("Cyclewise Date Computation",{"name":cycle},["start_date","end_date"],as_dict=1)
	start_date = cyclewise_computation[0]['start_date']
	end_date = cyclewise_computation[0]['end_date']
	fmcr_morning_list = []
	fmcr_evening_list = []
	
	filters = {
				'start_date':start_date,
				'end_date':end_date,
				'vlcc':vlcc,
				'farmer':farmer
				}
	l = get_fmcr(filters)
	
	dict1 = {}
	for fmcr in l:
		if dict1 and str(fmcr[0])+"#"+str(fmcr[7]) in dict1:
			dict1[str(fmcr[0])+"#"+str(fmcr[7])].append(fmcr)
		else:
			dict1[str(fmcr[0])+"#"+str(fmcr[7])] = [fmcr]

	final_ = []
	for k,v in dict1.items():
		if len(dict1.get(k.split('#')[0]+'#'+'MORNING', [])) and len(dict1.get(k.split('#')[0]+'#'+'EVENING', [])):
			# print "inside both",k,v
			# if len(dict1.get(k.split('#')[0]+'#'+'MORNING')) == len(dict1.get(k.split('#')[0]+'#'+'EVENING')):
			final_.append(dict1.get(k.split('#')[0]+'#'+'MORNING').pop(0) + dict1.get(k.split('#')[0]+'#'+'EVENING').pop(0))
			# print dict1,"inside cond 1____________________\n\n\n"
			# dict1[k.split('#')[0]+'#'+'MORNING'].pop(0)
			# dict1[k.split('#')[0]+'#'+'EVENING'].pop(0)
		elif len(dict1.get(k.split('#')[0]+'#'+'MORNING',[])):#and not len(dict1.get(k.split('#')[0]+'#'+'EVENING')):
			# print "inside M",k,v
			l = len(dict1.get(k.split('#')[0]+'#'+'MORNING',[]))
			for i in range(l):
				final_.append(dict1.get(k.split('#')[0]+'#'+'MORNING').pop(0) + ['-',0,'-','-','-','-',0,'-'])
			dict1[k.split('#')[0]+'#'+'MORNING'] = []
			# print dict1,"inside cond 2________________________\n\n\n"
			# dict1[k.split('#')[0]+'#'+'MORNING'].pop(0)
		elif len(dict1.get(k.split('#')[0]+'#'+'EVENING', [])) :#and not len(dict1.get(k.split('#')[0]+'#'+'MORNING')):
			# if k.split('#')[0] == '2018-07-01':
				# print "\n\n\ninside E",k,v, "\n\n\n"
			# final_.append(dict1.get(k.split('#')[0]+'#'+'EVENING').pop(0) + ['',''])
			l = len(dict1.get(k.split('#')[0]+'#'+'EVENING',[]))
			for i in range(l):
				final_.append([k.split('#')[0]+'#'+'EVENING',0,'-','-','-','-',0,'-'] + dict1.get(k.split('#')[0]+'#'+'EVENING').pop(0))
			dict1[k.split('#')[0]+'#'+'EVENING'] = []
			# print dict1,"inside cond 3____________________\n\n\n"
			# if k.split('#')[0] == '2018-07-01':
				# print "---> after --",dict1.get(k.split('#')[0]+'#'+'EVENING'), "\n\n"
			# dict1[k.split('#')[0]+'#'+'EVENING'].pop(0)
		else:
			print "inside else\n\n\n\n\n\n",k
			
	# print "\n\n\n\n\n",dict1,"dict final remain","\n\n\n\n\n"
	# print final_,"final_____________________"

	print final_,"before___________"
	for row in final_:
		# print row,"row_________"
		# print "values___________________",row[7]
		# print "values___________________",row[8]
		# print "values___________________",row[15]
		# print row,"after remove"
		del row[7]
		del row[8]
		if len(row) == 15:
			del row[15]
		# print row,"_row__"
		# row.insert(13,row[0] + row[7])
		# row.insert(14,row[5] + row[11])
	print final_,"after __________final_______________________"
	# final_.append(['',0,'','','','',0,0,'','','','',0,0,0])
	
	# for row in final_:
	# 	final_[-1][1] += row[1]
	# 	final_[-1][6] += row[6]
	# 	final_[-1][7] += row[7]
	# 	final_[-1][12] += row[12]
	# 	final_[-1][13] += row[13]
	# 	final_[-1][14] += row[14]	
	# print final_,"final_\n\n\n\n\n\n"
	
	# for shift in ["MORNING","EVENING"]:
	# 	if shift == "MORNING":
	# 		filters.update({
	# 			'shift':"MORNING"
	# 			})
	# 		fmcr_morning_list = get_fmcr(filters)
	# 	if shift == "EVENING":
	# 		filters.update({
	# 			'shift':"EVENING"
	# 			})
	# 		fmcr_evening_list = get_fmcr(filters)	
	
	# morning = make_table_row(fmcr_morning_list,filters)
	# evening = make_table_row(fmcr_evening_list,filters)
	# print morning,"morning_____________"
	# print evening,"evening_____________"
	# total = []
	# qty = []
	# amount = []
	# for row in range(2):
	# 	qty.append(get_qty_and_amount_total(morning,1))
	# 	amount.append(get_qty_and_amount_total(evening,6))
	# print qty,"qty___________________"
	# print amount,"amount_________________"
	# return {'morning':morning,'evening':evening}

def get_qty_and_amount_total(data,value):
	print data,"data________________________________"
	# for row in data:
	# 	for row_ in row:

def get_fmcr(filters):	
	fmcr_list = frappe.db.sql("""select
									date(fmcr.collectiondate),
									fmcr.milkquantity,
									fmcr.milktype,
									fmcr.fat,
									fmcr.snf,
									fmcr.rate,
									fmcr.amount,
									fmcr.shift
						from
							`tabFarmer Milk Collection Record` fmcr
						where
							{0}
							group by fmcr.collectiondate,fmcr.shift,fmcr.name
		""".format(get_conditions(filters)),as_list=1,debug=1)
	print fmcr_list,"fmcr_list_______________________"
	return fmcr_list

def get_conditions(filters):
	if filters:
		conditions = "fmcr.collectiondate between '{0}' and '{1}' \
					and fmcr.farmerid = '{2}'\
					and fmcr.associated_vlcc = '{3}'".format(filters.get('start_date'),filters.get('end_date'),filters.get('farmer'),filters.get('vlcc'))
		return conditions

# def get_conditions(filters):
# 	if filters:
# 		conditions = "fmcr.collectiondate between '{0}' and '{1}' \
# 					and fmcr.shift = '{2}'\
# 					and fmcr.farmerid = '{3}'\
# 					and fmcr.associated_vlcc = '{4}'".format(filters.get('start_date'),filters.get('end_date'),filters.get('shift'),filters.get('farmer'),filters.get('vlcc'))
# 		return conditions


# def make_table_row(fmcr_list,filters):
# 	day_diff = date_diff(filters.get('end_date'),filters.get('start_date'))
# 	cycle_range = day_diff + 1
# 	_fmcr_list = []
# 	for c in range(cycle_range):
# 		date = add_days(filters.get('start_date'),c)
# 		if check_fmcr(date,fmcr_list):
# 			_fmcr_list.append(check_fmcr(date,fmcr_list)) 
# 		else:
# 			_fmcr_list.append([['-','-','-','-','-','-','-']])
# 	return _fmcr_list

# def check_fmcr(date,fmcr_list):
# 	_fmcr_list = []
# 	for fmcr in fmcr_list:
# 		if fmcr[0] == date:
# 			_fmcr_list.append(fmcr)
# 	return _fmcr_list	