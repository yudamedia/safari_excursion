# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_guest_requirement/excursion_guest_requirement.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionGuestRequirement(Document):
    """
    DocType controller for Excursion Guest Requirement
    
    This controller handles guest requirements for excursions,
    including mandatory and recommended items that guests should bring.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_requirement_details()
        self.validate_category()
        self.validate_flags()
    
    def validate_requirement_details(self):
        """Validate requirement item name"""
        if not self.requirement_item:
            frappe.throw(_("Requirement Item is required"))
    
    def validate_category(self):
        """Validate requirement category"""
        valid_categories = [
            "Clothing", "Footwear", "Sun Protection", "Personal Items",
            "Medication", "Documents", "Food & Drinks", "Technology", "Other"
        ]
        
        if self.requirement_category and self.requirement_category not in valid_categories:
            frappe.throw(_("Invalid requirement category selected"))
    
    def validate_flags(self):
        """Validate mandatory and recommended flags"""
        # If mandatory is checked, recommended should also be checked
        if self.is_mandatory and not self.is_recommended:
            self.is_recommended = 1
            frappe.msgprint(_("Recommended flag automatically set for mandatory items"), alert=True)
    
    def get_requirement_summary(self):
        """Get a summary of the requirement"""
        summary = self.requirement_item
        
        if self.requirement_category:
            summary += f" ({self.requirement_category})"
        
        if self.is_mandatory:
            summary += " - MANDATORY"
        elif self.is_recommended:
            summary += " - Recommended"
        
        return summary
    
    def get_priority_level(self):
        """Get priority level for sorting"""
        if self.is_mandatory:
            return 1  # Highest priority
        elif self.is_recommended:
            return 2  # Medium priority
        else:
            return 3  # Lowest priority
    
    def get_category_icon(self):
        """Get appropriate icon for the category"""
        category_icons = {
            "Clothing": "👕",
            "Footwear": "👟",
            "Sun Protection": "☀️",
            "Personal Items": "🧴",
            "Medication": "💊",
            "Documents": "📄",
            "Food & Drinks": "🍎",
            "Technology": "📱",
            "Other": "📦"
        }
        
        return category_icons.get(self.requirement_category, "📦")
    
    def is_mandatory_requirement(self):
        """Check if this is a mandatory requirement"""
        return bool(self.is_mandatory)
    
    def is_recommended_requirement(self):
        """Check if this is a recommended requirement"""
        return bool(self.is_recommended)
    
    def get_full_description(self):
        """Get full description with additional details"""
        description_parts = []
        
        if self.description:
            description_parts.append(self.description)
        
        if self.where_to_buy:
            description_parts.append(f"Where to get: {self.where_to_buy}")
        
        return " | ".join(description_parts) if description_parts else ""
    
    def get_requirement_type(self):
        """Get the type of requirement"""
        if self.is_mandatory:
            return "Mandatory"
        elif self.is_recommended:
            return "Recommended"
        else:
            return "Optional" 