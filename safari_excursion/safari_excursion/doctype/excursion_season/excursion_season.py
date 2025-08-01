# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_season/excursion_season.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

class ExcursionSeason(Document):
    def validate(self):
        self.validate_dates()
        self.validate_locations()
    
    def validate_dates(self):
        """Validate that start date is before end date"""
        if self.start_date and self.end_date:
            if getdate(self.start_date) >= getdate(self.end_date):
                frappe.throw(_("Start date must be before end date"))
    
    def validate_locations(self):
        """Validate that at least one primary location is set"""
        if self.applicable_locations:
            primary_locations = [loc for loc in self.applicable_locations if loc.is_primary]
            if not primary_locations:
                frappe.throw(_("At least one primary location must be set"))
    
    def is_date_in_season(self, check_date):
        """Check if a given date falls within this season"""
        if not self.is_active:
            return False
        
        check_date = getdate(check_date)
        start_date = getdate(self.start_date)
        end_date = getdate(self.end_date)
        
        return start_date <= check_date <= end_date
    
    def get_season_type_display(self):
        """Get a user-friendly display name for the season type"""
        season_type_map = {
            "High": "High Season",
            "Peak": "Peak Season", 
            "Low": "Low Season",
            "Shoulder": "Shoulder Season",
            "Green": "Green Season",
            "Special": "Special Season"
        }
        return season_type_map.get(self.season_type, self.season_type)
    
    def get_primary_location(self):
        """Get the primary location for this season"""
        if self.applicable_locations:
            for location in self.applicable_locations:
                if location.is_primary:
                    return location.location_name
        return None 