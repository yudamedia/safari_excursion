# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_inclusion/excursion_inclusion.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionInclusion(Document):
    """
    DocType controller for Excursion Inclusion
    
    This controller handles inclusion items for excursions,
    including categories, highlighting, and display ordering.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_inclusion_details()
        self.validate_category()
        self.validate_display_order()
    
    def validate_inclusion_details(self):
        """Validate inclusion item name"""
        if not self.inclusion_item:
            frappe.throw(_("Inclusion Item is required"))
    
    def validate_category(self):
        """Validate inclusion category"""
        valid_categories = [
            "Transport", "Meals", "Activities", "Equipment", 
            "Guide Services", "Entrance Fees", "Accommodation", "Other"
        ]
        
        if self.inclusion_category and self.inclusion_category not in valid_categories:
            frappe.throw(_("Invalid inclusion category selected"))
    
    def validate_display_order(self):
        """Validate display order"""
        if self.display_order is not None and self.display_order < 0:
            frappe.throw(_("Display order cannot be negative"))
    
    def get_inclusion_summary(self):
        """Get a summary of the inclusion"""
        summary = self.inclusion_item
        
        if self.inclusion_category:
            summary += f" ({self.inclusion_category})"
        
        if self.is_highlighted:
            summary += " - HIGHLIGHTED"
        
        return summary
    
    def get_category_icon(self):
        """Get appropriate icon for the inclusion category"""
        category_icons = {
            "Transport": "🚗",
            "Meals": "🍽️",
            "Activities": "🎯",
            "Equipment": "🎒",
            "Guide Services": "👨‍🏫",
            "Entrance Fees": "🎫",
            "Accommodation": "🏨",
            "Other": "📋"
        }
        
        return category_icons.get(self.inclusion_category, "📋")
    
    def get_category_color(self):
        """Get color for the inclusion category"""
        category_colors = {
            "Transport": "blue",
            "Meals": "orange",
            "Activities": "green",
            "Equipment": "purple",
            "Guide Services": "teal",
            "Entrance Fees": "yellow",
            "Accommodation": "pink",
            "Other": "gray"
        }
        
        return category_colors.get(self.inclusion_category, "gray")
    
    def is_highlighted_inclusion(self):
        """Check if this is a highlighted inclusion"""
        return bool(self.is_highlighted)
    
    def is_transport_inclusion(self):
        """Check if this is a transport inclusion"""
        return self.inclusion_category == "Transport"
    
    def is_meal_inclusion(self):
        """Check if this is a meal inclusion"""
        return self.inclusion_category == "Meals"
    
    def is_activity_inclusion(self):
        """Check if this is an activity inclusion"""
        return self.inclusion_category == "Activities"
    
    def is_equipment_inclusion(self):
        """Check if this is an equipment inclusion"""
        return self.inclusion_category == "Equipment"
    
    def is_guide_service_inclusion(self):
        """Check if this is a guide service inclusion"""
        return self.inclusion_category == "Guide Services"
    
    def is_entrance_fee_inclusion(self):
        """Check if this is an entrance fee inclusion"""
        return self.inclusion_category == "Entrance Fees"
    
    def is_accommodation_inclusion(self):
        """Check if this is an accommodation inclusion"""
        return self.inclusion_category == "Accommodation"
    
    def get_inclusion_priority(self):
        """Get inclusion priority for display ordering"""
        if self.is_highlighted:
            return 1  # Highest priority
        elif self.inclusion_category in ["Transport", "Guide Services"]:
            return 2  # High priority
        elif self.inclusion_category in ["Meals", "Accommodation"]:
            return 3  # Medium priority
        else:
            return 4  # Lower priority
    
    def get_display_text(self):
        """Get formatted display text for the inclusion"""
        display_text = self.inclusion_item
        
        if self.description:
            display_text += f" - {self.description}"
        
        return display_text
    
    def get_full_description(self):
        """Get full description with category and highlighting"""
        description_parts = []
        
        if self.inclusion_item:
            description_parts.append(self.inclusion_item)
        
        if self.description:
            description_parts.append(self.description)
        
        if self.is_highlighted:
            description_parts.append("(Highlighted)")
        
        return " | ".join(description_parts) if description_parts else ""
    
    def get_inclusion_type(self):
        """Get inclusion type for classification"""
        if self.is_highlighted:
            return "Highlighted"
        elif self.inclusion_category in ["Transport", "Guide Services"]:
            return "Essential"
        elif self.inclusion_category in ["Meals", "Accommodation"]:
            return "Comfort"
        else:
            return "Additional" 