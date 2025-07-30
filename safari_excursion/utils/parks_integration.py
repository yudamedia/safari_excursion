# ~/frappe-bench/apps/safari_excursion/safari_excursion/utils/parks_integration.py

import frappe
from frappe import _
from frappe.utils import flt, getdate

class ExcursionParkFeeCalculator:
    """
    Utility class for calculating park fees for excursions
    
    This class integrates with the existing safari_parks app to calculate
    park fees for excursions that visit national parks or marine parks.
    """
    
    def __init__(self, excursion_booking):
        self.excursion_booking = excursion_booking
        if isinstance(excursion_booking, str):
            self.excursion_booking = frappe.get_doc("Excursion Booking", excursion_booking)
    
    def calculate_park_fees(self):
        """Calculate total park fees for the excursion"""
        if not self.has_park_visits():
            return {"total_fees": 0, "fee_breakdown": []}
        
        park_visits = self.get_park_visits()
        total_fees = 0
        fee_breakdown = []
        
        for park_visit in park_visits:
            park_fee_calc = self.calculate_single_park_fee(park_visit)
            total_fees += park_fee_calc["total_fee"]
            fee_breakdown.append(park_fee_calc)
        
        return {
            "total_fees": total_fees,
            "fee_breakdown": fee_breakdown
        }
    
    def has_park_visits(self):
        """Check if the excursion includes park visits"""
        package = frappe.get_doc("Excursion Package", self.excursion_booking.excursion_package)
        
        # Check if package has park destinations
        if hasattr(package, 'destination_locations') and package.destination_locations:
            for destination in package.destination_locations:
                if destination.location_type in ["National Park", "Marine Park", "Conservancy"]:
                    return True
        
        return False
    
    def get_park_visits(self):
        """Get list of parks to visit during the excursion"""
        package = frappe.get_doc("Excursion Package", self.excursion_booking.excursion_package)
        park_visits = []
        
        if hasattr(package, 'destination_locations') and package.destination_locations:
            for destination in package.destination_locations:
                if destination.location_type in ["National Park", "Marine Park", "Conservancy"]:
                    # Check if this destination is a registered park
                    park_name = self.find_park_by_name(destination.location_name)
                    if park_name:
                        park_visits.append({
                            "park": park_name,
                            "location_name": destination.location_name,
                            "visit_duration": destination.duration_hours or 4,  # Default 4 hours
                            "activities": destination.activities or []
                        })
        
        return park_visits
    
    def find_park_by_name(self, location_name):
        """Find park in the system by location name"""
        # Try exact match first
        park = frappe.db.get_value("National Park", {"park_name": location_name}, "name")
        if park:
            return park
        
        # Try partial match
        parks = frappe.get_all(
            "National Park",
            fields=["name", "park_name"],
            filters={"is_active": 1}
        )
        
        for park in parks:
            if location_name.lower() in park.park_name.lower() or park.park_name.lower() in location_name.lower():
                return park.name
        
        return None
    
    def calculate_single_park_fee(self, park_visit):
        """Calculate fees for a single park visit"""
        park = park_visit["park"]
        adults = self.excursion_booking.adult_count or 0
        children = self.excursion_booking.child_count or 0
        
        # Determine residence category from guests
        residence_category = self.get_guest_residence_category()
        
        fee_calculation = {
            "park": park,
            "park_name": park_visit["location_name"],
            "adult_count": adults,
            "child_count": children,
            "residence_category": residence_category,
            "adult_fee": 0,
            "child_fee": 0,
            "vehicle_fee": 0,
            "guide_fee": 0,
            "total_fee": 0,
            "currency": "USD"
        }
        
        # Calculate adult fees
        if adults > 0:
            adult_fee_rate = self.get_park_fee_rate(park, "Adult", residence_category)
            fee_calculation["adult_fee"] = flt(adult_fee_rate) * adults
        
        # Calculate child fees
        if children > 0:
            child_fee_rate = self.get_park_fee_rate(park, "Child", residence_category)
            fee_calculation["child_fee"] = flt(child_fee_rate) * children
        
        # Calculate vehicle fees if applicable
        if self.excursion_booking.assigned_vehicle:
            vehicle_fee = self.get_vehicle_fee(park, self.excursion_booking.assigned_vehicle)
            fee_calculation["vehicle_fee"] = vehicle_fee
        
        # Calculate guide fees if applicable
        if self.excursion_booking.assigned_guide:
            guide_fee = self.get_guide_fee(park)
            fee_calculation["guide_fee"] = guide_fee
        
        fee_calculation["total_fee"] = (
            fee_calculation["adult_fee"] + 
            fee_calculation["child_fee"] + 
            fee_calculation["vehicle_fee"] + 
            fee_calculation["guide_fee"]
        )
        
        return fee_calculation
    
    def get_guest_residence_category(self):
        """Determine residence category from booking party guests"""
        # Default to Non-Resident for international pricing
        default_category = "Non-Resident"
        
        if not self.excursion_booking.booking_party:
            return default_category
        
        try:
            booking_party = frappe.get_doc("Booking Party", self.excursion_booking.booking_party)
            
            # Check primary guest first
            if booking_party.primary_guest:
                guest = frappe.get_doc("Safari Guest", booking_party.primary_guest)
                if guest.residence_status:
                    return self.map_residence_to_park_category(guest.residence_status)
            
            # If no primary guest or no residence status, check other guests
            if hasattr(booking_party, 'guests') and booking_party.guests:
                for guest_row in booking_party.guests:
                    guest = frappe.get_doc("Safari Guest", guest_row.guest)
                    if guest.residence_status:
                        return self.map_residence_to_park_category(guest.residence_status)
            
        except Exception as e:
            frappe.log_error(f"Error determining residence category: {str(e)}")
        
        return default_category
    
    def map_residence_to_park_category(self, residence_status):
        """Map Safari Guest residence status to Park Fee Category"""
        # Get the park fee category type
        category_type = frappe.db.get_value(
            "Park Fee Category",
            residence_status,
            "category_type"
        )
        
        if category_type:
            return category_type
        
        # Fallback mapping based on common residence statuses
        residence_mapping = {
            "Kenyan Citizen": "Citizen",
            "Kenyan Resident": "Resident", 
            "EAC Citizen": "EAC Citizen",
            "Foreign Resident": "Resident",
            "Tourist": "Non-Resident",
            "International Visitor": "Non-Resident"
        }
        
        return residence_mapping.get(residence_status, "Non-Resident")
    
    def get_park_fee_rate(self, park, fee_type, visitor_category):
        """Get park fee rate for specific category"""
        # Check international fees first (for non-residents)
        if visitor_category in ["Non-Resident", "Tourist"]:
            rate = frappe.db.get_value(
                "Park International Fee",
                {
                    "parent": park,
                    "fee_type": fee_type,
                    "visitor_category": visitor_category
                },
                "rate"
            )
            if rate:
                return rate
        
        # Check local fees for residents/citizens
        rate = frappe.db.get_value(
            "Park Local Fee",
            {
                "parent": park,
                "fee_type": fee_type,
                "visitor_category": visitor_category
            },
            "rate"
        )
        
        return rate or 0
    
    def get_vehicle_fee(self, park, vehicle):
        """Get vehicle entry fee for the park"""
        try:
            vehicle_doc = frappe.get_doc("Vehicle", vehicle)
            vehicle_type = vehicle_doc.vehicle_type
            
            vehicle_fee = frappe.db.get_value(
                "Park Vehicle Fee",
                {
                    "parent": park,
                    "type_name": vehicle_type
                },
                "rate"
            )
            
            return vehicle_fee or 0
            
        except Exception as e:
            frappe.log_error(f"Error getting vehicle fee: {str(e)}")
            return 0
    
    def get_guide_fee(self, park):
        """Get guide fee if applicable"""
        # Some parks charge guide fees - this can be configured
        guide_fee = frappe.db.get_value(
            "Park Guide Fee",
            {
                "parent": park
            },
            "rate"
        )
        
        return guide_fee or 0
    
    def create_park_booking(self):
        """Create park booking record for the excursion"""
        if not self.has_park_visits():
            return None
        
        try:
            # Create park booking
            park_booking = frappe.get_doc({
                "doctype": "Park Booking",
                "booking_party": self.excursion_booking.booking_party,
                "booking_date": self.excursion_booking.booking_date,
                "visit_date": self.excursion_booking.excursion_date,
                "total_adults": self.excursion_booking.adult_count,
                "total_children": self.excursion_booking.child_count,
                "total_guests": self.excursion_booking.total_guests,
                "booking_type": "Excursion",
                "reference_booking": self.excursion_booking.name,
                "vehicle": self.excursion_booking.assigned_vehicle,
                "guide": self.excursion_booking.assigned_guide,
                "status": "Confirmed" if self.excursion_booking.booking_status == "Confirmed" else "Draft"
            })
            
            # Add park visits
            park_visits = self.get_park_visits()
            for park_visit in park_visits:
                park_booking.append("parks", {
                    "park": park_visit["park"],
                    "visit_duration": park_visit["visit_duration"],
                    "include_vehicle_fees": 1 if self.excursion_booking.assigned_vehicle else 0
                })
            
            park_booking.insert(ignore_permissions=True)
            
            # Submit if excursion is confirmed
            if self.excursion_booking.booking_status == "Confirmed":
                park_booking.submit()
            
            return park_booking.name
            
        except Exception as e:
            frappe.log_error(f"Error creating park booking: {str(e)}")
            return None

