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
		self.validate_status()
		self.validate_society()
		self.validate_vlcc()
		self.check_stock()

	def on_submit(self):
		try:
			if self.status == "Accept":
				pr = self.make_purchase_receipt()
				dn = self.make_delivery_note_vlcc()
				pi = self.make_purchase_invoice(pr)
				si = self.make_sales_invoice(dn)
				frappe.msgprint(_("Delivery Note <b>{0}</b>, Sales Invoice <b>{1}</b> Created at Vlcc level \
					AND Purchase Receipt <b>{2}</b>, Purchase Invoice <b>{3}</b> Created at Chilling centre level".format(
						'<a href="#Form/Delivery Note/'+dn+'">'+dn+'</a>',
						'<a href="#Form/Sales Invoice/'+si+'">'+si+'</a>',
						'<a href="#Form/Purchase Receipt/'+pr+'">'+pr+'</a>',
						'<a href="#Form/Purchase Invoice/'+pi+'">'+pi+'</a>',
					)))
		except Exception as e:
			raise e
			print frappe.get_traceback()
			frappe.db.rollback()
			frappe.throw(e)

	def validate_duplicate_entry(self):
		filters = {
			"societyid": self.societyid,
			"collectiontime": self.collectiontime,
			"collectiondate": self.collectiondate,
			"rcvdtime": self.rcvdtime,
			"shift": self.shift,
			"farmerid": self.farmerid,
			"milktype": self.milktype
		}
		is_duplicate = frappe.db.get_value("Vlcc Milk Collection Record", filters, "name")
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

	def validate_status(self):
		# user only create transactions with status - Accept
		if self.status == "Reject":
			frappe.throw(_("Status is Reject, Transaction can not be created"))

	def check_stock(self):
		"""check stock is available for transactions"""
		item = self.milktype+" Milk"
		vlcc_warehouse = frappe.db.get_value("Village Level Collection Centre", self.associated_vlcc, "warehouse")
		if not vlcc_warehouse:
			frappe.throw(_("Warehouse is not present on VLCC <b>{0}</b>".format(self.associated_vlcc)))
		stock_qty = frappe.db.get_value("Bin", {
			"warehouse": vlcc_warehouse,
			"item_code": item
		},"actual_qty") or 0
		if not stock_qty or stock_qty < self.milkquantity:
			frappe.throw(_("The dispatched quantity of <b>{0}</b> should be less than or \
				equal to stock <b>{1}</b> available at <b>{2}</b> warehouse".format(item, stock_qty, vlcc_warehouse)))

	def make_purchase_receipt(self):
		try:
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
			return pr.name
		except Exception as e:
			raise e

	def make_delivery_note_vlcc(self):
		try:
			item_mapper = {"COW": "COW Milk", "BUFFALO": "BUFFALO Milk"}
			item = frappe.get_doc("Item", item_mapper[self.milktype])
			customer = frappe.db.get_value("Village Level Collection Centre", self.associated_vlcc, "plant_office")
			warehouse = frappe.db.get_value("Village Level Collection Centre", {"amcu_id": self.farmerid }, 'warehouse')
			cost_center = frappe.db.get_value("Cost Center", {"company": self.associated_vlcc}, 'name')
			dn = frappe.new_doc("Delivery Note")
			dn.customer = customer
			dn.vlcc_milk_collection_record = self.name
			dn.company = self.associated_vlcc
			dn.append("items",
			{
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
			return dn.name
		except Exception as e:
			raise e

	def make_purchase_invoice(self,pr):
		try:
			item_mapper = {"COW": "COW Milk", "BUFFALO": "BUFFALO Milk"}
			item = frappe.get_doc("Item", item_mapper[self.milktype])
			pi = frappe.new_doc("Purchase Invoice")
			pi.supplier =  "vlcc2"
			pi.vlcc_milk_collection_record = self.name
			pi.company = frappe.db.get_value("Company",{"is_dairy":1},'name')
			pi.append("items",
				{
					"item_code": item.item_code,
					"item_name": item.item_name,
					"description": item.description,
					"uom": "Litre",
					"qty": self.milkquantity,
					"rate": self.rate,
					"amount": self.amount,
					"warehouse": frappe.db.get_value("Village Level Collection Centre", self.associated_vlcc, 'warehouse'),
					"purchase_receipt": pr
				}
			)
			pi.flags.ignore_permissions = True
			pi.submit()
			return pi.name
		except Exception as e:
			raise e

	def make_sales_invoice(self, dn):
		try:
			item_mapper = {"COW": "COW Milk", "BUFFALO": "BUFFALO Milk"}
			item = frappe.get_doc("Item", item_mapper[self.milktype])
			customer = frappe.db.get_value("Village Level Collection Centre", self.associated_vlcc, "plant_office")
			warehouse = frappe.db.get_value("Village Level Collection Centre", {"amcu_id": self.farmerid }, 'warehouse')
			cost_center = frappe.db.get_value("Cost Center", {"company": self.associated_vlcc}, 'name')
			si = frappe.new_doc("Sales Invoice")
			si.customer = customer
			si.company = self.associated_vlcc
			si.vlcc_milk_collection_record = self.name
			si.append("items",
			{
				"item_code": item.item_code,
				"qty": self.milkquantity,
				"rate": self.rate,
				"amount": self.amount,
				"warehouse": warehouse,
				"cost_center": cost_center,
				"delivery_note": dn
			})
			si.flags.ignore_permissions = True
			si.submit()
			return si.name
		except Exception as e:
			raise e
