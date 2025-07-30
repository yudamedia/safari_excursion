# ~/frappe-bench/apps/safari_excursion/safari_excursion/setup/uninstall.py

import frappe
from frappe import _

def before_uninstall():
    """Actions to perform before uninstalling Safari Excursion"""
    frappe.msgprint(_("Preparing to uninstall Safari Excursion..."))

def after_uninstall():
    """Actions to perform after uninstalling Safari Excursion"""
    cleanup_custom_fields()
    cleanup_email_templates()
    frappe.msgprint(_("Safari Excursion uninstalled successfully"))

def cleanup_custom_fields():
    """Remove custom fields added by Safari Excursion"""
    try:
        # Remove custom fields from Transport Booking
        transport_fields = [
            "excursion_booking",
            "is_excursion_transport"
        ]
        
        for field in transport_fields:
            if frappe.db.exists("Custom Field", {"dt": "Transport Booking", "fieldname": field}):
                frappe.delete_doc("Custom Field", f"Transport Booking-{field}")
        
        # Remove custom fields from Safari Guide
        guide_fields = [
            "excursion_specialties",
            "preferred_excursion_types"
        ]
        
        for field in guide_fields:
            if frappe.db.exists("Custom Field", {"dt": "Safari Guide", "fieldname": field}):
                frappe.delete_doc("Custom Field", f"Safari Guide-{field}")
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Custom field cleanup error: {str(e)}")

def cleanup_email_templates():
    """Remove email templates created by Safari Excursion"""
    try:
        templates = [
            "Excursion Booking Confirmation",
            "Excursion Guide Assignment"
        ]
        
        for template in templates:
            if frappe.db.exists("Email Template", template):
                frappe.delete_doc("Email Template", template)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Email template cleanup error: {str(e)}")