from __future__ import unicode_literals
from frappe import _


def get_data(): 
	return [
		{
			"label": _("Masters"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Customer",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Item",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Supplier",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Item Group",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Supplier Type",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Contact",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Address",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Customer Group",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Price List",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Territory",
					"description": _(" "),
				}							
			]
		},
		{
			"label": _("Documents"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Material Request",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Purchase Order",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Delivery Note",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Sales Invoice",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Purchase Invoice",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Payment Entry",
					"description": _(" "),
				}
			
			]
		},
		{
			"label": _("Setup"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Company",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Warehouse",
					"description": _(" "),
				}

			]
		},
		{
			"label": _("Vlcc"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Vlcc",
					"description": _(" "),
				}
			]
		}			
	]			