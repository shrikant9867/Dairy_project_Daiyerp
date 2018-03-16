# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class MaterialPriceList(Document):

	def validate(self):

		roles = frappe.get_roles()

		if self.price_template_type and not self.items:
			frappe.throw("Please add items")

		# if 'Dairy Manager' in roles:
	
		if self.is_new():
			self.get_conditions()

			
	def get_conditions(self):

		roles = frappe.get_roles()

		camp_office = self.camp_office if self.camp_office else ""
		company = self.company if 'Vlcc Manager' in roles or 'Vlcc Operator' in roles else ""

		if self.price_template_type == 'Dairy Supplier' and frappe.db.get_value("Price List",{'name':'GTCOB'},"name") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			frappe.throw("Please add items in the existing Material Price List GTCOB")

		elif self.price_template_type == 'VLCC Local Supplier' and frappe.db.get_value("Price List",{'name':'GTVLCCB'},"name") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			frappe.throw("Please add items in the existing Material Price List GTVLCCB")

		elif self.price_template_type == 'CO to VLCC' and frappe.db.get_value("Price List",{'name':'GTCOS'},"name") and ('Dairy Manager' in roles or 'Dairy Operator' in roles) and self.selling == 1:
			frappe.throw("Please add items in the existing Material Price List GTCOS")

		elif self.price_template_type == 'CO to VLCC' and frappe.db.get_value("Price List",{'name':'GTCOVLCCB'},"name") and ('Dairy Manager' in roles or 'Dairy Operator' in roles) and self.buying == 1:
			frappe.throw("Please add items in the existing Material Price List GTCOVLCCB")

		elif self.price_template_type == "VLCC Local Farmer" and frappe.db.get_value("Price List",{'name':'GTFS'},"name") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			frappe.throw("Please add items in the existing Material Price List GTFS")

		elif self.price_template_type == "VLCC Local Customer" and frappe.db.get_value("Price List",{'name':'GTCS'},"name") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			frappe.throw("Please add items in the existing Material Price List GTCS")

			####local prices validation
		

		elif self.price_template_type == "Dairy Supplier" and ('Camp Manager' in roles or 'Camp Operator' in roles) and frappe.db.get_value("Price List",'LCOB' +'-'+camp_office,"name"):
			frappe.throw("Please add items in the existing Material Price List LCOB-{0}".format(camp_office))

		elif self.price_template_type == "VLCC Local Supplier" and frappe.db.get_value("Price List",'LVLCCB'+"-"+company,"name") and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
			frappe.throw("Please add items in the existing Material Price List LVLCCB-{0}".format(company))

		elif self.price_template_type == "CO to VLCC" and frappe.db.exists('Price List', "LCOS" +"-"+camp_office) and ('Camp Manager' in roles or 'Camp Operator' in roles) and self.selling == 1:
			frappe.throw("Please add items in the existing Material Price List LCOS-{0}".format(camp_office))

		elif self.price_template_type == "CO to VLCC" and frappe.db.exists('Price List', "LCOVLCCB" +"-"+camp_office) and ('Camp Manager' in roles or 'Camp Operator' in roles) and self.buying == 1:
			frappe.throw("Please add items in the existing Material Price List LCOVLCCB-{0}".format(camp_office))

		elif self.price_template_type == "VLCC Local Farmer" and frappe.db.exists('Price List', "LFS" +"-"+company ) and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
			frappe.throw("Please add items in the existing Material Price List LFS-{0}".format(company))

		elif self.price_template_type == "VLCC Local Customer" and frappe.db.exists('Price List', "LCS" +"-"+company ) and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
			frappe.throw("Please add items in the existing Material Price List LCS-{0}".format(company))


	def after_insert(self):

		self.create_price_list()

	def on_update(self):
		
		if self.is_update == 1:
			self.update_item_price()
			self.update_reference_buying()

	def create_price_list(self):

		roles = frappe.get_roles()
		camp_office = self.camp_office if self.camp_office else ""
		company = self.company if 'Vlcc Manager' in roles or 'Vlcc Operator' in roles else ""

		if self.price_template_type == "Dairy Supplier" and not frappe.db.exists('Price List', "GTCOB") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			self.price_list_doc(template_name='GTCOB',buying=1,selling=0)
			self.is_update = 1

		elif self.price_template_type == "VLCC Local Supplier" and not frappe.db.exists('Price List', "GTVLCCB") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			self.price_list_doc(template_name='GTVLCCB',buying=1,selling=0)
			self.is_update = 1

		elif self.price_template_type == "CO to VLCC" and not frappe.db.exists('Price List', "GTCOS") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			self.price_list_doc(template_name='GTCOS',buying=0,selling=1,reference_buying='GTCOVLCCB')
			self.create_covlcc_buying(template_name="GTCOVLCCB")
			self.is_update = 1

		elif self.price_template_type == "VLCC Local Farmer" and not frappe.db.exists('Price List', "GTFS") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			self.price_list_doc(template_name='GTFS',buying=0,selling=1)
			self.is_update = 1

		elif self.price_template_type == "VLCC Local Customer" and not frappe.db.exists('Price List', "GTCS") and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
			self.price_list_doc(template_name='GTCS',buying=0,selling=1)
			self.is_update = 1

		#####Local Prices

		elif self.price_template_type == "Dairy Supplier" and not frappe.db.exists('Price List', "LCOB"+"-"+camp_office) and ('Camp Manager' in roles or 'Camp Operator' in roles):
			self.price_list_doc(template_name='LCOB'+"-"+camp_office,buying=1,selling=0)
			self.is_update = 1

		elif self.price_template_type == "VLCC Local Supplier" and not frappe.db.exists('Price List', "LVLCCB"+"-"+company) and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
			self.price_list_doc(template_name='LVLCCB'+"-"+company,buying=1,selling=0)
			self.is_update = 1

		elif self.price_template_type == "CO to VLCC" and not frappe.db.exists('Price List', "LCOS"+"-"+camp_office) and ('Camp Manager' in roles or 'Camp Operator' in roles):
			self.price_list_doc(template_name='LCOS'+"-"+camp_office,buying=0,selling=1,reference_buying="LCOVLCCB"+"-"+camp_office)
			self.create_covlcc_buying(template_name="LCOVLCCB"+"-"+camp_office)
			self.is_update = 1


		elif self.price_template_type == "VLCC Local Farmer" and not frappe.db.exists('Price List', "LFS"+"-"+company) and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
			self.price_list_doc(template_name='LFS'+"-"+company,buying=0,selling=1)
			self.is_update = 1

		elif self.price_template_type == "VLCC Local Customer" and not frappe.db.exists('Price List', "LCS"+"-"+company) and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
			self.price_list_doc(template_name='LCS'+"-"+company,buying=0,selling=1)
			self.is_update = 1

		self.save()


	def update_reference_buying(self):

		item_list = []
		if self.reference_buying:
			reference_buying_doc = frappe.db.get_value("Material Price List",{"price_list":self.reference_buying},"name")
			if reference_buying_doc:
				buying_doc = frappe.get_doc("Material Price List",reference_buying_doc)
				for row_ in buying_doc.items:
					item_list.append(row_.item)
				for row in self.items:
					if row.item not in item_list:
						buying_doc.append("items",{
						"item":row.item,
						"item_name":row.item_name,
						"price":row.price
						})
					else:
						for row_ in buying_doc.items:
							if row.item == row_.item and row.price !=row_.price:
								row_.price = row.price

				buying_doc.flags.ignore_permissions = True
				buying_doc.save()

				item_data = frappe.db.sql("""select item_code from `tabItem Price` where price_list = '{0}'""".format(buying_doc.price_list),as_dict=1)
				item_price_list = [data.get('item_code') for data in item_data]

				for row in buying_doc.items:
					if row.item not in item_price_list:
						item_price = frappe.new_doc("Item Price")
						item_price.price_list = buying_doc.price_list
						item_price.item_code = row.item
						item_price.price_list_rate = row.price
						item_price.flags.ignore_permissions = True
						item_price.save()

					else:
						item = frappe.db.get_value("Item Price",{'price_list':buying_doc.price_list, 'item_code':row.item},'name')
						item_pric_= frappe.get_doc("Item Price",item)
						if item_pric_.price_list_rate != row.price:
							item_pric_.price_list_rate = row.price
							item_pric_.save()
			
	
	def update_item_price(self):

		item_data = frappe.db.sql("""select item_code from `tabItem Price` where price_list = '{0}'""".format(self.price_list),as_dict=1)
		item_price_list = [data.get('item_code') for data in item_data]

		for row in self.items:
			if row.item not in item_price_list:
				item_price = frappe.new_doc("Item Price")
				item_price.price_list = self.price_list
				item_price.item_code = row.item
				item_price.price_list_rate = row.price
				item_price.flags.ignore_permissions = True
				item_price.save()

			else:
				item = frappe.db.get_value("Item Price",{'price_list':self.price_list, 'item_code':row.item},'name')
				item_pric_= frappe.get_doc("Item Price",item)
				if item_pric_.price_list_rate != row.price:
					item_pric_.price_list_rate = row.price
					item_pric_.save()


	def create_item_price(self,price_doc_name):

		for row in self.items:
			item_price = frappe.new_doc("Item Price")
			item_price.price_list = price_doc_name
			item_price.item_code = row.item
			item_price.price_list_rate = row.price
			item_price.flags.ignore_permissions = True
			item_price.save()


	def price_list_doc(self,template_name,buying,selling,reference_buying=None):

		roles = frappe.get_roles()

		price_doc = frappe.new_doc("Price List")
		price_doc.price_list_name = template_name
		price_doc.currency = "INR"
		price_doc.buying = buying
		price_doc.selling = selling
		price_doc.flags.ignore_permissions = True
		price_doc.save()

		self.price_list = price_doc.name
		self.reference_buying = reference_buying
		self.save()
		self.create_item_price(price_doc.name)

	def create_covlcc_buying(self,template_name):

		mpl_doc = frappe.new_doc("Material Price List")
		mpl_doc.price_template_type = "CO to VLCC"
		mpl_doc.is_update = 0
		mpl_doc.buying = 1
		for row in self.items:
			mpl_doc.append("items",{
				"item":row.item,
				"item_name":row.item_name,
				"price":row.price
				})
		mpl_doc.flags.ignore_permissions = True
		mpl_doc.flags.ignore_mandatory = True
		mpl_doc.save()

		price_doc = frappe.new_doc("Price List")
		price_doc.price_list_name = template_name
		price_doc.currency = "INR"
		price_doc.buying = 1
		price_doc.flags.ignore_permissions = True
		price_doc.save()

		mpl_doc.price_list = price_doc.name
		mpl_doc.save()

		self.create_item_price(price_doc.name)



