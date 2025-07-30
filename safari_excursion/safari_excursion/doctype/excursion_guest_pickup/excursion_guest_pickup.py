# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_guest_pickup/excursion_guest_pickup.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time, time_diff_in_seconds

class ExcursionGuestPickup(Document):
    """
    Controller for Excursion Guest Pickup child table
    
    This handles individual guest pickup scheduling and tracking
    """
    
    def validate(self):
        """Validate pickup data"""
        self.validate_pickup_time()
        self.validate_contact_phone()
        self.set_default_meeting_instructions()
    
    def validate_pickup_time(self):
        """Validate pickup time is reasonable"""
        if not self.estimated_pickup_time:
            return
        
        # Check if pickup time is not too early (before 5 AM) or too late (after 11 PM)
        pickup_time = get_time(self.estimated_pickup_time)
        early_limit = get_time("05:00:00")
        late_limit = get_time("23:00:00")
        
        if pickup_time < early_limit:
            frappe.msgprint(_("Warning: Pickup time {0} is very early for {1}").format(
                self.estimated_pickup_time, self.guest_name))
        
        if pickup_time > late_limit:
            frappe.msgprint(_("Warning: Pickup time {0} is very late for {1}").format(
                self.estimated_pickup_time, self.guest_name))
    
    def validate_contact_phone(self):
        """Validate contact phone is provided"""
        if not self.contact_phone:
            frappe.throw(_("Contact phone is required for guest {0}").format(self.guest_name))
    
    def set_default_meeting_instructions(self):
        """Set default meeting instructions if not provided"""
        if self.meeting_instructions:
            return  # Don't override existing instructions
        
        if not self.pickup_location_type:
            return
        
        instructions = {
            "Hotel": f"Meet at {self.pickup_location_name} main lobby/reception. Look for safari vehicle with company branding.",
            "Resort": f"Meet at {self.pickup_location_name} main reception area. Driver will contact you upon arrival.",
            "Airbnb": f"Meet at {self.pickup_location_name} main entrance. Please be ready and waiting.",
            "Private Residence": f"Meet at {self.pickup_location_name} main gate or entrance. Driver will call upon arrival.",
            "Lodge": f"Meet at {self.pickup_location_name} main reception/lobby area.",
            "Guest House": f"Meet at {self.pickup_location_name} reception or main entrance.",
            "Hostel": f"Meet at {self.pickup_location_name} reception desk. Driver will ask for you by name.",
            "Other": f"Meet at {self.pickup_location_name} main entrance. Driver will call you 5 minutes before arrival."
        }
        
        self.meeting_instructions = instructions.get(self.pickup_location_type, instructions["Other"])
    
    def calculate_travel_time_to_next(self, next_pickup_gps):
        """Calculate travel time to next pickup location"""
        if not self.gps_coordinates or not next_pickup_gps:
            return 15  # Default 15 minutes
        
        try:
            # Simple distance calculation (you could enhance with real routing API)
            distance = self.calculate_distance(self.gps_coordinates, next_pickup_gps)
            
            # Estimate travel time based on distance and location type
            # City driving: ~25 km/h, Highway: ~60 km/h
            if self.pickup_location_type in ["Airport", "Train Station"]:
                avg_speed = 40  # km/h (mix of city and highway)
            else:
                avg_speed = 25  # km/h (city driving)
            
            travel_time_hours = distance / avg_speed
            travel_time_minutes = max(5, round(travel_time_hours * 60))  # Minimum 5 minutes
            
            return travel_time_minutes
            
        except Exception as e:
            frappe.log_error(f"Travel time calculation error: {str(e)}")
            return 15  # Default fallback
    
    def calculate_distance(self, gps1, gps2):
        """Calculate distance between two GPS coordinates using Haversine formula"""
        import math
        
        try:
            # Parse GPS coordinates
            lat1, lon1 = map(float, gps1.split(','))
            lat2, lon2 = map(float, gps2.split(','))
            
            # Haversine formula
            R = 6371  # Earth's radius in kilometers
            
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            
            a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon/2) * math.sin(dlon/2))
            
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            return round(distance, 2)
            
        except Exception as e:
            frappe.log_error(f"Distance calculation error: {str(e)}")
            return 5  # Default 5km if calculation fails
    
    def update_pickup_status(self, new_status, notes=None):
        """Update pickup status with timestamp"""
        old_status = self.pickup_status
        self.pickup_status = new_status
        
        # Set actual pickup time when completed
        if new_status == "Completed":
            self.actual_pickup_time = frappe.utils.now_datetime().time()
        
        # Add notes with timestamp
        if notes:
            timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M")
            note_entry = f"[{timestamp}] Status: {old_status} → {new_status}\n{notes}"
            
            if self.special_notes:
                self.special_notes += f"\n\n{note_entry}"
            else:
                self.special_notes = note_entry
        
        # Log the status change
        frappe.logger().info(f"Pickup status updated for {self.guest_name}: {old_status} → {new_status}")
    
    def get_pickup_delay(self):
        """Calculate pickup delay in minutes"""
        if not self.actual_pickup_time or not self.estimated_pickup_time:
            return 0
        
        try:
            from datetime import datetime, date
            
            # Convert times to datetime objects for comparison
            estimated = datetime.combine(date.today(), get_time(self.estimated_pickup_time))
            actual = datetime.combine(date.today(), get_time(self.actual_pickup_time))
            
            # Calculate difference in seconds and convert to minutes
            diff_seconds = (actual - estimated).total_seconds()
            delay_minutes = round(diff_seconds / 60)
            
            return delay_minutes
            
        except Exception as e:
            frappe.log_error(f"Delay calculation error: {str(e)}")
            return 0
    
    def is_pickup_overdue(self):
        """Check if pickup is overdue (more than 10 minutes past scheduled time)"""
        if self.pickup_status in ["Completed", "No Show"]:
            return False
        
        if not self.estimated_pickup_time:
            return False
        
        try:
            from datetime import datetime, date
            
            current_time = datetime.now().time()
            estimated_time = get_time(self.estimated_pickup_time)
            
            # Convert to datetime for comparison
            current_dt = datetime.combine(date.today(), current_time)
            estimated_dt = datetime.combine(date.today(), estimated_time)
            
            # Check if more than 10 minutes overdue
            diff_minutes = (current_dt - estimated_dt).total_seconds() / 60
            
            return diff_minutes > 10
            
        except Exception as e:
            frappe.log_error(f"Overdue check error: {str(e)}")
            return False