def create_excursion_park_booking(doc, method):
    """Hook function to create park booking when excursion is submitted"""
    if doc.doctype == "Excursion Booking":
        park_calculator = ExcursionParkFeeCalculator(doc)
        
        if park_calculator.has_park_visits():
            park_booking = park_calculator.create_park_booking()
            if park_booking:
                doc.db_set("park_booking", park_booking, update_modified=False)
                frappe.msgprint(_("Park booking {0} created successfully").format(park_booking))

def cancel_excursion_park_booking(doc, method):
    """Hook function to cancel park booking when excursion is cancelled"""
    if doc.doctype == "Excursion Booking" and doc.park_booking:
        try:
            park_booking = frappe.get_doc("Park Booking", doc.park_booking)
            if park_booking.docstatus == 1:
                park_booking.cancel()
                frappe.msgprint(_("Park booking {0} cancelled").format(doc.park_booking))
        except Exception as e:
            frappe.log_error(f"Error cancelling park booking: {str(e)}")

@frappe.whitelist()
def get_excursion_park_fees(excursion_booking):
    """Get park fee breakdown for an excursion booking"""
    try:
        doc = frappe.get_doc("Excursion Booking", excursion_booking)
        calculator = ExcursionParkFeeCalculator(doc)
        
        fee_calculation = calculator.calculate_park_fees()
        
        return {
            "status": "success",
            "park_fees": fee_calculation
        }
        
    except Exception as e:
        frappe.log_error(f"Park fee calculation error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def update_excursion_pricing_with_park_fees(excursion_booking):
    """Update excursion pricing to include park fees"""
    try:
        doc = frappe.get_doc("Excursion Booking", excursion_booking)
        calculator = ExcursionParkFeeCalculator(doc)
        
        # Calculate park fees
        park_fees = calculator.calculate_park_fees()
        total_park_fees = park_fees["total_fees"]
        
        # Update additional charges with park fees
        current_additional = doc.additional_charges or 0
        doc.additional_charges = current_additional + total_park_fees
        doc.total_amount = (doc.base_amount or 0) - (doc.child_discount or 0) - (doc.group_discount or 0) + doc.additional_charges
        doc.balance_due = doc.total_amount - (doc.deposit_amount or 0)
        
        doc.save()
        
        return {
            "status": "success",
            "message": _("Pricing updated with park fees"),
            "park_fees": total_park_fees,
            "new_total": doc.total_amount
        }
        
    except Exception as e:
        frappe.log_error(f"Pricing update error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

class ExcursionParkReporting:
    """Utility class for park-related reporting for excursions"""
    
    @staticmethod
    def get_park_revenue_from_excursions(park, start_date, end_date):
        """Get revenue generated from excursions for a specific park"""
        try:
            revenue_data = frappe.db.sql("""
                SELECT 
                    COUNT(eb.name) as excursion_count,
                    SUM(eb.total_guests) as total_guests,
                    SUM(pfc.total_fee) as total_park_revenue
                FROM `tabExcursion Booking` eb
                LEFT JOIN `tabPark Booking` pb ON eb.park_booking = pb.name
                LEFT JOIN `tabPark Fee Calculation` pfc ON pb.name = pfc.park_booking
                WHERE pb.parks LIKE %s
                    AND eb.excursion_date BETWEEN %s AND %s
                    AND eb.booking_status != 'Cancelled'
            """, [f"%{park}%", start_date, end_date], as_dict=True)
            
            return revenue_data[0] if revenue_data else {}
            
        except Exception as e:
            frappe.log_error(f"Park revenue calculation error: {str(e)}")
            return {}
    
    @staticmethod
    def get_popular_parks_for_excursions(days_back=30):
        """Get most popular parks for excursions"""
        from frappe.utils import add_days, getdate
        
        start_date = add_days(getdate(), -days_back)
        
        try:
            popular_parks = frappe.db.sql("""
                SELECT 
                    np.park_name,
                    np.name as park_code,
                    COUNT(eb.name) as excursion_visits,
                    SUM(eb.total_guests) as total_guests,
                    AVG(eb.total_amount) as avg_excursion_value
                FROM `tabNational Park` np
                LEFT JOIN `tabPark Booking` pb ON FIND_IN_SET(np.name, pb.parks)
                LEFT JOIN `tabExcursion Booking` eb ON pb.name = eb.park_booking
                WHERE eb.excursion_date >= %s
                    AND eb.booking_status != 'Cancelled'
                GROUP BY np.name
                HAVING excursion_visits > 0
                ORDER BY excursion_visits DESC, total_guests DESC
                LIMIT 10
            """, [start_date], as_dict=True)
            
            return popular_parks
            
        except Exception as e:
            frappe.log_error(f"Popular parks query error: {str(e)}")
            return []

@frappe.whitelist()
def get_excursion_park_analytics(days_back=30):
    """Get park analytics for excursions"""
    try:
        reporting = ExcursionParkReporting()
        popular_parks = reporting.get_popular_parks_for_excursions(days_back)
        
        return {
            "status": "success",
            "analytics": {
                "popular_parks": popular_parks
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Park analytics error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
