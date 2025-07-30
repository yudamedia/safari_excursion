# ~/frappe-bench/apps/safari_excursion/safari_excursion/utils/multiple_pickup_transport.py

import frappe
from frappe import _
from frappe.utils import getdate, get_time, add_to_date, time_diff_in_seconds
from datetime import datetime, timedelta

class MultiplePickupManager:
    """
    Utility class to manage multiple hotel pickup scenarios for excursions
    
    This class handles:
    - Creating pickup schedules for multiple hotels
    - Optimizing pickup routes
    - Managing individual pickup confirmations
    - Driver notifications with complete pickup schedule
    """
    
    def __init__(self, excursion_booking):
        self.excursion_booking = excursion_booking
        if isinstance(excursion_booking, str):
            self.excursion_booking = frappe.get_doc("Excursion Booking", excursion_booking)
    
    def create_pickup_schedule(self):
        """Create optimized pickup schedule for all guests"""
        if not self.excursion_booking.pickup_required:
            return []
            
        if self.excursion_booking.pickup_type != "Individual Hotel Pickups":
            return []
        
        # Get guest accommodation details
        guest_locations = self.get_guest_accommodation_details()
        
        if not guest_locations:
            frappe.msgprint(_("No guest accommodation details found for pickup scheduling"))
            return []
        
        # Optimize pickup route
        optimized_schedule = self.optimize_pickup_route(guest_locations)
        
        # Create pickup schedule records
        self.create_pickup_records(optimized_schedule)
        
        return optimized_schedule
    
    def get_guest_accommodation_details(self):
        """Get accommodation details for all guests in the booking"""
        guest_locations = []
        
        if not self.excursion_booking.guests:
            # If no individual guest records, create from booking party
            if self.excursion_booking.booking_party:
                booking_party = frappe.get_doc("Booking Party", self.excursion_booking.booking_party)
                
                # Primary guest accommodation
                if booking_party.primary_guest:
                    guest = frappe.get_doc("Safari Guest", booking_party.primary_guest)
                    location = self.get_guest_accommodation(guest)
                    if location:
                        location['guest_name'] = guest.guest_name
                        location['contact_phone'] = guest.phone or self.excursion_booking.customer_phone
                        guest_locations.append(location)
                
                # Additional guests (if they have different accommodations)
                for guest_row in booking_party.guests or []:
                    guest = frappe.get_doc("Safari Guest", guest_row.guest)
                    location = self.get_guest_accommodation(guest)
                    if location and not self.is_duplicate_location(location, guest_locations):
                        location['guest_name'] = guest.guest_name
                        location['contact_phone'] = guest.phone or self.excursion_booking.customer_phone
                        guest_locations.append(location)
        else:
            # Use individual guest records from booking
            for guest_row in self.excursion_booking.guests:
                if guest_row.guest:
                    guest = frappe.get_doc("Safari Guest", guest_row.guest)
                    location = self.get_guest_accommodation(guest)
                    if location and not self.is_duplicate_location(location, guest_locations):
                        location['guest_name'] = guest_row.guest_name
                        location['contact_phone'] = guest_row.phone or self.excursion_booking.customer_phone
                        guest_locations.append(location)
        
        return guest_locations
    
    def get_guest_accommodation(self, guest):
        """Get accommodation details for a specific guest"""
        # Check if guest has current accommodation booking
        accommodation_booking = frappe.db.get_value(
            "Accommodation Booking",
            {
                "booking_party": self.excursion_booking.booking_party,
                "check_in_date": ["<=", self.excursion_booking.excursion_date],
                "check_out_date": [">=", self.excursion_booking.excursion_date],
                "status": ["in", ["Confirmed", "Checked In"]]
            },
            ["accommodation", "room_type"]
        )
        
        if accommodation_booking:
            accommodation = frappe.get_doc("Accommodation", accommodation_booking[0])
            return {
                "location_type": "Hotel",
                "location_name": accommodation.accommodation_name,
                "address": accommodation.address,
                "gps_coordinates": accommodation.gps_coordinates,
                "contact_phone": accommodation.contact_phone
            }
        
        # Fallback to guest's preferred accommodation or manually entered location
        if hasattr(guest, 'current_accommodation') and guest.current_accommodation:
            return {
                "location_type": "Hotel",
                "location_name": guest.current_accommodation,
                "address": getattr(guest, 'accommodation_address', ''),
                "gps_coordinates": getattr(guest, 'accommodation_gps', ''),
                "contact_phone": guest.phone
            }
        
        return None
    
    def is_duplicate_location(self, new_location, existing_locations):
        """Check if location already exists in the list"""
        for existing in existing_locations:
            if (existing['location_name'].lower() == new_location['location_name'].lower() and
                existing['address'] == new_location['address']):
                return True
        return False
    
    def optimize_pickup_route(self, guest_locations):
        """Optimize pickup route based on location proximity and traffic patterns"""
        if not guest_locations:
            return []
        
        # Simple optimization - in a real implementation, you might use Google Maps API
        # For now, we'll sort by distance from city center and apply traffic considerations
        
        optimized_locations = []
        departure_time = get_time(self.excursion_booking.departure_time)
        
        # Calculate pickup times working backwards from departure
        pickup_buffer = 30  # 30 minutes buffer before departure
        travel_between_hotels = 15  # Average 15 minutes between hotels
        pickup_duration = 5  # 5 minutes per pickup
        
        # Calculate first pickup time
        total_pickup_time = len(guest_locations) * pickup_duration + (len(guest_locations) - 1) * travel_between_hotels
        first_pickup_time = self.subtract_minutes_from_time(departure_time, total_pickup_time + pickup_buffer)
        
        # Sort locations (in real implementation, use GPS coordinates)
        sorted_locations = self.sort_locations_by_route(guest_locations)
        
        current_time = first_pickup_time
        for i, location in enumerate(sorted_locations, 1):
            pickup_record = {
                "guest_name": location['guest_name'],
                "pickup_order": i,
                "pickup_location_type": location['location_type'],
                "pickup_location_name": location['location_name'],
                "pickup_address": location['address'],
                "gps_coordinates": location.get('gps_coordinates', ''),
                "contact_phone": location['contact_phone'],
                "estimated_pickup_time": current_time,
                "pickup_status": "Pending",
                "meeting_instructions": self.generate_meeting_instructions(location),
                "travel_time_to_next": travel_between_hotels if i < len(sorted_locations) else 0
            }
            
            optimized_locations.append(pickup_record)
            
            # Calculate next pickup time
            if i < len(sorted_locations):
                current_time = self.add_minutes_to_time(current_time, pickup_duration + travel_between_hotels)
        
        return optimized_locations
    
    def sort_locations_by_route(self, locations):
        """Sort locations for optimal route (simplified version)"""
        # In a real implementation, this would use GPS coordinates and routing APIs
        # For now, sort by location type (hotels first, then others)
        
        return sorted(locations, key=lambda x: (
            0 if x['location_type'] == 'Hotel' else 1,
            x['location_name']
        ))
    
    def subtract_minutes_from_time(self, time_obj, minutes):
        """Subtract minutes from a time object"""
        if isinstance(time_obj, str):
            time_obj = datetime.strptime(time_obj, "%H:%M:%S").time()
        
        dt = datetime.combine(datetime.today(), time_obj)
        dt = dt - timedelta(minutes=minutes)
        return dt.time()
    
    def add_minutes_to_time(self, time_obj, minutes):
        """Add minutes to a time object"""
        if isinstance(time_obj, str):
            time_obj = datetime.strptime(time_obj, "%H:%M:%S").time()
        
        dt = datetime.combine(datetime.today(), time_obj)
        dt = dt + timedelta(minutes=minutes)
        return dt.time()
    
    def generate_meeting_instructions(self, location):
        """Generate meeting instructions for each location"""
        instructions = []
        
        if location['location_type'] == 'Hotel':
            instructions.append("Meet at hotel main lobby/reception")
            instructions.append("Look for safari vehicle with company branding")
            instructions.append("Driver will call guest 5 minutes before arrival")
        else:
            instructions.append("Meet at main entrance")
            instructions.append("Look for safari vehicle")
        
        if location.get('landmark'):
            instructions.append(f"Landmark: {location['landmark']}")
        
        return "\n".join(instructions)
    
    def create_pickup_records(self, pickup_schedule):
        """Create pickup records in the excursion booking"""
        # Clear existing pickup records
        self.excursion_booking.guest_pickups = []
        
        # Add new pickup records
        for pickup in pickup_schedule:
            self.excursion_booking.append("guest_pickups", pickup)
        
        self.excursion_booking.save()
    
    def send_individual_pickup_confirmations(self):
        """Send pickup confirmation to each guest individually"""
        if not self.excursion_booking.guest_pickups:
            return
        
        for pickup in self.excursion_booking.guest_pickups:
            try:
                self.send_pickup_confirmation_to_guest(pickup)
            except Exception as e:
                frappe.log_error(f"Pickup confirmation error for {pickup.guest_name}: {str(e)}")
    
    def send_pickup_confirmation_to_guest(self, pickup):
        """Send pickup confirmation to individual guest"""
        if not pickup.contact_phone:
            return
        
        # Try to get guest email
        guest_email = None
        if pickup.guest_name and self.excursion_booking.booking_party:
            booking_party = frappe.get_doc("Booking Party", self.excursion_booking.booking_party)
            for guest_row in booking_party.guests or []:
                guest = frappe.get_doc("Safari Guest", guest_row.guest)
                if guest.guest_name == pickup.guest_name:
                    guest_email = guest.email
                    break
        
        if guest_email:
            subject = f"Pickup Confirmation - {self.excursion_booking.excursion_package}"
            
            message = f"""
            <h3>Your Excursion Pickup Details</h3>
            <p>Dear {pickup.guest_name},</p>
            
            <p>Your pickup for the {self.excursion_booking.excursion_package} excursion has been confirmed:</p>
            
            <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr><td><strong>Pickup Time:</strong></td><td>{pickup.estimated_pickup_time}</td></tr>
                <tr><td><strong>Pickup Location:</strong></td><td>{pickup.pickup_location_name}</td></tr>
                <tr><td><strong>Address:</strong></td><td>{pickup.pickup_address}</td></tr>
                <tr><td><strong>Pickup Order:</strong></td><td>#{pickup.pickup_order}</td></tr>
            </table>
            
            <h4>Meeting Instructions:</h4>
            <p>{pickup.meeting_instructions or 'Meet at main entrance/lobby'}</p>
            
            <p><strong>Important:</strong></p>
            <ul>
                <li>Please be ready 5 minutes before pickup time</li>
                <li>Have your phone ready - the driver will call you</li>
                <li>Look for our safari vehicle with company branding</li>
                <li>Bring water and sun protection</li>
            </ul>
            
            <p>Driver contact will be shared closer to the excursion date.</p>
            <p>Looking forward to an amazing excursion with you!</p>
            """
            
            frappe.sendmail(
                recipients=[guest_email],
                subject=subject,
                message=message,
                reference_doctype=self.excursion_booking.doctype,
                reference_name=self.excursion_booking.name
            )
    
    def generate_driver_pickup_schedule(self):
        """Generate comprehensive pickup schedule for driver"""
        if not self.excursion_booking.guest_pickups:
            return ""
        
        schedule_html = f"""
        <h3>Pickup Schedule - {self.excursion_booking.excursion_package}</h3>
        <p><strong>Date:</strong> {self.excursion_booking.excursion_date}</p>
        <p><strong>Total Guests:</strong> {self.excursion_booking.total_guests}</p>
        <p><strong>Departure Time:</strong> {self.excursion_booking.departure_time}</p>
        
        <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background-color: #f0f0f0;">
                <th>Order</th>
                <th>Time</th>
                <th>Guest</th>
                <th>Location</th>
                <th>Contact</th>
                <th>Notes</th>
            </tr>
        """
        
        for pickup in self.excursion_booking.guest_pickups:
            schedule_html += f"""
            <tr>
                <td>{pickup.pickup_order}</td>
                <td><strong>{pickup.estimated_pickup_time}</strong></td>
                <td>{pickup.guest_name}</td>
                <td>{pickup.pickup_location_name}<br><small>{pickup.pickup_address}</small></td>
                <td>{pickup.contact_phone}</td>
                <td><small>{pickup.meeting_instructions or ''}</small></td>
            </tr>
            """
        
        schedule_html += """
        </table>
        
        <h4>Driver Instructions:</h4>
        <ul>
            <li>Call each guest 5 minutes before arrival</li>
            <li>Allow 5 minutes per pickup</li>
            <li>Follow the pickup order strictly</li>
            <li>Update pickup status in the system</li>
            <li>Contact operations if any guest is not ready after 10 minutes</li>
        </ul>
        """
        
        return schedule_html

@frappe.whitelist()
def create_pickup_schedule(excursion_booking):
    """Create pickup schedule for excursion booking"""
    try:
        manager = MultiplePickupManager(excursion_booking)
        schedule = manager.create_pickup_schedule()
        
        return {
            "status": "success",
            "message": f"Pickup schedule created for {len(schedule)} locations",
            "schedule": schedule
        }
        
    except Exception as e:
        frappe.log_error(f"Pickup schedule creation error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def update_pickup_status(excursion_booking, pickup_order, status, notes=None):
    """Update individual pickup status"""
    try:
        doc = frappe.get_doc("Excursion Booking", excursion_booking)
        
        for pickup in doc.guest_pickups:
            if pickup.pickup_order == int(pickup_order):
                pickup.pickup_status = status
                if status == "Completed":
                    pickup.actual_pickup_time = frappe.utils.now_datetime().time()
                if notes:
                    pickup.special_notes = f"{pickup.special_notes or ''}\nStatus Update: {notes}"
                break
        
        doc.save()
        
        return {
            "status": "success",
            "message": "Pickup status updated successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Pickup status update error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }