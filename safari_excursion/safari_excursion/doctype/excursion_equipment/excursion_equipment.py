import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionEquipment(Document):
    def validate(self):
        if not self.equipment_name:
            frappe.throw(_("Equipment Name is required"))
        if self.quantity_included is not None and self.quantity_included <= 0:
            frappe.throw(_("Quantity included must be greater than 0"))
        if self.rental_cost is not None and self.rental_cost < 0:
            frappe.throw(_("Rental cost cannot be negative"))
        if self.replacement_value is not None and self.replacement_value < 0:
            frappe.throw(_("Replacement value cannot be negative"))
    
    def get_equipment_summary(self):
        summary = self.equipment_name
        if self.equipment_category:
            summary += f" ({self.equipment_category})"
        if self.quantity_included:
            summary += f" - Qty: {self.quantity_included}"
        if self.per_person:
            summary += " - Per Person"
        return summary
    
    def is_per_person_equipment(self):
        return bool(self.per_person)
    
    def get_category_icon(self):
        icons = {
            "Safety Equipment": "🛡️",
            "Sports Equipment": "⚽",
            "Photography": "📷",
            "Navigation": "🧭",
            "Comfort Items": "🪑",
            "Educational": "📚",
            "Other": "📦"
        }
        return icons.get(self.equipment_category, "📦") 