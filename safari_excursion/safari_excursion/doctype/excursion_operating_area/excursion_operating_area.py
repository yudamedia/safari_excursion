# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_operating_area/excursion_operating_area.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionOperatingArea(Document):
    """
    DocType controller for Excursion Operating Area
    
    This controller handles operating areas for excursions,
    including area types, travel times, and permit requirements.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_area_details()
        self.validate_travel_information()
        self.validate_area_type()
    
    def validate_area_details(self):
        """Validate area name and basic details"""
        if not self.area_name:
            frappe.throw(_("Area Name is required"))
    
    def validate_travel_information(self):
        """Validate travel time and distance"""
        if self.travel_time_minutes is not None:
            if self.travel_time_minutes < 0:
                frappe.throw(_("Travel time cannot be negative"))
            
            if self.travel_time_minutes > 1440:  # 24 hours
                frappe.msgprint(_("Warning: Travel time seems very long"), alert=True)
        
        if self.distance_km is not None:
            if self.distance_km < 0:
                frappe.throw(_("Distance cannot be negative"))
            
            if self.distance_km > 1000:  # 1000 km
                frappe.msgprint(_("Warning: Distance seems very far"), alert=True)
    
    def validate_area_type(self):
        """Validate area type selection"""
        valid_types = [
            "City", "County", "Region", "National Park", 
            "Marine Park", "Conservancy", "Private Reserve"
        ]
        
        if self.area_type and self.area_type not in valid_types:
            frappe.throw(_("Invalid area type selected"))
    
    def get_area_summary(self):
        """Get a summary of the operating area"""
        summary = self.area_name
        
        if self.area_type:
            summary += f" ({self.area_type})"
        
        if self.travel_time_minutes:
            summary += f" - {self.travel_time_minutes} min"
        
        if self.distance_km:
            summary += f" - {self.distance_km} km"
        
        return summary
    
    def get_travel_info(self):
        """Get formatted travel information"""
        travel_info = []
        
        if self.travel_time_minutes:
            hours = self.travel_time_minutes // 60
            minutes = self.travel_time_minutes % 60
            
            if hours > 0:
                travel_info.append(f"{hours}h {minutes}m")
            else:
                travel_info.append(f"{minutes} minutes")
        
        if self.distance_km:
            travel_info.append(f"{self.distance_km} km")
        
        return " | ".join(travel_info) if travel_info else "No travel info"
    
    def has_permits_required(self):
        """Check if operating permits are required"""
        return bool(self.operating_permits_required)
    
    def has_seasonal_restrictions(self):
        """Check if there are seasonal restrictions"""
        return bool(self.seasonal_restrictions)
    
    def has_special_requirements(self):
        """Check if there are special requirements"""
        return bool(self.special_requirements)
    
    def get_requirements_summary(self):
        """Get summary of all requirements"""
        requirements = []
        
        if self.operating_permits_required:
            requirements.append(f"Permits: {self.operating_permits_required}")
        
        if self.seasonal_restrictions:
            requirements.append(f"Seasonal: {self.seasonal_restrictions}")
        
        if self.special_requirements:
            requirements.append(f"Special: {self.special_requirements}")
        
        return " | ".join(requirements) if requirements else "No special requirements"
    
    def is_protected_area(self):
        """Check if this is a protected area"""
        protected_types = ["National Park", "Marine Park", "Conservancy", "Private Reserve"]
        return self.area_type in protected_types
    
    def is_urban_area(self):
        """Check if this is an urban area"""
        urban_types = ["City", "County"]
        return self.area_type in urban_types
    
    def get_area_category(self):
        """Get area category for classification"""
        if self.is_protected_area():
            return "Protected"
        elif self.is_urban_area():
            return "Urban"
        else:
            return "Regional" 