def permission_query_condition(user):

	roles = frappe.get_roles()
	user_doc = frappe.db.get_value("User",{"name":frappe.session.user},['operator_type','company','branch_office'], as_dict =1)
	co = frappe.db.get_value("Village Level Collection Centre",{"name":user_doc.get('company')},"camp_office")

	lcob = "LCOB"+"-"+user_doc.get('branch_office') if user_doc.get('branch_office') else ""
	lcos = "LCOS" +"-"+user_doc.get('branch_office') if user_doc.get('branch_office') else ""

	lvlccb = "LVLCCB" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lfs = "LFS" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lcs = "LCS" +"-"+user_doc.get('company') if user_doc.get('company') and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles) else ""
	lcovlccb = "LCOVLCCB" +"-"+co if co else ""


	if user != 'Administrator' and ('Camp Manager' in roles or 'Camp Operator' in roles):
		return """`tabMaterial Price List`.price_list in ('GTCOB','GTCOS','{0}','{1}') """.format(lcob,lcos)
	elif user != 'Administrator' and ('Vlcc Manager' in roles or 'Vlcc Operator' in roles):
		return """`tabMaterial Price List`.price_list in ('GTVLCCB','GTFS','GTCS','GTCOVLCCB','{0}','{1}','{2}','{3}') """.format(lvlccb,lfs,lcs,lcovlccb)
	elif user != 'Administrator' and 'Vet/AI Technician' in roles:
		return """`tabMaterial Price List`.price_list in ('GTFS','{0}') """.format(lfs)
	elif user != 'Administrator' and ('Dairy Manager' in roles or 'Dairy Operator' in roles):
		return """`tabMaterial Price List`.price_list in ('GTVLCCB','GTFS','GTCS','GTCOVLCCB','GTCOB','GTCOS') """

@frappe.whitelist()
def get_template(template):

	price_doc = frappe.get_doc("Material Price List",template)
	return price_doc
		