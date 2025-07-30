# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_season/excursion_season.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, add_days

class ExcursionSeason(Document):
    """
    DocType controller for Excursion Season
    
    This controller handles seasonal availability for excursions,
    including date ranges, capacity adjustments, and weather conditions.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_season_details()
        self.validate_date_range()
        self.validate_capacity_adjustment()
        self.check_date_overlaps()
    
    def validate_season_details(self):
        """Validate season name and basic details"""
        if not self.season_name:
            frappe.throw(_("Season Name is required"))
    
    def validate_date_range(self):
        """Validate start and end dates"""
        if not self.start_date:
            frappe.throw(_("Start Date is required"))
        
        if not self.end_date:
            frappe.throw(_("End Date is required"))
        
        if getdate(self.start_date) >= getdate(self.end_date):
            frappe.throw(_("End Date must be after Start Date"))
        
        # Check if season spans multiple years
        start_year = getdate(self.start_date).year
        end_year = getdate(self.end_date).year
        if end_year - start_year > 1:
            frappe.msgprint(_("Warning: Season spans multiple years"), alert=True)
    
    def validate_capacity_adjustment(self):
        """Validate capacity adjustment percentage"""
        if self.capacity_adjustment is not None:
            if self.capacity_adjustment < -100:
                frappe.throw(_("Capacity adjustment cannot be less than -100%"))
            
            if self.capacity_adjustment > 200:
                frappe.msgprint(_("Warning: Capacity adjustment seems very high"), alert=True)
    
    def check_date_overlaps(self):
        """Check for overlapping date ranges with other seasons"""
        # This would need to be implemented based on the parent document context
        # For now, we'll just validate the individual record
        pass
    
    def is_date_in_season(self, check_date):
        """Check if a given date falls within this season"""
        if not self.start_date or not self.end_date:
            return False
        
        check_date = getdate(check_date)
        start_date = getdate(self.start_date)
        end_date = getdate(self.end_date)
        
        return start_date <= check_date <= end_date
    
    def get_season_summary(self):
        """Get a summary of the season"""
        summary = self.season_name
        
        if self.start_date and self.end_date:
            summary += f" ({self.start_date} to {self.end_date})"
        
        if not self.is_available:
            summary += " - UNAVAILABLE"
        
        if self.capacity_adjustment:
            if self.capacity_adjustment > 0:
                summary += f" - +{self.capacity_adjustment}% capacity"
            else:
                summary += f" - {self.capacity_adjustment}% capacity"
        
        return summary
    
    def get_season_duration_days(self):
        """Get the duration of the season in days"""
        if not self.start_date or not self.end_date:
            return 0
        
        start = getdate(self.start_date)
        end = getdate(self.end_date)
        
        # Calculate days difference
        delta = end - start
        return delta.days + 1  # Include both start and end dates
    
    def get_season_duration_months(self):
        """Get the duration of the season in months"""
        if not self.start_date or not self.end_date:
            return 0
        
        start = getdate(self.start_date)
        end = getdate(self.end_date)
        
        # Calculate months difference
        months = (end.year - start.year) * 12 + (end.month - start.month)
        if end.day < start.day:
            months -= 1
        
        return max(0, months)
    
    def is_current_season(self):
        """Check if this season is currently active"""
        today = getdate()
        return self.is_date_in_season(today)
    
    def is_future_season(self):
        """Check if this season is in the future"""
        today = getdate()
        return getdate(self.start_date) > today
    
    def is_past_season(self):
        """Check if this season is in the past"""
        today = getdate()
        return getdate(self.end_date) < today
    
    def get_capacity_multiplier(self):
        """Get capacity multiplier based on adjustment"""
        if self.capacity_adjustment is None:
            return 1.0
        
        return 1.0 + (self.capacity_adjustment / 100.0)
    
    def get_adjusted_capacity(self, base_capacity):
        """Get adjusted capacity based on season adjustment"""
        if not base_capacity:
            return 0
        
        multiplier = self.get_capacity_multiplier()
        return int(base_capacity * multiplier)
    
    def get_season_status(self):
        """Get current season status"""
        if not self.is_available:
            return "Unavailable"
        
        if self.is_current_season():
            return "Active"
        elif self.is_future_season():
            return "Upcoming"
        elif self.is_past_season():
            return "Past"
        else:
            return "Unknown"
    
    def get_season_status_color(self):
        """Get color for season status display"""
        status_colors = {
            "Active": "green",
            "Upcoming": "blue",
            "Past": "gray",
            "Unavailable": "red",
            "Unknown": "orange"
        }
        
        return status_colors.get(self.get_season_status(), "gray")
    
    def get_weather_summary(self):
        """Get weather conditions summary"""
        if not self.weather_conditions:
            return "Weather conditions not specified"
        
        return self.weather_conditions
    
    def is_peak_season(self):
        """Check if this is a peak season (positive capacity adjustment)"""
        return self.capacity_adjustment and self.capacity_adjustment > 0
    
    def is_low_season(self):
        """Check if this is a low season (negative capacity adjustment)"""
        return self.capacity_adjustment and self.capacity_adjustment < 0
    
    def is_standard_season(self):
        """Check if this is a standard season (no capacity adjustment)"""
        return not self.capacity_adjustment or self.capacity_adjustment == 0
    
    def get_season_type(self):
        """Get season type classification"""
        if not self.is_available:
            return "Unavailable"
        elif self.is_peak_season():
            return "Peak Season"
        elif self.is_low_season():
            return "Low Season"
        else:
            return "Standard Season"
    
    def get_days_until_start(self):
        """Get number of days until season starts"""
        if not self.start_date:
            return None
        
        today = getdate()
        start_date = getdate(self.start_date)
        
        if start_date <= today:
            return 0
        
        delta = start_date - today
        return delta.days
    
    def get_days_until_end(self):
        """Get number of days until season ends"""
        if not self.end_date:
            return None
        
        today = getdate()
        end_date = getdate(self.end_date)
        
        if end_date <= today:
            return 0
        
        delta = end_date - today
        return delta.days 