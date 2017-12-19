# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "Dairy Erp",
			"color": "green",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Dairy Erp")
		},
			{
			"module_name": "Dairy",
			"color": "#589494",
			"icon": "fa fa-paw",
			"type": "page",
			"link": "dairy-dashboard",
			"label": _("Dairy Dashboard")
		},
	]
