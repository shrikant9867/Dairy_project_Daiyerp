import frappe
import json
from frappe.utils import has_common


@frappe.whitelist()
def guess_price_list(transaction_type, doc):
	doc = json.loads(doc)
	if transaction_type == "Selling":
		return get_selling_price_list(doc)
	elif transaction_type == "Buying":
		return get_buying_price_list(doc)


def get_selling_price_list(doc, is_vlcc=False, is_camp_office=False):
	# co operator/ co manger - 
	# 	- LCOS-{name} or - GTCOS

	# vlcc operator/ vlcc manger -
	# 	(if Local sale)
	# 		- if farmer 
	# 		    - LFS-{name} or GTFS
	# 		- if Customer
	# 		    - LCS-{name} or GTCS
	# 	else:
	# 		LVLCCS-{name} or GTVLCCS
	roles = frappe.get_roles()
	
	# camp-office user
	if has_common(["Camp Manager", "Camp Operator"], roles or is_camp_office):
		camp_office = doc.get('camp_office')
		local_price = "LCOS-"+camp_office
		if validate_price_list(price_list):
			return local_price
		elif validate_price_list("GTCOS"):
			return "GTCOS"
	
	# vlcc user
	elif has_common(["Vlcc Manager", "Vlcc Operator"], roles or is_vlcc):
		# if local sale
		if doc.get('doctype') == "Sales Invoice" and doc.get('local_sale'):
			if doc.get('customer_or_farmer') == "Vlcc Local Customer":
				local_price = "LCS-"+doc.get('company')
				if validate_price_list(local_price):
					return local_price
				elif validate_price_list("GTCS"):
					return "GTCS"
			elif doc.get('customer_or_farmer') == "Farmer":
				local_price = "LFS-"+doc.get('company')
				if validate_price_list(local_price):
					return local_price
				elif validate_price_list("GTFS"):
					return "GTFS"
		else:
			#local/global vlcc
			if validate_price_list("LVLCCS-"+doc.get('company')):
				return "LVLCCS-"+doc.get('company')
			elif validate_price_list("GTVLCCS"):
				return "GTVLCCS"

def get_buying_price_list(doc, is_vlcc=False, is_camp_office=False):
	# co operator/ co manger - 
	# 		- LCOB-{name} OR GTCOB

	# vlcc operator/ vlcc manger - 
	# 	- if supplier dairy (camp office)
	# 		- LCOVLCCB-{name} or GTCOVLCCB
	# 	- elif local supplier (vlcc supplier)
	# 		- LVLCCB-{name} or GTVLCCB
	roles = frappe.get_roles()

	#camp-office user
	if has_common(["Camp Manager", "Camp Operator"], roles or is_camp_office):
		local_price = "LCOB-"+doc.get('camp_office')
		if validate_price_list(local_price):
			return local_price
		elif validate_price_list("GTCOB"):
			return "GTCOB"
	# vlcc user
	elif has_common(["Vlcc Manager", "Vlcc Operator"], roles or is_vlcc):
		supplier_type = frappe.db.get_value("Supplier", doc.get('supplier'), "supplier_type")
		# co - vlcc
		if supplier_type == "Dairy Type":
			if validate_price_list("LCOVLCCB-"+doc.get('company')):
				return "LCOVLCCB-"+doc.get('company')
			elif validate_price_list("GTCOVLCCB"):
				return "GTCOVLCCB"
		elif supplier_type == "VLCC Local":
			if validate_price_list("LVLCCB-"+doc.get('company')):
				return "LVLCCB-"+doc.get('company')
			elif validate_price_list("GTVLCCB"):
				return "GTVLCCB"

def validate_price_list(price_list):
	if frappe.db.exists("Price List", price_list):
		return True
	else:
		return False