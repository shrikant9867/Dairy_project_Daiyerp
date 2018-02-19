# -*- coding: utf-8 -*-
# Copyright (c) 2018, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class MaterialPriceList(Document):

	def validate(self):

		roles = frappe.get_roles()

		if self.institution_type and self.party_type and not self.items:
			frappe.throw("Please add items")

		if 'Dairy Manager' in roles:
			price_list = frappe.db.sql("select name from `tabMaterial Price List` where institution_type = 'Dairy' and party_type = 'Local Supplier' and buying = 1",as_dict=1)
			price_list_sell = frappe.db.sql("select name from `tabMaterial Price List` where institution_type = 'Dairy' and party_type = 'VLCC' and selling = 1",as_dict=1)
			if self.is_new() and self.institution_type == 'Dairy' and self.party_type == 'Local Supplier':
				if price_list:
					frappe.throw("Please add items in the existing Material Price List <b>{0}</b>".format("<a href='#Form/Material Price List/{0}'>{0}</a>".format(price_list[0].get('name'))))

			elif self.is_new() and self.institution_type == 'Dairy' and self.party_type == 'VLCC':
				if price_list_sell:
					frappe.throw("Please add items in the existing Material Price List <b>{0}</b>".format("<a href='#Form/Material Price List/{0}'>{0}</a>".format(price_list_sell[0].get('name'))))





	def after_insert(self):

		self.create_item_price()

	def create_item_price(self):

		roles = frappe.get_roles();

		if 'Dairy Manager' in roles:
			if self.institution_type == "Dairy" and self.party_type == 'Local Supplier':
				for row in self.items:
					item_price = frappe.new_doc("Item Price")
					item_price.price_list = 'Standard Buying'
					item_price.item_code = row.item
					item_price.price_list_rate = row.price
					item_price.flags.ignore_permissions = True
					item_price.save()

			elif self.institution_type == "Dairy" and self.party_type == 'VLCC':
				for row in self.items:
					item_price = frappe.new_doc("Item Price")
					item_price.price_list = 'Standard Selling'
					item_price.item_code = row.item
					item_price.price_list_rate = row.price
					item_price.flags.ignore_permissions = True
					item_price.save()


	def on_update(self):

		roles = frappe.get_roles()

		if 'Dairy Manager' in roles:
			if self.institution_type == 'Dairy' and self.party_type == 'Local Supplier':
				# item_price_list = [item.get('item_code') for item in frappe.get_all('Item Price',fields=["item_code","price_list","name"])]
				item_data = frappe.db.sql("""select item_code from `tabItem Price` where price_list = 'Standard Buying'""",as_dict=1)
				item_price_list = [data.get('item_code') for data in item_data]
				for row in self.items:
					if row.item not in item_price_list:
						item_price = frappe.new_doc("Item Price")
						item_price.price_list = "Standard Buying"
						item_price.item_code = row.item
						item_price.price_list_rate = row.price
						item_price.flags.ignore_permissions = True
						item_price.save()

					else:
						item = frappe.db.get_value("Item Price",{'price_list':"Standard Buying", 'item_code':row.item},'name')
						item_pric_= frappe.get_doc("Item Price",item)
						item_pric_.price_list_rate = row.price
						item_pric_.save()

			elif self.institution_type == 'Dairy' and self.party_type == 'VLCC':
				# item_price_list = [item.get('item_code') for item in frappe.get_all('Item Price',fields=["item_code","price_list","name"])]
				item_data = frappe.db.sql("""select item_code from `tabItem Price` where price_list = 'Standard Selling'""",as_dict=1)
				item_price_list = [data.get('item_code') for data in item_data]
				for row in self.items:
					if row.item not in item_price_list:
						item_price = frappe.new_doc("Item Price")
						item_price.price_list = "Standard Selling"
						item_price.item_code = row.item
						item_price.price_list_rate = row.price
						item_price.flags.ignore_permissions = True
						item_price.save()

					else:
						item = frappe.db.get_value("Item Price",{'price_list':"Standard Selling", 'item_code':row.item},'name')
						if item:
							item_pric_= frappe.get_doc("Item Price",item)
							item_pric_.price_list_rate = row.price
							item_pric_.save()