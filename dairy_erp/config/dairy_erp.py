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
				},
				{
					"type": "doctype",
					"name": "Purchase Receipt",
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
				},
				{
					"type": "doctype",
					"name": "Dairy Log",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Mobile App Log",
					"description": _(" "),
				}

			]
		},
		{
			"label": _("Village Level Collection Centre"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Farmer",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Local Sale",
					"description": _(" "),
				},
				{
					"type": "page",
					"name": "vlcc-dashboard",
					"label": "Vlcc Dashboard",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Farmer Milk Collection Record",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Veterinary AI Technician",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Service Note",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Supplier Item Price",
					"description": _(" "),
				}
				
			]
		},
		{
			"label": _("Dairy"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Village Level Collection Centre",
					"description": _(" "),
				},
				{
					"type": "page",
					"name": "dairy-dashboard",
					"label": "Dairy Dashboard",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Vlcc Milk Collection Record",
					"description": _(" "),
				}

			]
		},
		{
			"label": _("Village Level Collection Centre Reports"),
			"icon": "icon-star",
			"items": [
				{
					"type": "report",
					"name": "Farmer Net Payoff",
					"doctype": "Farmer",
					"is_query_report": True
				}
			]
		}				
	]			

