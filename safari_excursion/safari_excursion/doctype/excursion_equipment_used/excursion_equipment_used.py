# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_equipment_used/excursion_equipment_used.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionEquipmentUsed(Document):
    """
    DocType controller for Excursion Equipment Used
    
    This controller handles tracking of equipment used during excursions,
    including condition monitoring and replacement needs.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_equipment_details()
        self.validate_quantity()
        self.validate_condition_tracking()
        self.set_replacement_flag()
    
    def validate_equipment_details(self):
        """Validate equipment name"""
        if not self.equipment_name:
            frappe.throw(_("Equipment Name is required"))
    
    def validate_quantity(self):
        """Validate quantity used"""
        if not self.quantity_used or self.quantity_used <= 0:
            frappe.throw(_("Quantity Used must be greater than 0"))
    
    def validate_condition_tracking(self):
        """Validate condition tracking fields"""
        valid_conditions = ["Excellent", "Good", "Fair", "Poor"]
        
        if self.condition_before and self.condition_before not in valid_conditions:
            frappe.throw(_("Invalid condition before value"))
        
        valid_conditions_after = valid_conditions + ["Damaged", "Lost"]
        if self.condition_after and self.condition_after not in valid_conditions_after:
            frappe.throw(_("Invalid condition after value"))
    
    def set_replacement_flag(self):
        """Set replacement needed flag based on condition"""
        if self.condition_after in ["Damaged", "Lost"]:
            self.replacement_needed = 1
        elif self.condition_after == "Poor":
            # Auto-set replacement needed for poor condition
            self.replacement_needed = 1
    
    def get_condition_summary(self):
        """Get a summary of equipment condition"""
        summary = f"{self.equipment_name} (Qty: {self.quantity_used})"
        
        if self.condition_before and self.condition_after:
            summary += f" - {self.condition_before} → {self.condition_after}"
        
        if self.replacement_needed:
            summary += " - Replacement Needed"
        
        return summary
    
    def get_equipment_status(self):
        """Get equipment status for reporting"""
        if self.condition_after == "Damaged":
            return "Damaged"
        elif self.condition_after == "Lost":
            return "Lost"
        elif self.replacement_needed:
            return "Needs Replacement"
        else:
            return "OK" 