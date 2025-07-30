# ~/frappe-bench/apps/safari_excursion/safari_excursion/notifications.py

import frappe
from frappe import _

def get_notification_config():
    """
    Return notification configuration for Safari Excursion
    
    This function defines what notifications should appear in the desk
    for excursion-related documents and activities.
    """
    
    return {
        "for_doctype": {
            # Excursion Bookings that need attention
            "Excursion Booking": {
                "filters": [
                    {
                        "fieldname": "booking_status",
                        "fieldtype": "Select",
                        "condition": "=",
                        "value": "Confirmed"
                    },
                    {
                        "fieldname": "excursion_date",
                        "fieldtype": "Date", 
                        "condition": "=",
                        "value": "Today"
                    }
                ],
                "fields": ["name", "customer_name", "excursion_package", "departure_time"],
                "title": _("Today's Excursions")
            },
            
            # Excursion Operations that are in progress
            "Excursion Operation": {
                "filters": [
                    {
                        "fieldname": "operation_status",
                        "fieldtype": "Select",
                        "condition": "in",
                        "value": ["Scheduled", "In Progress"]
                    },
                    {
                        "fieldname": "operation_date",
                        "fieldtype": "Date",
                        "condition": "=", 
                        "value": "Today"
                    }
                ],
                "fields": ["name", "excursion_booking", "assigned_guide", "operation_status"],
                "title": _("Active Operations")
            }
        },
        
        # Open document types that should appear in notifications
        "open_count_doctype": [
            "Excursion Booking", 
            "Excursion Operation"
        ]
    }

def get_excursion_notifications():
    """
    Get excursion-specific notifications for the current user
    
    Returns:
        dict: Notification data for excursions
    """
    
    notifications = []
    
    try:
        # Today's excursions needing attention
        today_excursions = frappe.get_all(
            "Excursion Booking",
            filters={
                "excursion_date": frappe.utils.today(),
                "booking_status": "Confirmed",
                "excursion_status": ["in", ["Scheduled", "In Progress"]]
            },
            fields=["name", "customer_name", "departure_time", "assigned_guide", "pickup_confirmation_status"],
            order_by="departure_time"
        )
        
        if today_excursions:
            # Check for unconfirmed pickups
            unconfirmed_pickups = [ex for ex in today_excursions if ex.pickup_confirmation_status == "Pending"]
            
            if unconfirmed_pickups:
                notifications.append({
                    "type": "alert",
                    "title": _("Pickup Confirmations Needed"),
                    "message": _("{0} excursions need pickup confirmation").format(len(unconfirmed_pickups)),
                    "indicator": "orange",
                    "route": "/app/excursion-booking?pickup_confirmation_status=Pending&excursion_date=Today"
                })
            
            # Check for unassigned guides
            unassigned_guides = [ex for ex in today_excursions if not ex.assigned_guide]
            
            if unassigned_guides:
                notifications.append({
                    "type": "alert", 
                    "title": _("Guide Assignment Required"),
                    "message": _("{0} excursions need guide assignment").format(len(unassigned_guides)),
                    "indicator": "red",
                    "route": "/app/excursion-booking?assigned_guide=&excursion_date=Today"
                })
        
        # Tomorrow's excursions for preparation
        from frappe.utils import add_days
        tomorrow = add_days(frappe.utils.today(), 1)
        
        tomorrow_excursions = frappe.db.count(
            "Excursion Booking",
            {
                "excursion_date": tomorrow,
                "booking_status": "Confirmed"
            }
        )
        
        if tomorrow_excursions > 0:
            notifications.append({
                "type": "info",
                "title": _("Tomorrow's Excursions"),
                "message": _("{0} excursions scheduled for tomorrow").format(tomorrow_excursions),
                "indicator": "blue",
                "route": f"/app/excursion-booking?excursion_date={tomorrow}"
            })
        
        # Overdue payment notifications
        overdue_payments = frappe.get_all(
            "Excursion Booking",
            filters={
                "payment_status": ["in", ["Unpaid", "Partially Paid"]],
                "payment_due_date": ["<", frappe.utils.today()],
                "booking_status": "Confirmed"
            },
            fields=["name"]
        )
        
        if overdue_payments:
            notifications.append({
                "type": "alert",
                "title": _("Overdue Payments"),
                "message": _("{0} bookings have overdue payments").format(len(overdue_payments)),
                "indicator": "red",
                "route": "/app/excursion-booking?payment_status=Unpaid&payment_status=Partially Paid"
            })
            
    except Exception as e:
        frappe.log_error(f"Excursion notifications error: {str(e)}")
    
    return notifications

def get_excursion_dashboard_notifications():
    """
    Get dashboard-specific notifications for excursion management
    
    Returns:
        dict: Dashboard notification data
    """
    
    try:
        from frappe.utils import today, add_days
        
        # Get current statistics
        today_stats = {
            "confirmed_bookings": frappe.db.count("Excursion Booking", {
                "excursion_date": today(),
                "booking_status": "Confirmed"
            }),
            "in_progress": frappe.db.count("Excursion Booking", {
                "excursion_date": today(),
                "excursion_status": "In Progress"
            }),
            "completed": frappe.db.count("Excursion Booking", {
                "excursion_date": today(),
                "excursion_status": "Completed"
            }),
            "unassigned_guides": frappe.db.count("Excursion Booking", {
                "excursion_date": ["between", [today(), add_days(today(), 2)]],
                "booking_status": "Confirmed",
                "assigned_guide": ["is", "not set"]
            }),
            "unassigned_vehicles": frappe.db.count("Excursion Booking", {
                "excursion_date": ["between", [today(), add_days(today(), 2)]],
                "booking_status": "Confirmed",
                "assigned_vehicle": ["is", "not set"]
            })
        }
        
        return {
            "status": "success",
            "data": today_stats
        }
        
    except Exception as e:
        frappe.log_error(f"Dashboard notifications error: {str(e)}")
        return {"status": "error", "message": str(e)}