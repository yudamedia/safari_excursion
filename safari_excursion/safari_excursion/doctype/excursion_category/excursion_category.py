import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionCategory(Document):
    def validate(self):
        if not self.category_name:
            frappe.throw(_("Category Name is required"))
        if self.default_duration_hours is not None and self.default_duration_hours <= 0:
            frappe.throw(_("Default duration must be greater than 0"))
        self.validate_fitness_level()
    
    def validate_fitness_level(self):
        valid_levels = ["", "Low", "Moderate", "High", "Very High"]
        if self.fitness_level_required and self.fitness_level_required not in valid_levels:
            frappe.throw(_("Invalid fitness level selected"))
    
    def get_category_summary(self):
        summary = self.category_name
        if self.default_duration_hours:
            summary += f" ({self.default_duration_hours}h)"
        if self.requires_guide:
            summary += " - Guide Required"
        if self.requires_vehicle:
            summary += " - Vehicle Required"
        return summary
    
    def requires_guide_service(self):
        return bool(self.requires_guide)
    
    def requires_vehicle_service(self):
        return bool(self.requires_vehicle)
    
    def is_active_category(self):
        return bool(self.is_active)
    
    def get_fitness_level_display(self):
        if not self.fitness_level_required:
            return "Not specified"
        return self.fitness_level_required
    
    def get_category_icon(self):
        icons = {
            "Safari": "🦁",
            "Adventure": "🧗",
            "Cultural": "🏺",
            "Nature": "🌲",
            "Water": "🏊",
            "Photography": "📷",
            "Educational": "📚",
            "Relaxation": "🧘"
        }
        return icons.get(self.category_name, "🏷️") 