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

# include js, css files in header of desk.html
# app_include_css = "/assets/dairy_erp/css/dairy_erp.css"
# app_include_js = "/assets/dairy_erp/js/dairy_erp.js"

# include js, css files in header of web template
# web_include_css = "/assets/dairy_erp/css/dairy_erp.css"
# web_include_js = "/assets/dairy_erp/js/dairy_erp.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
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
after_install = "dairy_erp.customization.customization.create_supplier_type"

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
		"after_insert": "dairy_erp.customization.customization.set_warehouse",
		"on_update": "dairy_erp.customization.customization.update_warehouse",
		"validate": "dairy_erp.customization.customization.validate_headoffice"
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
fixtures=['Property Setter','Custom Field']
# Testing
# -------

# before_tests = "dairy_erp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dairy_erp.event.get_events"
# }

