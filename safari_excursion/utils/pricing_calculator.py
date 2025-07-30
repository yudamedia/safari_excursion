# ~/frappe-bench/apps/safari_excursion/safari_excursion/utils/pricing_calculator.py

import frappe
from frappe import _
from frappe.utils import flt, getdate

class ExcursionPricingCalculator:
    """
    Utility class for calculating excursion pricing with various discounts and charges
    
    This class handles complex pricing calculations including:
    - Base pricing for adults and children
    - Seasonal pricing adjustments
    - Group discounts
    - Additional charges
    """
    
    def __init__(self, excursion_booking):
        self.excursion_booking = excursion_booking
        if isinstance(excursion_booking, str):
            self.excursion_booking = frappe.get_doc("Excursion Booking", excursion_booking)
        
        self.package = frappe.get_doc("Excursion Package", self.excursion_booking.excursion_package)
    
    def calculate_total_price(self):
        """Calculate the total price for the excursion booking"""
        pricing_details = {
            "base_amount": 0,
            "child_discount": 0,
            "group_discount": 0,
            "seasonal_adjustment": 0,
            "additional_charges": 0,
            "total_amount": 0
        }
        
        # Calculate base amount
        base_prices = self.calculate_base_amount()
        pricing_details["base_amount"] = base_prices["total_base"]
        
        # Apply seasonal pricing if applicable
        seasonal_price = self.get_seasonal_price()
        if seasonal_price:
            pricing_details["seasonal_adjustment"] = seasonal_price - base_prices["adult_price"]
            pricing_details["base_amount"] = (seasonal_price * self.excursion_booking.adult_count + 
                                            base_prices["child_total"])
        
        # Calculate child discount
        pricing_details["child_discount"] = base_prices["child_discount"]
        
        # Calculate group discount
        if self.package.group_discount_applicable:
            group_discount = self.calculate_group_discount(pricing_details["base_amount"])
            pricing_details["group_discount"] = group_discount
        
        # Calculate additional charges
        additional_charges = self.calculate_additional_charges()
        pricing_details["additional_charges"] = additional_charges
        
        # Calculate total
        pricing_details["total_amount"] = (
            pricing_details["base_amount"] - 
            pricing_details["child_discount"] - 
            pricing_details["group_discount"] + 
            pricing_details["additional_charges"]
        )
        
        return pricing_details
    
    def calculate_base_amount(self):
        """Calculate base amount for adults and children"""
        adult_count = self.excursion_booking.adult_count or 0
        child_count = self.excursion_booking.child_count or 0
        
        adult_price = flt(self.package.base_price_adult)
        child_price = flt(self.package.base_price_child) or (adult_price * 0.7)  # Default child price is 70% of adult
        
        adult_total = adult_price * adult_count
        child_total = child_price * child_count
        child_discount = (adult_price - child_price) * child_count
        
        return {
            "adult_price": adult_price,
            "child_price": child_price,
            "adult_total": adult_total,
            "child_total": child_total,
            "total_base": adult_total + child_total,
            "child_discount": child_discount
        }
    
    def get_seasonal_price(self):
        """Get seasonal price if applicable"""
        excursion_date = getdate(self.excursion_booking.excursion_date)
        
        if not self.package.seasonal_pricing:
            return None
            
        for season in self.package.seasonal_pricing:
            start_date = getdate(season.start_date)
            end_date = getdate(season.end_date)
            
            if start_date <= excursion_date <= end_date:
                if season.price_type == "Fixed":
                    return flt(season.adult_price)
                elif season.price_type == "Percentage":
                    adjustment = flt(self.package.base_price_adult) * (flt(season.percentage_change) / 100)
                    return flt(self.package.base_price_adult) + adjustment
        
        return None
    
    def calculate_group_discount(self, base_amount):
        """Calculate group discount if applicable"""
        if not self.package.group_discount_applicable:
            return 0
            
        total_guests = self.excursion_booking.total_guests
        minimum_group_size = self.package.minimum_group_size or 5
        
        if total_guests < minimum_group_size:
            return 0
        
        # Get group discount settings from system
        group_discount_settings = self.get_group_discount_settings()
        
        discount_percentage = 0
        for tier in group_discount_settings:
            if total_guests >= tier.get("minimum_size", 0):
                discount_percentage = tier.get("discount_percentage", 0)
        
        return base_amount * (discount_percentage / 100)
    
    def get_group_discount_settings(self):
        """Get group discount tiers from settings or default"""
        # This could be configurable in a settings doctype
        # For now, using default tiers
        return [
            {"minimum_size": 5, "discount_percentage": 5},
            {"minimum_size": 10, "discount_percentage": 10},
            {"minimum_size": 15, "discount_percentage": 15},
            {"minimum_size": 20, "discount_percentage": 20}
        ]
    
    def calculate_additional_charges(self):
        """Calculate additional charges based on requirements"""
        additional_charges = 0
        
        # Park fees calculation
        park_fees = self.calculate_park_fees()
        additional_charges += park_fees
        
        # Equipment rental charges
        if self.excursion_booking.special_requirements:
            additional_charges += self.calculate_equipment_charges()
        
        # Transport charges for distant pickup locations
        if self.excursion_booking.pickup_required:
            additional_charges += self.calculate_transport_charges()
        
        # Premium time charges (early morning, late evening)
        additional_charges += self.calculate_time_premium_charges()
        
        return additional_charges
    
    def calculate_park_fees(self):
        """Calculate park fees for excursions visiting national/marine parks"""
        try:
            from safari_excursion.utils.parks_integration import ExcursionParkFeeCalculator
            
            park_calculator = ExcursionParkFeeCalculator(self.excursion_booking)
            if park_calculator.has_park_visits():
                park_fees = park_calculator.calculate_park_fees()
                return park_fees.get("total_fees", 0)
            
            return 0
            
        except Exception as e:
            frappe.log_error(f"Park fee calculation error: {str(e)}")
            return 0
    
    def calculate_equipment_charges(self):
        """Calculate equipment rental charges"""
        # This could be enhanced to check specific equipment requirements
        # For now, returning 0 - can be extended based on business needs
        return 0
    
    def calculate_transport_charges(self):
        """Calculate additional transport charges for distant pickups"""
        # Check if pickup location requires additional transport charges
        pickup_location = self.excursion_booking.pickup_location or ""
        
        # Get distance-based transport charges from settings
        transport_zones = self.get_transport_zones()
        
        for zone in transport_zones:
            if any(keyword in pickup_location.lower() for keyword in zone.get("keywords", [])):
                return zone.get("additional_charge", 0)
        
        return 0
    
    def get_transport_zones(self):
        """Get transport zones and charges"""
        # This could be configurable in a settings doctype
        return [
            {
                "name": "Airport Zone",
                "keywords": ["airport", "jomo kenyatta", "jkia"],
                "additional_charge": 2000
            },
            {
                "name": "Distant Hotels",
                "keywords": ["karen", "langata", "westlands"],
                "additional_charge": 1000
            },
            {
                "name": "City Center",
                "keywords": ["cbd", "city center", "downtown"],
                "additional_charge": 500
            }
        ]
    
    def calculate_time_premium_charges(self):
        """Calculate premium charges for early/late departures"""
        from frappe.utils import get_time
        
        departure_time = get_time(self.excursion_booking.departure_time)
        
        # Early morning premium (before 6 AM)
        if departure_time < get_time("06:00:00"):
            return flt(self.package.base_price_adult) * 0.1  # 10% premium
        
        # Late evening premium (after 7 PM)
        if departure_time > get_time("19:00:00"):
            return flt(self.package.base_price_adult) * 0.15  # 15% premium
        
        return 0
    
    @staticmethod
    def get_pricing_preview(excursion_package, adult_count, child_count, excursion_date, departure_time=None):
        """Get pricing preview without creating a booking"""
        
        # Create a temporary booking object for calculation
        temp_booking = frappe._dict({
            "excursion_package": excursion_package,
            "adult_count": adult_count,
            "child_count": child_count,
            "total_guests": adult_count + (child_count or 0),
            "excursion_date": excursion_date,
            "departure_time": departure_time or "08:00:00",
            "pickup_required": True,
            "pickup_location": "",
            "special_requirements": ""
        })
        
        calculator = ExcursionPricingCalculator(temp_booking)
        return calculator.calculate_total_price()

