# Copyright (c) 2025, Safari Management and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionSettings(Document):
    def validate(self):
        """Validate settings before saving"""
        self.validate_percentages()
        self.validate_time_settings()
        self.validate_group_discount_tiers()
        self.validate_transport_zones()
    
    def validate_percentages(self):
        """Validate percentage fields"""
        percentage_fields = [
            'child_discount_percentage',
            'early_morning_premium',
            'late_evening_premium',
            'cancellation_charge_percentage',
            'no_show_charge_percentage',
            'advance_payment_percentage'
        ]
        
        for field in percentage_fields:
            value = self.get(field)
            if value is not None and (value < 0 or value > 100):
                frappe.throw(_("{0} must be between 0 and 100").format(
                    self.meta.get_label(field)
                ))
    
    def validate_time_settings(self):
        """Validate time-related settings"""
        if self.early_morning_cutoff and self.late_evening_cutoff:
            if self.early_morning_cutoff >= self.late_evening_cutoff:
                frappe.throw(_("Early morning cutoff must be before late evening cutoff"))
    
    def validate_group_discount_tiers(self):
        """Validate group discount tier configuration"""
        if not self.enable_group_discounts:
            return
            
        if not self.group_discount_tiers:
            frappe.throw(_("Group discount tiers are required when group discounts are enabled"))
        
        # Check for duplicate minimum group sizes
        sizes = []
        for tier in self.group_discount_tiers:
            if tier.minimum_group_size in sizes:
                frappe.throw(_("Duplicate minimum group size: {0}").format(tier.minimum_group_size))
            sizes.append(tier.minimum_group_size)
            
            # Validate discount percentage
            if tier.discount_percentage < 0 or tier.discount_percentage > 100:
                frappe.throw(_("Discount percentage must be between 0 and 100"))
    
    def validate_transport_zones(self):
        """Validate transport zone configuration"""
        if not self.enable_transport_zones:
            return
            
        zone_names = []
        for zone in self.transport_zones:
            if zone.zone_name in zone_names:
                frappe.throw(_("Duplicate zone name: {0}").format(zone.zone_name))
            zone_names.append(zone.zone_name)
            
            if zone.additional_charge < 0:
                frappe.throw(_("Additional charge cannot be negative"))

@frappe.whitelist()
def get_excursion_settings():
    """Get excursion settings for use in other modules"""
    return frappe.get_single("Excursion Settings")