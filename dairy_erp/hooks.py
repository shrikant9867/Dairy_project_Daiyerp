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
app_include_css = "/assets/js/dairy.desk.min.css"
app_include_js = "/assets/js/dairy.desk.min.js"

# include js, css files in header of web template
# web_include_css = "/assets/dairy_erp/css/dairy_erp.css"
# web_include_js = "/assets/dairy_erp/js/dairy_erp.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_list_js = {
# "Material Request":["customization/material_request/material_request_list.js"],
# "Purchase Invoice":["customization/purchase_invoice/purchase_invoice_list.js"]
# }
website_context = {
    "favicon":  "/assets/dairy_erp/images/stellapps_logo.png",
    "splash_image": "/assets/dairy_erp/images/stellapps_logo.png"
}

doctype_js = {
    "Address":["customization/address.js"],
    "Supplier":["customization/supplier.js"],
    "Material Request":["customization/material_request/material_request.js"],
    "Purchase Order":["customization/purchase_order/purchase_order.js"],
    "User":["customization/user/user.js"],
    "Sales Order":["customization/sales_order/sales_order.js"],
    "Purchase Receipt": ["customization/purchase_receipt/purchase_receipt.js"],
    "Sales Invoice": ["customization/sales_invoice/sales_invoice.js"],
    "Stock Entry":["customization/stock_entry/stock_entry.js"],
    "Purchase Invoice": "customization/purchase_invoice/purchase_invoice.js",
    "Delivery Note": "customization/delivery_note/delivery_note.js"
}
doctype_list_js = {
    "Purchase Receipt" :["customization/purchase_receipt/purchase_receipt_list.js"],
    "Material Request" :["customization/material_request/material_request_list.js"],
    "Purchase Invoice":["customization/purchase_invoice/purchase_invoice_list.js"],
    "Purchase Order":["customization/purchase_order/purchase_order_list.js"],
    "Delivery Note":["customization/delivery_note/delivery_note_list.js"],
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#   "Role": "home_page"
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
#   "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#   "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Address": {
        "after_insert": ["dairy_erp.customization.customization.validate_dairy_company","dairy_erp.customization.customization.make_account_and_warehouse"],
        "on_update": "dairy_erp.customization.customization.update_warehouse",
        "validate": "dairy_erp.customization.customization.validate_headoffice"
    },
    "Purchase Order":{
        "validate":["dairy_erp.customization.customization.set_co_warehouse_po","dairy_erp.customization.customization.set_page_break"]
    },
    "Purchase Receipt":{
        "on_submit": "dairy_erp.customization.customization.on_submit_pr",
        "validate": ["dairy_erp.customization.customization.set_co_warehouse_pr","dairy_erp.customization.customization.validate_qty"]
    },
    "Sales Order":{
        "on_submit":"dairy_erp.customization.customization.make_so_against_vlcc",
        "validate": "dairy_erp.customization.customization.set_vlcc_warehouse"
    },
    "Delivery Note":{
        "on_submit": ["dairy_erp.customization.customization.validate_pr","dairy_erp.customization.customization.update_mi"],
        "validate":["dairy_erp.customization.customization.set_vlcc_warehouse","dairy_erp.customization.customization.validate_dn"],
        "after_insert":"dairy_erp.customization.customization.make_purchase_receipt",
        "on_update":"dairy_erp.customization.delivery_note.delivery_note.get_partial_quatity"
    },
    "Material Request":{
        "validate": ["dairy_erp.customization.customization.set_mr_warehouse","dairy_erp.customization.customization.set_chilling_wrhouse","dairy_erp.customization.material_request.material_request.validate"],
        "on_update_after_submit":"dairy_erp.customization.material_request.material_request.status_updater"
    },
    "Supplier":{
        "validate": "dairy_erp.customization.customization.set_company",
        "after_insert": "dairy_erp.customization.customization.set_supp_company"
    },
    "GL Entry":{
        "before_submit": "dairy_erp.customization.customization.set_camp"
    },
    "Sales Invoice":{
        "validate": ["dairy_erp.customization.sales_invoice.sales_invoice.validate_local_sale", "dairy_erp.customization.sales_invoice.sales_invoice.set_camp_office_accounts"],
        "on_submit": "dairy_erp.customization.sales_invoice.sales_invoice.payment_entry"
    },
    "Stock Entry":{
        "validate": "dairy_erp.customization.stock_entry.stock_entry.set_target_warehouse",
        "on_submit": ["dairy_erp.customization.stock_entry.stock_entry.validate_camp_submission","dairy_erp.customization.stock_entry.stock_entry.check_if_dropship"]
    },
    "Purchase Invoice": {
        "validate": "dairy_erp.customization.sales_invoice.sales_invoice.set_camp_office_accounts",
    },
    "Payment Entry": {
        "validate": "dairy_erp.customization.payment_entry.payment_entry.validate_by_credit_invoice"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#   "all": [
#       "dairy_erp.tasks.all"
#   ],
#   "daily": [
#       "dairy_erp.tasks.daily"
#   ],
#   "hourly": [
#       "dairy_erp.tasks.hourly"
#   ],
#   "weekly": [
#       "dairy_erp.tasks.weekly"
#   ]
#   "monthly": [
#       "dairy_erp.tasks.monthly"
#   ]
# }
fixtures=['Property Setter','Custom Field','Print Format','Role','Custom DocPerm','Custom Role']


permission_query_conditions = {
    "Material Request": "dairy_erp.customization.customization.mr_permission",
    "Purchase Receipt": "dairy_erp.customization.customization.pr_permission",
    "Purchase Order": "dairy_erp.customization.customization.po_permission",
    "Purchase Invoice": "dairy_erp.customization.customization.pi_permission",
    "Delivery Note": "dairy_erp.customization.customization.dn_permission",
    "Sales Invoice": "dairy_erp.customization.customization.si_permission",
    "Farmer": "dairy_erp.customization.customization.farmer_permission",
    "Village Level Collection Centre": "dairy_erp.customization.customization.vlcc_permission",
    "Farmer Milk Collection Record": "dairy_erp.customization.customization.fmrc_permission",
    "Vlcc Milk Collection Record": "dairy_erp.customization.customization.vmcr_permission",
    "Payment Entry": "dairy_erp.customization.customization.pe_permission",
    "Supplier":"dairy_erp.customization.customization.supplier_permission",
    "Customer": "dairy_erp.customization.customization.customer_permission",
    "Company": "dairy_erp.customization.customization.company_permission",
    "Warehouse": "dairy_erp.customization.customization.warehouse_permission",
    "Material Price List" : "dairy_erp.dairy_erp.doctype.material_price_list.material_price_list.permission_query_condition"
}
# Testing
# -------

# before_tests = "dairy_erp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
#   "frappe.desk.doctype.event.event.get_events": "dairy_erp.event.get_events"
# }

