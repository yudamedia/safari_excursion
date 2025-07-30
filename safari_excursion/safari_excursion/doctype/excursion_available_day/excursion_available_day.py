# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_available_day/excursion_available_day.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionAvailableDay(Document):
    """
    DocType controller for Excursion Available Day
    
    This controller handles availability settings for specific days,
    including capacity overrides and special notes.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_day_selection()
        self.validate_capacity_override()
        self.set_default_values()
    
    def validate_day_selection(self):
        """Validate day selection"""
        if not self.day:
            frappe.throw(_("Day is required"))
        
        valid_days = [
            "Monday", "Tuesday", "Wednesday", "Thursday", 
            "Friday", "Saturday", "Sunday"
        ]
        
        if self.day not in valid_days:
            frappe.throw(_("Invalid day selected"))
    
    def validate_capacity_override(self):
        """Validate capacity override"""
        if self.max_capacity_override is not None:
            if self.max_capacity_override <= 0:
                frappe.throw(_("Maximum capacity override must be greater than 0"))
    
    def set_default_values(self):
        """Set default values for various fields"""
        if self.is_available is None:
            self.is_available = 1
    
    def get_day_summary(self):
        """Get a summary of the available day"""
        summary = self.day
        
        if not self.is_available:
            summary += " - NOT AVAILABLE"
        else:
            summary += " - Available"
        
        if self.max_capacity_override:
            summary += f" (Max: {self.max_capacity_override})"
        
        return summary
    
    def is_weekday(self):
        """Check if this is a weekday"""
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        return self.day in weekdays
    
    def is_weekend(self):
        """Check if this is a weekend"""
        weekends = ["Saturday", "Sunday"]
        return self.day in weekends
    
    def is_available_day(self):
        """Check if this day is available"""
        return bool(self.is_available)
    
    def get_availability_status(self):
        """Get availability status"""
        if not self.is_available:
            return "Unavailable"
        elif self.max_capacity_override:
            return f"Available (Max: {self.max_capacity_override})"
        else:
            return "Available"
    
    def has_capacity_override(self):
        """Check if there's a capacity override"""
        return bool(self.max_capacity_override)
    
    def has_special_notes(self):
        """Check if there are special notes"""
        return bool(self.special_notes)
    
    def get_day_category(self):
        """Get day category for classification"""
        if self.is_weekend():
            return "Weekend"
        elif not self.is_available:
            return "Unavailable"
        else:
            return "Weekday" 