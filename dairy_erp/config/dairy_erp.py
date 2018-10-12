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
					"name": "Territory",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Customer Group",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Customer",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Supplier Type",
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
					"name": "Item",
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
					"name": "Price List",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Material Price List",
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
					"name": "Purchase Receipt",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Purchase Invoice",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Sales Invoice",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Delivery Note",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Stock Entry",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Payment Entry",
					"description": _(" "),
				},				
				{
					"type": "doctype",
					"name": "Journal Entry",
					"description": _(" "),
				}	
			]
		},
		{
			"label": _("Village Level Collection Centre"),
			"icon": "icon-star",
			"items": [
				{
					"type": "page",
					"name": "vlcc-dashboard",
					"label": _("Vlcc Dashboard"),
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Village Level Collection Centre",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Farmer",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Farmer Milk Collection Record",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Shift Ended Confirmation",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Veterinary AI Technician",
					"description": _(" "),
				}
			]
		},
		{
			"label": _("Reports"),
			"icon": "icon-star",
			"items": [
				{
					"type": "page",
					"name": "smarterp_comparison_report",
					"label": _("SmartAMCU - SmartERP Comparison Report"),
					"description": _(" "),
				},
				{
					"type": "report",
					"name": "Milk Bill txt",
					"label":_("Milk Bill Txt"),
					"doctype": "Vlcc Milk Collection Record",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "10 Days STMT",
					"label":_("10 Days STMT"),
					"doctype": "Vlcc Milk Collection Record",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Truck sheet",
					"label":_("Truck sheet"),
					"doctype": "Vlcc Milk Collection Record",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Milk Passbook",
					"label":_("Milk Passbook"),
					"doctype": "Farmer Milk Collection Record",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Local Sales Report",
					"label": _("Local Sales Report"),
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "page",
					"name": "individual_farmer_milk_report",
					"label": _("Individual Farmer Milk Report"),
					"description": _(" "),
				},
				{
					"type": "page",
					"name": "daily-milk-purchase",
					"label": _("Daily Milk Purchase Report"),
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Dairy Register",
					"label": _("Dairy Register"),
					"description": _(" "),
				},
				{
					"type": "page",
					"name": "mis_report",
					"label": _("MIS Report"),
					"description": _(" "),
				},
				{
					"type": "report",
					"name": "Cattle Feed Sales Report",
					"label":_("Cattle Feed Sales Report"),
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Cattle Feed Advance Report",
					"label":_("Cattle Feed Advance Report"),
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "CC Report",
					"label":_("CC Report"),
					"doctype": "Vlcc Milk Collection Record",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Farmer Net Payoff",
					"label": _("Farmer Net Payoff"),
					"doctype": "Farmer",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounts Receivable",
					"label": _("Accounts Receivable"),
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounts Payable",
					"label": _("Accounts Payable"),
					"doctype": "Purchase Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Profit and Loss Statement",
					"label":_("Profit and Loss Statement"),
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Trial Balance",
					"label": _("Trial Balance"),
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Balance Sheet",
					"label":_("Balance Sheet"),
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Cash Flow",
					"label":_("Cash Flow"),
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "General Ledger",
					"label":_("General Ledger"),
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Stock Ledger",
					"label": _("Stock Ledger"),
					"doctype": "Stock Ledger Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Stock Balance",
					"label": _("Stock Balance"),
					"doctype": "Stock Ledger Entry",
					"is_query_report": True
				},				
				{
					"type": "report",
					"name": "Vlcc Net Pay Off",
					"doctype": "Village Level Collection Centre",
					"label": _("Vlcc Net Pay Off"),
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "VLCC Payment Settlement",
					"label": _("VLCC Payment Settlement"),
					"doctype": "VLCC Payment Cycle",
					"is_query_report": True
				},				
				{
					"type": "report",
					"name": "Purchase Order Detail Report",
					"label":_("Purchase Order Detail Report"),
					"doctype": "Purchase Order",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Material Indent Detail Report",
					"label":_("Material Indent Detail Report"),
					"doctype": "Material Request",
					"is_query_report": True
				}
			]
		},
		{
			"label": _("Loan & Advance"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Farmer Loan",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Farmer Advance",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Vlcc Advance",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Vlcc Loan",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "VLCC Payment Cycle Report",
					"description": _(" "),
				}
			]
		},
		{
			"label": _("Settings"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Farmer Settings",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "VLCC Settings",
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
				},
				{
					"type": "doctype",
					"name": "AgRupay Log",
					"description": _(" "),
				}
			]
		},
		{
			"label": _("Payment Tool"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Farmer Payment Cycle",
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Farmer Payment Cycle Report",
					"description": _(" "),
				},
				{
					"type": "report",
					"name": "Farmer Payment Settlement",
					"label": _("Farmer Payment Settlement"),
					"doctype": "Farmer Payment Cycle",
					"is_query_report": True
				},
				{
					"type": "doctype",
					"name": "VLCC Payment Cycle",
					"description": _(" "),
				},
			]
		},
		{
			"label": _("Dairy"),
			"icon": "icon-star",
			"items": [
				{
					"type": "page",
					"name": "dairy-dashboard",
					"label": _("Dairy Dashboard"),
					"description": _(" "),
				},
				{
					"type": "doctype",
					"name": "Vlcc Milk Collection Record",
					"description": _(" "),
				}

			]
		}				
	]			

