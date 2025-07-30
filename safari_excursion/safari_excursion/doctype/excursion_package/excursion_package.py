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
        
        if not self.excursion_category:
            frappe.throw(_("Excursion Category is required"))
        
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
        if self.base_price_adult is not None and self.base_price_adult < 0:
            frappe.throw(_("Adult price cannot be negative"))
        
        if self.base_price_child is not None and self.base_price_child < 0:
            frappe.throw(_("Child price cannot be negative"))
        
        if self.minimum_group_size and self.minimum_group_size < 2:
            frappe.throw(_("Minimum group size must be at least 2"))
    
    def validate_capacity_and_timing(self):
        """Validate capacity and timing details"""
        if self.max_capacity and self.max_capacity <= 0:
            frappe.throw(_("Maximum capacity must be greater than 0"))
        
        if self.duration_hours and self.duration_hours <= 0:
            frappe.throw(_("Duration must be greater than 0"))
        
        if self.booking_deadline_hours and self.booking_deadline_hours < 0:
            frappe.throw(_("Booking deadline cannot be negative"))
    
    def validate_availability(self):
        """Validate availability settings"""
        if self.minimum_age and self.maximum_age:
            if self.minimum_age >= self.maximum_age:
                frappe.throw(_("Minimum age must be less than maximum age"))
    
    def validate_requirements(self):
        """Validate requirements and equipment"""
        if self.fitness_level and self.fitness_level not in [
            "Low", "Moderate", "High", "Very High"
        ]:
            frappe.throw(_("Invalid fitness level selected"))
    
    def set_default_values(self):
        """Set default values for various fields"""
        if not self.package_status:
            self.package_status = "Draft"
        
        if not self.currency:
            self.currency = "USD"
        
        if not self.booking_deadline_hours:
            self.booking_deadline_hours = 24
    
    def autoname(self):
        """Set package name automatically if not provided"""
        if not self.package_code:
            from frappe.model.naming import make_autoname
            self.package_code = make_autoname("EXP-.#####")
    
    def on_submit(self):
        """Handle package submission"""
        self.validate_package_completeness()
        self.send_notifications()
    
    def validate_package_completeness(self):
        """Validate that package is complete before submission"""
        required_fields = [
            "package_name", "package_code", "excursion_category",
            "description", "duration_hours", "max_capacity"
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field, None):
                missing_fields.append(field.replace("_", " ").title())
        
        if missing_fields:
            frappe.throw(_("Please complete the following fields: {0}").format(
                ", ".join(missing_fields)))
    
    def send_notifications(self):
        """Send notifications when package is submitted"""
        # Implementation for notifications
        pass
    
    def get_package_summary(self):
        """Get a summary of the package"""
        summary = f"{self.package_name} ({self.package_code})"
        
        if self.excursion_category:
            summary += f" - {self.excursion_category}"
        
        if self.duration_hours:
            summary += f" - {self.duration_hours}h"
        
        if self.max_capacity:
            summary += f" - Max {self.max_capacity} guests"
        
        return summary
    
    def get_pricing_summary(self):
        """Get pricing summary"""
        pricing = []
        
        if self.base_price_adult:
            pricing.append(f"Adult: {self.base_price_adult}")
        
        if self.base_price_child:
            pricing.append(f"Child: {self.base_price_child}")
        
        if self.currency:
            pricing.append(f"({self.currency})")
        
        return " | ".join(pricing) if pricing else "No pricing set"
    
    def is_available_on_date(self, check_date):
        """Check if package is available on specific date"""
        if not self.is_published or self.package_status != "Active":
            return False
        
        # Check seasonal availability
        if self.seasonal_availability:
            for season in self.seasonal_availability:
                if season.is_date_in_season(check_date):
                    return True
            return False
        
        return True
    
    def get_effective_price(self, guest_type="adult", guest_count=1, date=None):
        """Get effective price for given parameters"""
        base_price = self.base_price_adult if guest_type == "adult" else self.base_price_child
        
        if not base_price:
            return 0
        
        # Apply seasonal pricing
        if date and self.seasonal_pricing:
            for season in self.seasonal_pricing:
                if season.is_date_in_season(date):
                    base_price = season.calculate_price(base_price, guest_type)
                    break
        
        # Apply group discount
        if self.group_discount_applicable and guest_count >= self.minimum_group_size:
            # Group discount logic would be implemented here
            pass
        
        return base_price * guest_count
    
    def get_availability_status(self):
        """Get current availability status"""
        if not self.is_published:
            return "Draft"
        
        if self.package_status != "Active":
            return self.package_status
        
        return "Available"
    
    @frappe.whitelist()
    def publish_package(self):
        """Publish the package"""
        self.is_published = 1
        self.package_status = "Active"
        self.save()
        frappe.msgprint(_("Package published successfully"))
    
    @frappe.whitelist()
    def unpublish_package(self):
        """Unpublish the package"""
        self.is_published = 0
        self.package_status = "Inactive"
        self.save()
        frappe.msgprint(_("Package unpublished successfully"))
    
    def get_related_bookings(self):
        """Get related excursion bookings"""
        return frappe.get_all("Excursion Booking", {
            "excursion_package": self.name
        }, ["name", "booking_number", "booking_status", "excursion_date"])
    
    def get_booking_count(self):
        """Get total booking count"""
        return frappe.db.count("Excursion Booking", {
            "excursion_package": self.name
        })
    
    def get_revenue_summary(self):
        """Get revenue summary for this package"""
        # This would calculate total revenue from bookings
        # Implementation would depend on business logic
        return 0 