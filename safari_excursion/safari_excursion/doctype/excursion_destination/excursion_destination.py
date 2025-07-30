# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_destination/excursion_destination.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionDestination(Document):
    """
    DocType controller for Excursion Destination
    
    This controller handles destination locations for excursions,
    including location types, activities, and special requirements.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_destination_details()
        self.validate_location_type()
        self.validate_duration()
        self.validate_entrance_fee()
    
    def validate_destination_details(self):
        """Validate destination name and basic details"""
        if not self.location_name:
            frappe.throw(_("Location Name is required"))
    
    def validate_location_type(self):
        """Validate location type selection"""
        valid_types = [
            "Tourist Attraction", "National Park", "Marine Park", "Conservancy",
            "Beach", "Historical Site", "Cultural Site", "Adventure Site"
        ]
        
        if not self.location_type:
            frappe.throw(_("Location Type is required"))
        
        if self.location_type not in valid_types:
            frappe.throw(_("Invalid location type selected"))
    
    def validate_duration(self):
        """Validate duration hours"""
        if self.duration_hours is not None:
            if self.duration_hours <= 0:
                frappe.throw(_("Duration must be greater than 0"))
            
            if self.duration_hours > 24:
                frappe.msgprint(_("Warning: Duration seems very long for a single destination"), alert=True)
    
    def validate_entrance_fee(self):
        """Validate entrance fee inclusion based on location type"""
        protected_areas = ["National Park", "Marine Park", "Conservancy"]
        
        if self.location_type in protected_areas:
            # For protected areas, entrance fee inclusion should be considered
            if not self.entrance_fee_included:
                frappe.msgprint(_("Note: Entrance fees for {0} may apply").format(self.location_type), alert=True)
    
    def get_destination_summary(self):
        """Get a summary of the destination"""
        summary = self.location_name
        
        if self.location_type:
            summary += f" ({self.location_type})"
        
        if self.duration_hours:
            summary += f" - {self.duration_hours}h"
        
        if self.is_main_destination:
            summary += " - MAIN DESTINATION"
        
        return summary
    
    def get_activities_summary(self):
        """Get formatted activities summary"""
        if not self.activities:
            return "No specific activities listed"
        
        return self.activities
    
    def get_requirements_summary(self):
        """Get formatted requirements summary"""
        requirements = []
        
        if self.special_requirements:
            requirements.append(self.special_requirements)
        
        if self.location_type in ["National Park", "Marine Park", "Conservancy"]:
            if self.entrance_fee_included:
                requirements.append("Entrance fee included")
            else:
                requirements.append("Entrance fee may apply")
        
        return " | ".join(requirements) if requirements else "No special requirements"
    
    def is_protected_area(self):
        """Check if this is a protected area"""
        protected_types = ["National Park", "Marine Park", "Conservancy"]
        return self.location_type in protected_types
    
    def is_cultural_site(self):
        """Check if this is a cultural site"""
        cultural_types = ["Historical Site", "Cultural Site"]
        return self.location_type in cultural_types
    
    def is_adventure_site(self):
        """Check if this is an adventure site"""
        return self.location_type == "Adventure Site"
    
    def is_natural_attraction(self):
        """Check if this is a natural attraction"""
        natural_types = ["National Park", "Marine Park", "Conservancy", "Beach"]
        return self.location_type in natural_types
    
    def get_destination_category(self):
        """Get destination category for classification"""
        if self.is_protected_area():
            return "Protected Area"
        elif self.is_cultural_site():
            return "Cultural Site"
        elif self.is_adventure_site():
            return "Adventure Site"
        elif self.is_natural_attraction():
            return "Natural Attraction"
        else:
            return "Tourist Attraction"
    
    def get_duration_display(self):
        """Get formatted duration display"""
        if not self.duration_hours:
            return "Duration not specified"
        
        hours = int(self.duration_hours)
        minutes = int((self.duration_hours - hours) * 60)
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours} hours"
        else:
            return f"{minutes} minutes"
    
    def get_location_type_icon(self):
        """Get appropriate icon for the location type"""
        type_icons = {
            "Tourist Attraction": "🏛️",
            "National Park": "🌲",
            "Marine Park": "🐠",
            "Conservancy": "🦁",
            "Beach": "🏖️",
            "Historical Site": "🏺",
            "Cultural Site": "🎭",
            "Adventure Site": "🧗"
        }
        
        return type_icons.get(self.location_type, "📍")
    
    def is_main_destination(self):
        """Check if this is the main destination"""
        return bool(self.is_main_destination)
    
    def has_entrance_fee(self):
        """Check if entrance fee is included"""
        return bool(self.entrance_fee_included)
    
    def get_destination_priority(self):
        """Get destination priority for itinerary planning"""
        if self.is_main_destination:
            return 1  # Highest priority
        elif self.is_protected_area():
            return 2  # High priority
        elif self.is_cultural_site():
            return 3  # Medium priority
        else:
            return 4  # Lower priority 