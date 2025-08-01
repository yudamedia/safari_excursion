# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_package/excursion_package.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, add_days, now_datetime

class ExcursionPackage(Document):
    """
    DocType controller for Excursion Package
    
    This controller handles excursion package management,
    including pricing, availability, and operational details.
    Note: Web functionality removed - this is now a desk-only DocType
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_basic_information()
        self.validate_pricing()
        self.validate_capacity_and_timing()
        self.validate_availability()
        self.set_default_values()
        self.validate_requirements()
    
    def validate_basic_information(self):
        """Validate basic package information"""
        if not self.package_name:
            frappe.throw(_("Package Name is required"))
        
        if not self.package_code:
            frappe.throw(_("Package Code is required"))
        
        # Temporarily skip category validation for testing
        # if not self.excursion_category:
        #     frappe.throw(_("Excursion Category is required"))
        
        # Validate package code uniqueness
        self.validate_package_code_uniqueness()
    
    def validate_package_code_uniqueness(self):
        """Validate that package code is unique"""
        existing = frappe.get_all("Excursion Package", {
            "package_code": self.package_code,
            "name": ["!=", self.name]
        })
        
        if existing:
            frappe.throw(_("Package Code '{0}' already exists").format(self.package_code))
    
    def validate_pricing(self):
        """Validate pricing information"""
        # Validate rate configuration if provided
        if self.rate_configuration:
            if not frappe.db.exists("Excursion Rate Configuration", self.rate_configuration):
                frappe.throw(_("Rate Configuration '{0}' does not exist").format(self.rate_configuration))
        
        # Validate group discount settings if applicable
        if hasattr(self, 'group_discount_applicable') and self.group_discount_applicable:
            if hasattr(self, 'minimum_group_size') and self.minimum_group_size and self.minimum_group_size < 2:
                frappe.throw(_("Minimum group size must be at least 2"))
    
    def validate_capacity_and_timing(self):
        """Validate capacity and timing details"""
        if self.max_capacity and self.max_capacity <= 0:
            frappe.throw(_("Maximum capacity must be greater than 0"))
        
        if self.duration_hours and self.duration_hours <= 0:
            frappe.throw(_("Duration must be greater than 0 hours"))
    
    def validate_availability(self):
        """Validate availability settings"""
        # Add availability validation logic here
        pass
    
    def validate_requirements(self):
        """Validate age and fitness requirements"""
        if self.minimum_age and self.maximum_age:
            if self.minimum_age >= self.maximum_age:
                frappe.throw(_("Minimum age must be less than maximum age"))
    
    def set_default_values(self):
        """Set default values for various fields"""
        if self.booking_deadline_hours is None:
            self.booking_deadline_hours = 24
        
        # Set system information fields
        if self.is_new():
            self.created_by_user = frappe.session.user
        
        self.last_modified_by = frappe.session.user
    
    def get_package_summary(self):
        """Get a summary of the package for listing views"""
        return {
            "name": self.name,
            "package_name": self.package_name,
            "package_code": self.package_code,
            "category": self.excursion_category,
            "rate_configuration": self.rate_configuration,
            "duration_hours": self.duration_hours,
            "max_capacity": self.max_capacity,
            "featured_image": self.featured_image,
            "is_published": self.is_published,
            "is_featured": self.is_featured
        }
    
    def get_available_dates(self, start_date=None, end_date=None):
        """Get available dates for booking this package"""
        # Implementation for getting available dates
        # This would consider seasonal availability, available days, etc.
        available_dates = []
        
        # Logic to calculate available dates based on:
        # - available_days (which days of week)
        # - seasonal_availability
        # - existing bookings vs max_capacity
        
        return available_dates
    
    def calculate_price(self, adults=1, children=0, booking_date=None, residence_type="International"):
        """Calculate price for given parameters using new pricing system"""
        if not self.rate_configuration:
            frappe.throw(_("No rate configuration found for this package"))
        
        try:
            from safari_excursion.safari_excursion.utils.pricing_utils import get_excursion_pricing
            
            # Convert children count to list of ages (assuming average age for simplicity)
            children_ages = [8] * children if children else []
            
            pricing = get_excursion_pricing(
                excursion_package=self.name,
                excursion_date=booking_date or frappe.utils.today(),
                adults=adults,
                children=children_ages,
                residence_type=residence_type,
                group_size=adults + children
            )
            
            return pricing.get("total", 0)
            
        except Exception as e:
            frappe.throw(_("Error calculating price: {0}").format(str(e)))
    
    def _is_date_in_season(self, booking_date, season):
        """Check if booking date falls within a seasonal pricing period"""
        # Implementation to check if date is in season
        # This would compare against season.start_date and season.end_date
        return False  # Placeholder
    
    def can_book(self, booking_date=None, party_size=1):
        """Check if package can be booked for given date and party size"""
        if not self.is_published:
            return False, "Package is not published"
        
        if self.max_capacity and party_size > self.max_capacity:
            return False, f"Party size exceeds maximum capacity of {self.max_capacity}"
        
        # Check booking deadline
        if booking_date and self.booking_deadline_hours:
            from datetime import datetime, timedelta
            deadline = datetime.now() + timedelta(hours=self.booking_deadline_hours)
            booking_datetime = datetime.combine(booking_date, datetime.min.time())
            if booking_datetime < deadline:
                return False, f"Booking must be made at least {self.booking_deadline_hours} hours in advance"
        
        # Check if date is available (not fully booked)
        if booking_date:
            existing_bookings = frappe.get_all("Excursion Booking", {
                "excursion_package": self.name,
                "excursion_date": booking_date,
                "booking_status": ["in", ["Confirmed", "Checked In"]]
            }, ["SUM(total_participants) as total_booked"])
            
            total_booked = existing_bookings[0].total_booked or 0
            if self.max_capacity and (total_booked + party_size) > self.max_capacity:
                return False, f"Insufficient capacity. Available: {self.max_capacity - total_booked}"
        
        return True, "Available for booking"
    
    def get_booking_statistics(self):
        """Get booking statistics for this package"""
        stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_bookings,
                SUM(total_participants) as total_participants,
                AVG(total_amount) as average_booking_value,
                SUM(CASE WHEN booking_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed_bookings
            FROM `tabExcursion Booking`
            WHERE excursion_package = %s
        """, [self.name], as_dict=True)
        
        return stats[0] if stats else {
            "total_bookings": 0,
            "total_participants": 0,
            "average_booking_value": 0,
            "confirmed_bookings": 0
        }