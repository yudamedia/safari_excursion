# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_departure_time/excursion_departure_time.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time

class ExcursionDepartureTime(Document):
    """
    DocType controller for Excursion Departure Time
    
    This controller handles departure time configurations for excursions,
    including time labels, availability, and premium charges.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_departure_time()
        self.validate_time_label()
        self.validate_capacity()
        self.validate_premium_charge()
        self.set_default_time_label()
    
    def validate_departure_time(self):
        """Validate departure time"""
        if not self.departure_time:
            frappe.throw(_("Departure Time is required"))
        
        # Validate time format
        try:
            get_time(self.departure_time)
        except:
            frappe.throw(_("Invalid departure time format"))
    
    def validate_time_label(self):
        """Validate time label"""
        if not self.time_label:
            # Auto-generate time label if not provided
            self.time_label = self.generate_time_label()
    
    def validate_capacity(self):
        """Validate maximum capacity"""
        if self.max_capacity is not None and self.max_capacity <= 0:
            frappe.throw(_("Maximum capacity must be greater than 0"))
    
    def validate_premium_charge(self):
        """Validate premium charge"""
        if self.premium_charge is not None and self.premium_charge < 0:
            frappe.throw(_("Premium charge cannot be negative"))
    
    def set_default_time_label(self):
        """Set default time label if not provided"""
        if not self.time_label:
            self.time_label = self.generate_time_label()
    
    def generate_time_label(self):
        """Generate a user-friendly time label"""
        if not self.departure_time:
            return ""
        
        time_obj = get_time(self.departure_time)
        hour = time_obj.hour
        
        if hour < 12:
            period = "AM"
            if hour == 0:
                hour = 12
        else:
            period = "PM"
            if hour > 12:
                hour -= 12
        
        return f"{hour}:{time_obj.minute:02d} {period}"
    
    def is_available_on_day(self, day_of_week):
        """Check if departure time is available on specific day"""
        if not self.available_days or self.available_days == "All Days":
            return True
        
        if self.available_days == "Weekdays Only":
            return day_of_week in [0, 1, 2, 3, 4]  # Monday to Friday
        
        if self.available_days == "Weekends Only":
            return day_of_week in [5, 6]  # Saturday and Sunday
        
        # For custom availability, additional logic would be needed
        return True
    
    def get_display_time(self):
        """Get formatted display time"""
        if not self.departure_time:
            return ""
        
        time_obj = get_time(self.departure_time)
        return time_obj.strftime("%I:%M %p")
    
    def get_summary(self):
        """Get summary of departure time configuration"""
        summary = self.get_display_time()
        
        if self.time_label and self.time_label != summary:
            summary += f" ({self.time_label})"
        
        if self.max_capacity:
            summary += f" - Max: {self.max_capacity}"
        
        if self.premium_charge and self.premium_charge > 0:
            summary += f" - Premium: {self.premium_charge}"
        
        if not self.is_active:
            summary += " - Inactive"
        
        return summary
    
    def is_default_time(self):
        """Check if this is the default departure time"""
        return bool(self.is_default) 