@frappe.whitelist()
def get_excursion_pricing_preview(excursion_package, adult_count, child_count, excursion_date, departure_time=None):
    """Whitelisted method to get pricing preview from client side"""
    try:
        adult_count = int(adult_count or 0)
        child_count = int(child_count or 0)
        
        if adult_count <= 0:
            frappe.throw(_("Adult count must be greater than 0"))
        
        pricing = ExcursionPricingCalculator.get_pricing_preview(
            excursion_package, adult_count, child_count, excursion_date, departure_time
        )
        
        return {
            "status": "success",
            "pricing": pricing
        }
        
    except Exception as e:
        frappe.log_error(f"Pricing preview error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def calculate_booking_pricing(excursion_booking):
    """Recalculate pricing for an existing booking"""
    try:
        doc = frappe.get_doc("Excursion Booking", excursion_booking)
        calculator = ExcursionPricingCalculator(doc)
        pricing = calculator.calculate_total_price()
        
        # Update the booking with new pricing
        doc.base_amount = pricing["base_amount"]
        doc.child_discount = pricing["child_discount"]
        doc.group_discount = pricing["group_discount"]
        doc.additional_charges = pricing["additional_charges"]
        doc.total_amount = pricing["total_amount"]
        doc.balance_due = doc.total_amount - (doc.deposit_amount or 0)
        
        doc.save()
        
        return {
            "status": "success",
            "pricing": pricing,
            "message": _("Pricing updated successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Booking pricing calculation error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

class ExcursionQuoteGenerator:
    """
    Generate quotes for excursion packages with multiple scenarios
    """
    
    def __init__(self, excursion_package):
        self.package = frappe.get_doc("Excursion Package", excursion_package)
    
    def generate_quote_scenarios(self, base_adult_count=2, base_child_count=0):
        """Generate multiple pricing scenarios for different group sizes"""
        scenarios = []
        
        # Different group size scenarios
        group_scenarios = [
            {"adults": 2, "children": 0, "name": "Couple"},
            {"adults": 2, "children": 2, "name": "Family of 4"},
            {"adults": 4, "children": 2, "name": "Large Family"},
            {"adults": 6, "children": 0, "name": "Friends Group"},
            {"adults": 10, "children": 0, "name": "Small Group"},
            {"adults": 15, "children": 5, "name": "Large Group"}
        ]
        
        for scenario in group_scenarios:
            pricing = ExcursionPricingCalculator.get_pricing_preview(
                self.package.name,
                scenario["adults"],
                scenario["children"],
                frappe.utils.add_days(frappe.utils.nowdate(), 7)  # Next week
            )
            
            scenarios.append({
                "scenario_name": scenario["name"],
                "adult_count": scenario["adults"],
                "child_count": scenario["children"],
                "total_guests": scenario["adults"] + scenario["children"],
                "pricing": pricing
            })
        
        return scenarios
    
    def generate_seasonal_comparison(self, adult_count=2, child_count=0):
        """Generate pricing comparison across different seasons"""
        seasonal_prices = []
        
        if not self.package.seasonal_pricing:
            return seasonal_prices
        
        for season in self.package.seasonal_pricing:
            # Use middle date of season for calculation
            from frappe.utils import add_days, date_diff
            start_date = frappe.utils.getdate(season.start_date)
            end_date = frappe.utils.getdate(season.end_date)
            middle_date = add_days(start_date, date_diff(end_date, start_date) // 2)
            
            pricing = ExcursionPricingCalculator.get_pricing_preview(
                self.package.name,
                adult_count,
                child_count,
                middle_date
            )
            
            seasonal_prices.append({
                "season_name": season.season_name,
                "start_date": season.start_date,
                "end_date": season.end_date,
                "pricing": pricing
            })
        
        return seasonal_prices

@frappe.whitelist()
def generate_excursion_quote(excursion_package, adult_count=2, child_count=0):
    """Generate comprehensive quote for excursion package"""
    try:
        quote_generator = ExcursionQuoteGenerator(excursion_package)
        
        # Base pricing
        base_pricing = ExcursionPricingCalculator.get_pricing_preview(
            excursion_package,
            int(adult_count),
            int(child_count),
            frappe.utils.add_days(frappe.utils.nowdate(), 7)
        )
        
        # Group scenarios
        group_scenarios = quote_generator.generate_quote_scenarios()
        
        # Seasonal comparison
        seasonal_comparison = quote_generator.generate_seasonal_comparison(
            int(adult_count), int(child_count)
        )
        
        return {
            "status": "success",
            "quote": {
                "package_details": {
                    "name": quote_generator.package.package_name,
                    "duration": quote_generator.package.duration_hours,
                    "currency": quote_generator.package.currency
                },
                "base_pricing": base_pricing,
                "group_scenarios": group_scenarios,
                "seasonal_comparison": seasonal_comparison
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Quote generation error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
