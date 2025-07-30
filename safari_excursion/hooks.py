app_name = "safari_excursion"
app_title = "Safari Excusion"
app_publisher = "Graphic Station"
app_description = "Excursion and single day activity management app for SafariERP"
app_email = "safarierp@graphicstation.co.ke"
app_license = "gpl-3.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "safari_excursion",
# 		"logo": "/assets/safari_excursion/logo.png",
# 		"title": "Safari Excusion",
# 		"route": "/safari_excursion",
# 		"has_permission": "safari_excursion.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/safari_excursion/css/safari_excursion.css"
# app_include_js = "/assets/safari_excursion/js/safari_excursion.js"

# include js, css files in header of web template
# web_include_css = "/assets/safari_excursion/css/safari_excursion.css"
# web_include_js = "/assets/safari_excursion/js/safari_excursion.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "safari_excursion/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "safari_excursion/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "safari_excursion.utils.jinja_methods",
# 	"filters": "safari_excursion.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "safari_excursion.install.before_install"
# after_install = "safari_excursion.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "safari_excursion.uninstall.before_uninstall"
# after_uninstall = "safari_excursion.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "safari_excursion.utils.before_app_install"
# after_app_install = "safari_excursion.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "safari_excursion.utils.before_app_uninstall"
# after_app_uninstall = "safari_excursion.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "safari_excursion.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"safari_excursion.tasks.all"
# 	],
# 	"daily": [
# 		"safari_excursion.tasks.daily"
# 	],
# 	"hourly": [
# 		"safari_excursion.tasks.hourly"
# 	],
# 	"weekly": [
# 		"safari_excursion.tasks.weekly"
# 	],
# 	"monthly": [
# 		"safari_excursion.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "safari_excursion.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "safari_excursion.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "safari_excursion.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["safari_excursion.utils.before_request"]
# after_request = ["safari_excursion.utils.after_request"]

# Job Events
# ----------
# before_job = ["safari_excursion.utils.before_job"]
# after_job = ["safari_excursion.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"safari_excursion.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

