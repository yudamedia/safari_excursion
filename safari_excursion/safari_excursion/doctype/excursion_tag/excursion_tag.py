# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_tag/excursion_tag.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionTag(Document):
    """
    DocType controller for Excursion Tag
    
    This controller handles tags for excursions,
    including tag colors, searchability, and display priority.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_tag_details()
        self.validate_display_priority()
        self.set_default_values()
    
    def validate_tag_details(self):
        """Validate tag name"""
        if not self.tag_name:
            frappe.throw(_("Tag Name is required"))
        
        # Check for duplicate tag names
        self.validate_tag_name_uniqueness()
    
    def validate_tag_name_uniqueness(self):
        """Validate that tag name is unique"""
        existing = frappe.get_all("Excursion Tag", {
            "tag_name": self.tag_name,
            "name": ["!=", self.name]
        })
        
        if existing:
            frappe.throw(_("Tag Name '{0}' already exists").format(self.tag_name))
    
    def validate_display_priority(self):
        """Validate display priority"""
        if self.display_priority is not None and self.display_priority < 0:
            frappe.throw(_("Display priority cannot be negative"))
    
    def set_default_values(self):
        """Set default values for various fields"""
        if self.is_searchable is None:
            self.is_searchable = 1
        
        if not self.tag_color:
            self.tag_color = "#6c757d"  # Default gray color
    
    def get_tag_summary(self):
        """Get a summary of the tag"""
        summary = self.tag_name
        
        if self.display_priority:
            summary += f" (Priority: {self.display_priority})"
        
        if not self.is_searchable:
            summary += " - Not Searchable"
        
        return summary
    
    def get_tag_display(self):
        """Get formatted tag display with color"""
        display = self.tag_name
        
        if self.tag_color:
            display = f'<span style="color: {self.tag_color};">{self.tag_name}</span>'
        
        return display
    
    def is_searchable_tag(self):
        """Check if this tag is searchable"""
        return bool(self.is_searchable)
    
    def get_tag_priority_level(self):
        """Get priority level for sorting"""
        if not self.display_priority:
            return 999  # Lowest priority
        
        return self.display_priority
    
    def get_tag_color_code(self):
        """Get tag color code"""
        return self.tag_color or "#6c757d"
    
    def get_tag_style(self):
        """Get CSS style for the tag"""
        if not self.tag_color:
            return ""
        
        return f"color: {self.tag_color};"
    
    def is_high_priority_tag(self):
        """Check if this is a high priority tag"""
        return self.display_priority and self.display_priority <= 5
    
    def is_medium_priority_tag(self):
        """Check if this is a medium priority tag"""
        return self.display_priority and 6 <= self.display_priority <= 10
    
    def is_low_priority_tag(self):
        """Check if this is a low priority tag"""
        return not self.display_priority or self.display_priority > 10
    
    def get_tag_category(self):
        """Get tag category based on priority"""
        if self.is_high_priority_tag():
            return "High Priority"
        elif self.is_medium_priority_tag():
            return "Medium Priority"
        else:
            return "Low Priority"
    
    def get_usage_count(self):
        """Get count of excursions using this tag"""
        # This would need to be implemented based on how tags are linked to excursions
        return 0
    
    def get_related_excursions(self):
        """Get related excursions using this tag"""
        # This would need to be implemented based on how tags are linked to excursions
        return []
    
    def duplicate_tag(self):
        """Create a duplicate of this tag"""
        new_tag = frappe.copy_doc(self)
        new_tag.tag_name = f"{self.tag_name} (Copy)"
        new_tag.display_priority = (self.display_priority or 0) + 1
        new_tag.insert()
        
        frappe.msgprint(_("Tag duplicated successfully"))
        return new_tag.name
    
    def toggle_searchability(self):
        """Toggle searchability of the tag"""
        self.is_searchable = not self.is_searchable
        self.save()
        
        status = "searchable" if self.is_searchable else "not searchable"
        frappe.msgprint(_("Tag marked as {0}").format(status))
    
    def get_tag_info(self):
        """Get comprehensive tag information"""
        return {
            "name": self.tag_name,
            "color": self.tag_color,
            "searchable": self.is_searchable,
            "priority": self.display_priority,
            "category": self.get_tag_category(),
            "usage_count": self.get_usage_count()
        } 