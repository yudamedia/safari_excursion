# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_operation/excursion_operation.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, time_diff_in_hours, get_time

class ExcursionOperation(Document):
    """
    DocType controller for Excursion Operation
    
    This controller handles the actual execution and tracking of excursions,
    including progress tracking, guide assignments, and operational feedback.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_booking_details()
        self.validate_operation_timing()
        self.validate_assignments()
        self.validate_progress_tracking()
        self.set_operation_status()
    
    def validate_booking_details(self):
        """Validate excursion booking and package details"""
        if not self.excursion_booking:
            frappe.throw(_("Excursion Booking is required"))
        
        # Get booking details
        booking = frappe.get_doc("Excursion Booking", self.excursion_booking)
        self.excursion_package = booking.excursion_package
        self.guest_count = booking.total_guests
        self.departure_time = booking.departure_time
        self.estimated_return_time = booking.estimated_return_time
    
    def validate_operation_timing(self):
        """Validate operation date and timing"""
        if not self.operation_date:
            frappe.throw(_("Operation Date is required"))
        
        if getdate(self.operation_date) < getdate():
            frappe.throw(_("Operation date cannot be in the past"))
        
        # Validate actual times if provided
        if self.actual_departure_time and self.departure_time:
            if get_time(self.actual_departure_time) < get_time(self.departure_time):
                frappe.msgprint(_("Actual departure time is earlier than scheduled departure time"), alert=True)
    
    def validate_assignments(self):
        """Validate guide and vehicle assignments"""
        if self.assigned_guide:
            if not self.is_guide_available(self.assigned_guide):
                frappe.throw(_("Selected guide is not available for this operation"))
        
        if self.assigned_vehicle:
            if not self.is_vehicle_available(self.assigned_vehicle):
                frappe.throw(_("Selected vehicle is not available for this operation"))
    
    def validate_progress_tracking(self):
        """Validate progress tracking fields"""
        # Validate pickup completion
        if self.pickup_completed and not self.pickup_completion_time:
            self.pickup_completion_time = now_datetime()
        
        # Validate excursion start
        if self.excursion_started and not self.excursion_start_time:
            self.excursion_start_time = now_datetime()
        
        # Validate excursion completion
        if self.excursion_completed and not self.excursion_completion_time:
            self.excursion_completion_time = now_datetime()
        
        # Validate dropoff completion
        if self.dropoff_completed and not self.dropoff_completion_time:
            self.dropoff_completion_time = now_datetime()
    
    def set_operation_status(self):
        """Set operation status based on progress"""
        if self.operation_status == "Scheduled":
            if self.pickup_completed:
                self.operation_status = "In Progress"
        
        if self.operation_status == "In Progress":
            if self.excursion_completed and self.dropoff_completed:
                self.operation_status = "Completed"
    
    def is_guide_available(self, guide):
        """Check if guide is available for this operation"""
        # Check if guide has any conflicting operations on the same date
        conflicting_ops = frappe.get_all("Excursion Operation", {
            "assigned_guide": guide,
            "operation_date": self.operation_date,
            "name": ["!=", self.name],
            "operation_status": ["in", ["Scheduled", "In Progress"]]
        })
        
        return len(conflicting_ops) == 0
    
    def is_vehicle_available(self, vehicle):
        """Check if vehicle is available for this operation"""
        # Check if vehicle has any conflicting operations on the same date
        conflicting_ops = frappe.get_all("Excursion Operation", {
            "assigned_vehicle": vehicle,
            "operation_date": self.operation_date,
            "name": ["!=", self.name],
            "operation_status": ["in", ["Scheduled", "In Progress"]]
        })
        
        return len(conflicting_ops) == 0
    
    def on_submit(self):
        """Handle operation submission"""
        self.send_operation_notifications()
        self.update_booking_status()
    
    def send_operation_notifications(self):
        """Send notifications for operation status changes"""
        if self.operation_status == "In Progress":
            self.send_guide_notification()
        elif self.operation_status == "Completed":
            self.send_completion_notification()
    
    def send_guide_notification(self):
        """Send notification to assigned guide"""
        if self.assigned_guide:
            # Implementation for guide notification
            pass
    
    def send_completion_notification(self):
        """Send completion notification"""
        # Implementation for completion notification
        pass
    
    def update_booking_status(self):
        """Update related booking status"""
        if self.excursion_booking:
            booking = frappe.get_doc("Excursion Booking", self.excursion_booking)
            if self.operation_status == "Completed":
                booking.booking_status = "Completed"
                booking.save()
    
    @frappe.whitelist()
    def start_pickup(self):
        """Mark pickup as started"""
        self.pickup_completed = 1
        self.pickup_completion_time = now_datetime()
        self.operation_status = "In Progress"
        self.save()
        frappe.msgprint(_("Pickup marked as completed"))
    
    @frappe.whitelist()
    def start_excursion(self):
        """Mark excursion as started"""
        self.excursion_started = 1
        self.excursion_start_time = now_datetime()
        self.save()
        frappe.msgprint(_("Excursion marked as started"))
    
    @frappe.whitelist()
    def complete_excursion(self):
        """Mark excursion as completed"""
        self.excursion_completed = 1
        self.excursion_completion_time = now_datetime()
        self.save()
        frappe.msgprint(_("Excursion marked as completed"))
    
    @frappe.whitelist()
    def complete_dropoff(self):
        """Mark dropoff as completed"""
        self.dropoff_completed = 1
        self.dropoff_completion_time = now_datetime()
        self.operation_status = "Completed"
        self.save()
        frappe.msgprint(_("Dropoff marked as completed"))
    
    def get_operation_duration(self):
        """Calculate total operation duration in hours"""
        if self.excursion_start_time and self.excursion_completion_time:
            return time_diff_in_hours(self.excursion_completion_time, self.excursion_start_time)
        return 0
    
    def get_guide_name(self):
        """Get assigned guide name"""
        if self.assigned_guide:
            return frappe.get_value("Safari Guide", self.assigned_guide, "guide_name")
        return ""
    
    def get_vehicle_details(self):
        """Get assigned vehicle details"""
        if self.assigned_vehicle:
            return frappe.get_value("Vehicle", self.assigned_vehicle, "vehicle_number")
        return "" 