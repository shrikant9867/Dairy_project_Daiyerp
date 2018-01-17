# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "dairy_erp"
app_title = "Dairy Erp"
app_publisher = "indictrans technologies"
app_description = "Erp for co-operative Dairy"
app_icon = "octicon octicon-file-directory"
app_color = "green"
app_email = "khushal.t@indictranstech.com"
app_license = "MIT"

# Includes in <head>
# ------------------
setup_wizard_complete = "dairy_erp.customization.customization.create_item_group"
# include js, css files in header of desk.html
# app_include_css = "/assets/dairy_erp/css/dairy_erp.css"
# app_include_js = "/assets/dairy_erp/js/dialog.min.js"

# include js, css files in header of web template
# web_include_css = "/assets/dairy_erp/css/dairy_erp.css"
# web_include_js = "/assets/dairy_erp/js/dairy_erp.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_list_js = {
"Material Request":["customization/material_request/material_request_list.js"]
}
doctype_js = {
    "Address":["customization/address.js"],
    "Supplier":["customization/supplier.js"],
    "Material Request":["customization/material_request/material_request.js"],
    "Purchase Order":["customization/purchase_order/purchase_order.js"],
    "User":["customization/user/user.js"],
    "Sales Order":["customization/sales_order/sales_order.js"]
    }
doctype_list_js = {
    "Purchase Receipt" :["customization/purchase_receipt/purchase_receipt_list.js"],
    "Material Request" :["customization/material_request/material_request_list.js"]
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "dairy_erp.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "dairy_erp.install.before_install"
after_install = "dairy_erp.customization.customization.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dairy_erp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Address": {
		"after_insert": ["dairy_erp.customization.customization.set_warehouse","dairy_erp.customization.customization.validate_dairy_company"],
		"on_update": "dairy_erp.customization.customization.update_warehouse",
		"validate": "dairy_erp.customization.customization.validate_headoffice"
	},
    "Purchase Order":{
        "validate":["dairy_erp.customization.customization.set_co_warehouse_po","dairy_erp.customization.customization.set_page_break"]
    },
    "Purchase Receipt":{
        "on_submit": "dairy_erp.customization.customization.submit_dn",
        "validate": ["dairy_erp.customization.customization.set_co_warehouse_pr"]
    },
    "Sales Order":{
        "on_submit":"dairy_erp.customization.customization.make_so_against_vlcc",
        "validate": "dairy_erp.customization.customization.set_vlcc_warehouse"
    },
    "Delivery Note":{
        "on_submit": "dairy_erp.customization.customization.make_si_against_vlcc",
        "validate":"dairy_erp.customization.customization.set_vlcc_warehouse",
        "after_insert":"dairy_erp.customization.customization.make_purchase_receipt"
    },
    "Material Request":{
        "validate": "dairy_erp.customization.customization.set_mr_warehouse"
    },
    "Supplier":{
        "validate": "dairy_erp.customization.customization.set_company"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dairy_erp.tasks.all"
# 	],
# 	"daily": [
# 		"dairy_erp.tasks.daily"
# 	],
# 	"hourly": [
# 		"dairy_erp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dairy_erp.tasks.weekly"
# 	]
# 	"monthly": [
# 		"dairy_erp.tasks.monthly"
# 	]
# }
fixtures=['Property Setter','Custom Field','Print Format','Role']
# Testing
# -------

# before_tests = "dairy_erp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dairy_erp.event.get_events"
# }

