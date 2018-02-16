import frappe
from frappe import unscrub
from datetime import datetime, timedelta
from frappe.utils import add_days, nowdate
from frappe.contacts.doctype.address.address import get_address_display


@frappe.whitelist()
def get_vlcc_data():
	data = frappe._dict()
	vlcc = frappe.db.get_value("User", frappe.session.user, "company")
	if not vlcc:
		return {}
	data.addresses = get_address(vlcc);
	data.total_summery = get_total_counts(vlcc);
	data.farmer = get_farmers(vlcc)
	data.supplier = get_suppliers(vlcc)
	return data

def get_address(vlcc):
	fields = ["chilling_centre", "plant_office", "camp_office"]
	vlcc_data = frappe.db.get_value("Village Level Collection Centre",
		vlcc, fields, as_dict=True)
	vlcc_data["head_office"] = frappe.db.get_value("Address", {
		"address_type": "Head Office"}, "name")
	addresses = []
	for addr_type, addr in vlcc_data.iteritems():
		addresses.append({
			"label": unscrub(addr_type),
			"doctype": "Address",
			"records": [{addr:get_address_display(addr)}],
			"add_type": unscrub(addr_type),
		})
	return addresses

def get_total_counts(vlcc):
	def _query(vlcc,start, end):
		return """
			select 
				ifnull(sum(milkquantity), 0) as milk_qty, 
				ifnull(sum(amount), 0) as milk_amt 
			from 
				`tabFarmer Milk Collection Record` 
			where 
				associated_vlcc = '%s' and 
				date(rcvdtime) between '%s' and '%s'
		"""%(vlcc, start, end)
	
	# Indents Pending
	material_req = frappe.db.get_value("Material Request", {
		"company": vlcc}, "count(name) as count")

	this_start, this_end, last_start, last_end = get_start_end_dates()

	# Milk procured & amount
	this_week_milk = frappe.db.sql(_query(vlcc, this_start, this_end),as_dict=True)
	last_week_milk = frappe.db.sql(_query(vlcc, last_start, last_end),as_dict=True)

	return {
		"this_milk_qty": this_week_milk[0].get('milk_qty'), 
		"this_milk_amt": this_week_milk[0].get('milk_amt'), 
		"last_milk_qty": last_week_milk[0].get('milk_qty'), 
		"last_milk_amt": last_week_milk[0].get('milk_amt'), 
		"pending_indent": material_req
	}

def get_start_end_dates():
	# get last and this week start-end dates
	dt = datetime.strptime(nowdate(), '%Y-%m-%d')
	start = dt - timedelta(days=dt.weekday())
	this_start = start.strftime('%Y-%m-%d')
	this_end = add_days(this_start, 6)
	last_start,last_end = add_days(this_start, -7), add_days(this_start, -1)
	return this_start, this_end, last_start, last_end

def get_farmers(vlcc):
	farmers = frappe.get_all('Farmer', 
		filters={'vlcc_name': vlcc}, 
		fields = ["name", "address"],
		order_by="modified desc",
		limit_page_length=2
	)
	return format_data("Farmer", farmers)

def get_suppliers(vlcc):
	suppliers =  frappe.db.sql("""
		select supp.name as name, addr.parent as address
		from `tabSupplier` supp left join `tabDynamic Link` addr
		on addr.link_name = supp.name and addr.link_doctype='Supplier' 
		where supp.company = '%s' limit 2
	"""%(vlcc), as_dict=True)
	return format_data("Supplier", suppliers)

def format_data(dt, data):
	return {
		"label": dt,
		"records": [ { row.get('name'): get_address_display(row.get('address')) for row in data } ],
		"doctype": dt,
		"add_type": ""
	}
