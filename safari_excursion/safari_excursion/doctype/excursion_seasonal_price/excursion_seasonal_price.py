# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_seasonal_price/excursion_seasonal_price.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, add_days

class ExcursionSeasonalPrice(Document):
    """
    DocType controller for Excursion Seasonal Price
    
    This controller handles seasonal pricing for excursions,
    including fixed prices and percentage-based adjustments.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_season_details()
        self.validate_date_range()
        self.validate_pricing()
        self.validate_percentage_change()
    
    def validate_season_details(self):
        """Validate season name"""
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
        
        # Check for overlapping seasons
        self.check_date_overlaps()
    
    def validate_pricing(self):
        """Validate pricing based on price type"""
        if not self.price_type:
            frappe.throw(_("Price Type is required"))
        
        if self.price_type == "Fixed":
            if self.adult_price is None or self.adult_price < 0:
                frappe.throw(_("Adult Price must be greater than or equal to 0"))
            
            if self.child_price is None or self.child_price < 0:
                frappe.throw(_("Child Price must be greater than or equal to 0"))
        
        elif self.price_type == "Percentage":
            if self.percentage_change is None:
                frappe.throw(_("Percentage Change is required for percentage-based pricing"))
    
    def validate_percentage_change(self):
        """Validate percentage change value"""
        if self.price_type == "Percentage" and self.percentage_change is not None:
            if self.percentage_change < -100:
                frappe.throw(_("Percentage change cannot be less than -100%"))
            
            if self.percentage_change > 1000:
                frappe.throw(_("Percentage change cannot exceed 1000%"))
    
    def check_date_overlaps(self):
        """Check for overlapping date ranges with other seasonal prices"""
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
    
    def calculate_price(self, base_price, guest_type="adult"):
        """Calculate the seasonal price based on base price and guest type"""
        if self.price_type == "Fixed":
            if guest_type.lower() == "adult":
                return self.adult_price or 0
            elif guest_type.lower() == "child":
                return self.child_price or 0
            else:
                return 0
        
        elif self.price_type == "Percentage":
            if self.percentage_change is None:
                return base_price
            
            # Calculate percentage change
            multiplier = 1 + (self.percentage_change / 100)
            return base_price * multiplier
        
        return base_price
    
    def get_season_summary(self):
        """Get a summary of the seasonal pricing"""
        summary = f"{self.season_name} ({self.start_date} to {self.end_date})"
        
        if self.price_type == "Fixed":
            if self.adult_price:
                summary += f" - Adult: {self.adult_price}"
            if self.child_price:
                summary += f", Child: {self.child_price}"
        elif self.price_type == "Percentage":
            if self.percentage_change is not None:
                summary += f" - {self.percentage_change:+.1f}%"
        
        return summary
    
    def get_price_display(self):
        """Get formatted price display"""
        if self.price_type == "Fixed":
            prices = []
            if self.adult_price:
                prices.append(f"Adult: {self.adult_price}")
            if self.child_price:
                prices.append(f"Child: {self.child_price}")
            return ", ".join(prices) if prices else "No fixed prices set"
        
        elif self.price_type == "Percentage":
            if self.percentage_change is not None:
                return f"{self.percentage_change:+.1f}% adjustment"
            return "No percentage set"
        
        return "No pricing configured"
    
    def get_season_duration_days(self):
        """Get the duration of the season in days"""
        if not self.start_date or not self.end_date:
            return 0
        
        start = getdate(self.start_date)
        end = getdate(self.end_date)
        
        # Calculate days difference
        delta = end - start
        return delta.days + 1  # Include both start and end dates
    
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