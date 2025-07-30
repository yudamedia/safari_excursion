# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_pickup_location/excursion_pickup_location.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionPickupLocation(Document):
    """
    DocType controller for Excursion Pickup Location
    
    This controller handles pickup location details for excursion packages,
    including location information, timing adjustments, and additional charges.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_location_details()
        self.validate_timing_adjustment()
        self.validate_additional_charge()
    
    def validate_location_details(self):
        """Validate location name and type"""
        if not self.location_name:
            frappe.throw(_("Location Name is required"))
        
        if self.location_type and self.location_type not in [
            "Hotel", "Resort", "Airport", "Train Station", 
            "Bus Station", "City Center", "Landmark", "Other"
        ]:
            frappe.throw(_("Invalid location type selected"))
    
    def validate_timing_adjustment(self):
        """Validate pickup time adjustment"""
        if self.pickup_time_adjustment is not None:
            if self.pickup_time_adjustment < -120 or self.pickup_time_adjustment > 120:
                frappe.throw(_("Pickup time adjustment must be between -120 and 120 minutes"))
    
    def validate_additional_charge(self):
        """Validate additional charge amount"""
        if self.additional_charge is not None and self.additional_charge < 0:
            frappe.throw(_("Additional charge cannot be negative"))
    
    def get_full_address(self):
        """Get complete address string"""
        address_parts = []
        
        if self.address:
            address_parts.append(self.address)
        
        if self.landmark:
            address_parts.append(f"Near: {self.landmark}")
        
        if self.gps_coordinates:
            address_parts.append(f"GPS: {self.gps_coordinates}")
        
        return ", ".join(address_parts) if address_parts else ""
    
    def get_location_summary(self):
        """Get a summary of the location for display"""
        summary = self.location_name
        
        if self.location_type:
            summary += f" ({self.location_type})"
        
        if self.additional_charge and self.additional_charge > 0:
            summary += f" - Additional: {self.additional_charge}"
        
        return summary 