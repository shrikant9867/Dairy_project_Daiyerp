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
	
		# 	if self.is_new():
		# 		self.get_conditions()

			
	def get_conditions(self):


		if self.price_template_type == 'Dairy Supplier' and frappe.db.get_value("Price List",{'name':'GTCOB'},"name"):
			frappe.throw("GTCOB exits")

		elif self.price_template_type == 'VLCC Local Supplier' and frappe.db.get_value("Price List",{'name':'GTVLCCB'},"name"):
			frappe.throw("GTVLCCB exits")
			# conditions = "where price_template_type = '{0}' and buying = 1".format(self.price_template_type)

		# elif self.price_template_type == 'CO to VLCC' and frappe.db.exists("Material Price List",'GTCOS'):
		# 	frappe.throw("GTCOS exits")

		# elif self.price_template_type == 'CO to VLCC' and frappe.db.get_value("Price List",{'name':'GTCOVLCCB'},"name"):
		# 	frappe.throw("GTCOVLCCB exits")
			# conditions = "where price_template_type = '{0}' and buying = 1".format(self.price_template_type)

			# conditions = "where price_template_type = '{0}' and selling = 1".format(self.price_template_type)

		elif self.price_template_type == "VLCC Local Farmer" and frappe.db.get_value("Price List",{'name':'GTFS'},"name"):
			frappe.throw("GTFS exits")

		elif self.price_template_type == "VLCC Local Customer" and frappe.db.get_value("Price List",{'name':'GTCS'},"name"):
			frappe.throw("GTCS exits")
			
		
		# return conditions


	def after_insert(self):

		self.create_price_list()

	def on_update(self):
		pass
		# self.update_item_price()

	def create_price_list(self):

		roles = frappe.get_roles()

		if self.price_template_type == "Dairy Supplier" and not frappe.db.exists('Price List', "GTCOB"):
			self.price_list_doc(template_name='GTCOB',buying=1,selling=0)

		elif self.price_template_type == "VLCC Local Supplier" and not frappe.db.exists('Price List', "GTVLCCB"):
			self.price_list_doc(template_name='GTVLCCB',buying=1,selling=0)

		elif self.price_template_type == "CO to VLCC" and not frappe.db.exists('Price List', "GTCOS"):
			self.price_list_doc(template_name='GTCOS',buying=0,selling=1)
			self.create_covlcc_buying(template_name="GTCOVLCCB")

		elif self.price_template_type == "VLCC Local Farmer" and not frappe.db.exists('Price List', "GTFS"):
			self.price_list_doc(template_name='GTFS',buying=0,selling=1)

		elif self.price_template_type == "VLCC Local Customer" and not frappe.db.exists('Price List', "GTCS"):
			self.price_list_doc(template_name='GTCS',buying=0,selling=1)

		#####Local Prices

		elif self.price_template_type == "Dairy Supplier" and not frappe.db.exists('Price List', "LCOB"):
			self.price_list_doc(template_name='LCOB',buying=1,selling=0)

		elif self.price_template_type == "VLCC Local Supplier" and not frappe.db.exists('Price List', "GTVLCCB"):
			self.price_list_doc(template_name='LVLCCB',buying=1,selling=0)

		elif self.price_template_type == "CO to VLCC" and not frappe.db.exists('Price List', "LCOS") and 'Camp Manager' in roles:
			self.price_list_doc(template_name='LCOS',buying=0,selling=1)
			self.create_covlcc_buying(template_name="LCOVLCCB")


		elif self.price_template_type == "VLCC Local Farmer" and not frappe.db.exists('Price List', "GTVLCCB"):
			self.price_list_doc(template_name='LFS',buying=1,selling=0)

		elif self.price_template_type == "VLCC Local Customer" and not frappe.db.exists('Price List', "GTCS"):
			self.price_list_doc(template_name='LCS',buying=0,selling=1)

	
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
				item_pric_.price_list_rate = row.price
				item_pric_.save()

	def create_item_price(self,price_doc_name):

		for row in self.items:
			# if not frappe.db.get_value('Item Price', {"price_list":price_doc_name},"name"):
			item_price = frappe.new_doc("Item Price")
			item_price.price_list = price_doc_name
			item_price.item_code = row.item
			item_price.price_list_rate = row.price
			item_price.flags.ignore_permissions = True
			item_price.save()


	def price_list_doc(self,template_name,buying,selling):

		price_doc = frappe.new_doc("Price List")
		price_doc.price_list_name = template_name
		price_doc.currency = "INR"
		price_doc.buying = buying
		price_doc.selling = selling
		price_doc.default = 1
		price_doc.flags.ignore_permissions = True
		price_doc.save()

		self.price_list = price_doc.name
		self.save()
		self.create_item_price(price_doc.name)

	def create_covlcc_buying(self,template_name):

		mpl_doc = frappe.new_doc("Material Price List")
		mpl_doc.price_template_type = "CO to VLCC"
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
		price_doc.default = 1
		price_doc.flags.ignore_permissions = True
		price_doc.save()

		mpl_doc.price_list = price_doc.name
		mpl_doc.save()

		self.create_item_price(price_doc.name)



def permission_query_condition(user):

	pass

	# branch_office = frappe.db.get_value("User",frappe.session.user,["branch_office","operator_type"],as_dict=1)
	# if branch_office.get('operator_type') == 'Camp Office':
	# 	return """`tabMaterial Price List`.price_list in ('GTCOB','GTCOS','LCOB','LCOS') """
	# elif branch_office.get('operator_type') == 'VLCC':
	# 	return """`tabMaterial Price List`.price_list in ('GTVLCCB','GTFS','GTCS','GTCOVLCCB') """

@frappe.whitelist()
def get_template(template):

	price_doc = frappe.get_doc("Material Price List",template)
	return price_doc
		