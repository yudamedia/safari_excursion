# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_booking_guest/excursion_booking_guest.py

import frappe
from frappe import _
from frappe.model.document import Document
import re

class ExcursionBookingGuest(Document):
    """
    DocType controller for Excursion Booking Guest
    
    This controller handles guest information for excursion bookings,
    including personal details, contact information, and special requirements.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_guest_details()
        self.validate_contact_information()
        self.validate_age_category()
        self.validate_email()
        self.validate_phone()
    
    def validate_guest_details(self):
        """Validate guest name and basic details"""
        if not self.guest_name:
            frappe.throw(_("Guest Name is required"))
        
        if not self.age_category:
            frappe.throw(_("Age Category is required"))
        
        # Validate age category options
        valid_categories = ["Adult", "Child", "Infant"]
        if self.age_category not in valid_categories:
            frappe.throw(_("Invalid age category selected"))
    
    def validate_contact_information(self):
        """Validate contact information"""
        if self.email and not self.is_valid_email(self.email):
            frappe.throw(_("Invalid email address format"))
        
        if self.phone and not self.is_valid_phone(self.phone):
            frappe.throw(_("Invalid phone number format"))
    
    def validate_age_category(self):
        """Validate age based on age category"""
        if self.age is not None:
            if self.age_category == "Adult" and self.age < 18:
                frappe.msgprint(_("Warning: Age {0} seems low for Adult category").format(self.age), alert=True)
            elif self.age_category == "Child" and (self.age < 2 or self.age > 17):
                frappe.msgprint(_("Warning: Age {0} seems outside Child category range (2-17)").format(self.age), alert=True)
            elif self.age_category == "Infant" and self.age > 2:
                frappe.msgprint(_("Warning: Age {0} seems high for Infant category").format(self.age), alert=True)
    
    def validate_email(self):
        """Validate email format"""
        if self.email and not self.is_valid_email(self.email):
            frappe.throw(_("Please enter a valid email address"))
    
    def validate_phone(self):
        """Validate phone number format"""
        if self.phone and not self.is_valid_phone(self.phone):
            frappe.throw(_("Please enter a valid phone number"))
    
    def is_valid_email(self, email):
        """Check if email format is valid"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_valid_phone(self, phone):
        """Check if phone number format is valid"""
        # Remove spaces, dashes, and parentheses
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        # Check if it contains only digits and optional + at start
        return re.match(r'^\+?[\d]{7,15}$', cleaned_phone) is not None
    
    def get_guest_summary(self):
        """Get a summary of guest information"""
        summary = f"{self.guest_name} ({self.age_category})"
        
        if self.age:
            summary += f" - Age: {self.age}"
        
        if self.nationality:
            summary += f" - {self.nationality}"
        
        if self.dietary_restrictions:
            summary += " - Dietary restrictions"
        
        if self.medical_conditions:
            summary += " - Medical conditions"
        
        return summary
    
    def get_contact_info(self):
        """Get formatted contact information"""
        contact_info = []
        
        if self.phone:
            contact_info.append(f"Phone: {self.phone}")
        
        if self.email:
            contact_info.append(f"Email: {self.email}")
        
        if self.emergency_contact:
            contact_info.append(f"Emergency: {self.emergency_contact}")
        
        return ", ".join(contact_info) if contact_info else "No contact information"
    
    def get_special_requirements(self):
        """Get all special requirements as a list"""
        requirements = []
        
        if self.dietary_restrictions:
            requirements.append(f"Dietary: {self.dietary_restrictions}")
        
        if self.medical_conditions:
            requirements.append(f"Medical: {self.medical_conditions}")
        
        if self.special_requirements:
            requirements.append(f"Special: {self.special_requirements}")
        
        return requirements
    
    def is_adult(self):
        """Check if guest is an adult"""
        return self.age_category == "Adult"
    
    def is_child(self):
        """Check if guest is a child"""
        return self.age_category == "Child"
    
    def is_infant(self):
        """Check if guest is an infant"""
        return self.age_category == "Infant"
    
    def has_special_requirements(self):
        """Check if guest has any special requirements"""
        return bool(self.dietary_restrictions or self.medical_conditions or self.special_requirements) 