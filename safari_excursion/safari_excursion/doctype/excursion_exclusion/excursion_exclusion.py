# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_exclusion/excursion_exclusion.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionExclusion(Document):
    """
    DocType controller for Excursion Exclusion
    
    This controller handles exclusion items for excursions,
    including categories, importance flags, and cost estimates.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_exclusion_details()
        self.validate_category()
        self.validate_display_order()
        self.validate_estimated_cost()
    
    def validate_exclusion_details(self):
        """Validate exclusion item name"""
        if not self.exclusion_item:
            frappe.throw(_("Exclusion Item is required"))
    
    def validate_category(self):
        """Validate exclusion category"""
        valid_categories = [
            "Personal Expenses", "Meals", "Tips", "Insurance", 
            "Equipment Rental", "Extra Activities", "Transport", "Other"
        ]
        
        if self.exclusion_category and self.exclusion_category not in valid_categories:
            frappe.throw(_("Invalid exclusion category selected"))
    
    def validate_display_order(self):
        """Validate display order"""
        if self.display_order is not None and self.display_order < 0:
            frappe.throw(_("Display order cannot be negative"))
    
    def validate_estimated_cost(self):
        """Validate estimated cost"""
        if self.estimated_cost is not None and self.estimated_cost < 0:
            frappe.throw(_("Estimated cost cannot be negative"))
    
    def get_exclusion_summary(self):
        """Get a summary of the exclusion"""
        summary = self.exclusion_item
        
        if self.exclusion_category:
            summary += f" ({self.exclusion_category})"
        
        if self.is_important:
            summary += " - IMPORTANT"
        
        if self.estimated_cost:
            summary += f" - {self.estimated_cost}"
        
        return summary
    
    def get_category_icon(self):
        """Get appropriate icon for the exclusion category"""
        category_icons = {
            "Personal Expenses": "💳",
            "Meals": "🍽️",
            "Tips": "💸",
            "Insurance": "🛡️",
            "Equipment Rental": "🎒",
            "Extra Activities": "🎯",
            "Transport": "🚗",
            "Other": "❌"
        }
        
        return category_icons.get(self.exclusion_category, "❌")
    
    def get_category_color(self):
        """Get color for the exclusion category"""
        category_colors = {
            "Personal Expenses": "red",
            "Meals": "orange",
            "Tips": "yellow",
            "Insurance": "blue",
            "Equipment Rental": "purple",
            "Extra Activities": "green",
            "Transport": "gray",
            "Other": "darkgray"
        }
        
        return category_colors.get(self.exclusion_category, "darkgray")
    
    def is_important_exclusion(self):
        """Check if this is an important exclusion"""
        return bool(self.is_important)
    
    def is_personal_expense_exclusion(self):
        """Check if this is a personal expense exclusion"""
        return self.exclusion_category == "Personal Expenses"
    
    def is_meal_exclusion(self):
        """Check if this is a meal exclusion"""
        return self.exclusion_category == "Meals"
    
    def is_tip_exclusion(self):
        """Check if this is a tip exclusion"""
        return self.exclusion_category == "Tips"
    
    def is_insurance_exclusion(self):
        """Check if this is an insurance exclusion"""
        return self.exclusion_category == "Insurance"
    
    def is_equipment_rental_exclusion(self):
        """Check if this is an equipment rental exclusion"""
        return self.exclusion_category == "Equipment Rental"
    
    def is_extra_activity_exclusion(self):
        """Check if this is an extra activity exclusion"""
        return self.exclusion_category == "Extra Activities"
    
    def is_transport_exclusion(self):
        """Check if this is a transport exclusion"""
        return self.exclusion_category == "Transport"
    
    def get_exclusion_priority(self):
        """Get exclusion priority for display ordering"""
        if self.is_important:
            return 1  # Highest priority
        elif self.exclusion_category in ["Insurance", "Personal Expenses"]:
            return 2  # High priority
        elif self.exclusion_category in ["Meals", "Transport"]:
            return 3  # Medium priority
        else:
            return 4  # Lower priority
    
    def get_display_text(self):
        """Get formatted display text for the exclusion"""
        display_text = self.exclusion_item
        
        if self.description:
            display_text += f" - {self.description}"
        
        if self.estimated_cost:
            display_text += f" (Est: {self.estimated_cost})"
        
        return display_text
    
    def get_full_description(self):
        """Get full description with category and importance"""
        description_parts = []
        
        if self.exclusion_item:
            description_parts.append(self.exclusion_item)
        
        if self.description:
            description_parts.append(self.description)
        
        if self.estimated_cost:
            description_parts.append(f"Est. Cost: {self.estimated_cost}")
        
        if self.is_important:
            description_parts.append("(Important)")
        
        return " | ".join(description_parts) if description_parts else ""
    
    def get_exclusion_type(self):
        """Get exclusion type for classification"""
        if self.is_important:
            return "Important"
        elif self.exclusion_category in ["Insurance", "Personal Expenses"]:
            return "Essential"
        elif self.exclusion_category in ["Meals", "Transport"]:
            return "Standard"
        else:
            return "Optional"
    
    def get_cost_display(self):
        """Get formatted cost display"""
        if not self.estimated_cost:
            return "Cost not specified"
        
        return f"{self.estimated_cost}"
    
    def is_costly_exclusion(self):
        """Check if this is a costly exclusion (>$50)"""
        return self.estimated_cost and self.estimated_cost > 50
    
    def is_affordable_exclusion(self):
        """Check if this is an affordable exclusion (<$20)"""
        return self.estimated_cost and self.estimated_cost < 20
    
    def get_cost_category(self):
        """Get cost category for the exclusion"""
        if not self.estimated_cost:
            return "Unknown"
        elif self.estimated_cost < 10:
            return "Low Cost"
        elif self.estimated_cost < 50:
            return "Medium Cost"
        elif self.estimated_cost < 100:
            return "High Cost"
        else:
            return "Very High Cost" 