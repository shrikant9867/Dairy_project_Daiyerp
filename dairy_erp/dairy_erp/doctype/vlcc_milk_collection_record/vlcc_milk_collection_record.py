# -*- coding: utf-8 -*-
# Copyright (c) 2017, indictrans technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class VlccMilkCollectionRecord(Document):

	def validate(self):
		self.validate_duplicate_entry()
		self.validate_society()
		self.validate_vlcc()
		self.check_stock()

	def on_submit(self):
		try:
			if self.status == "Accept":
				pr = self.make_purchase_receipt()
				self.make_delivery_note(pr)
		except Exception as e:
			print frappe.get_traceback()
			frappe.db.rollback()
			frappe.msgprint(e)

	def validate_duplicate_entry(self):
		args = {
			"societyid": self.societyid,
			"collectiontime": self.collectiontime,
			"collectiondate": self.collectiondate,
			"rcvdtime": self.rcvdtime,
			"shift": self.shift,
			"farmerid": self.farmerid,
			"milktype": self.milktype
		}
		if is_duplicate and is_duplicate != self.name:
			frappe.throw(_("Duplicate Entry found - {0}".format(is_duplicate)))

	def validate_society(self):
		address = frappe.db.get_value("Address", {
				"centre_id": self.societyid
			}, "name")
		if not address:
			frappe.throw(_("Invalid Society ID"))

	def validate_vlcc(self):
		vlcc = frappe.db.get_value("Village Level Collection Centre", {
			"amcu_id": self.farmerid
		}, "name")
		if not vlcc:
			frappe.throw("Invalid Amcu ID/VLCC")

	def check_stock(self):
		"""check stock is available for transactions"""
		item = self.milktype+" Milk"
		vlcc_warehouse = frappe.db.get_value("Village Level Collection Centre", self.associated_vlcc, "warehouse")
		stock_qty = frappe.db.get_value("Bin", {
			"warehouse": vlcc_warehouse,
			"item_code": item
		},"actual_qty")
		if not stock_qty or stock_qty < self.milkquantity:
			frappe.throw(_("The dispatched quantity of {0} should be less than or \
				equal to stock {1} available at {2} warehouse".format(item, stock_qty, vlcc_warehouse)))

	def make_purchase_receipt(self):
		item_mapper = {"COW": "COW Milk", "BUFFALO": "BUFFALO Milk"}
		camp_office = frappe.db.get_value("Village Level Collection Centre",{'name':self.associated_vlcc},"camp_office")
		item = frappe.get_doc("Item", item_mapper[self.milktype])
		pr = frappe.new_doc("Purchase Receipt")
		pr.supplier =  self.associated_vlcc
		pr.vlcc_milk_collection_record = self.name
		pr.company = frappe.db.get_value("Company",{"is_dairy":1},'name')
		pr.camp_office = camp_office
		pr.append("items",
			{
				"item_code": item.item_code,
				"item_name": item.item_name,
				"description": item.description,
				"uom": "Litre",
				"qty": self.milkquantity,
				"rate": self.rate,
				"amount": self.amount,
				"warehouse": frappe.db.get_value("Address", {"centre_id": self.societyid }, 'warehouse')
			}
		)
		pr.status = "Completed"
		pr.per_billed = 100
		pr.flags.ignore_permissions = True
		pr.submit()

	def make_delivery_note(self, pr):
		item_mapper = {"COW": "COW Milk", "BUFFALO": "BUFFALO Milk"}
		item = frappe.get_doc("Item", item_mapper[self.milktype])
		customer = frappe.db.get_value("Village Level Collection Centre", self.associated_vlcc, "plant_office")
		warehouse = frappe.db.get_value("Village Level Collection Centre", {"amcu_id": self.farmerid }, 'warehouse')
		cost_center = frappe.db.get_value("Cost Center", {"company": self.associated_vlcc}, 'name')
		dn = frappe.new_doc("Delivery Note")
		dn.customer = customer
		dn.vlcc_milk_collection_record = self.name
		dn.company = self.associated_vlcc
		dn.append("items", {
			"item_code": item.item_code,
			"item_name": item.item_name,
			"description": item.description,
			"uom": "Litre",
			"qty": self.milkquantity,
			"rate": self.rate,
			"amount": self.amount,
			"warehouse": warehouse,
			"cost_center": cost_center
		})
		dn.status = "Completed"
		dn.flags.ignore_permissions = True
		dn.submit()
