# ~/frappe-bench/apps/safari_excursion/safari_excursion/utils/transport_integration.py

import frappe
from frappe import _
from frappe.utils import getdate, add_to_date, get_time

class ExcursionTransportManager:
    """
    Utility class to manage transport bookings for excursions
    
    This class integrates with the existing safari_transport app to create
    and manage transport bookings for excursion pickups and dropoffs.
    """
    
    def __init__(self, excursion_booking):
        self.excursion_booking = excursion_booking
        if isinstance(excursion_booking, str):
            self.excursion_booking = frappe.get_doc("Excursion Booking", excursion_booking)
    
    def create_transport_booking(self):
        """Create a transport booking for excursion pickup and dropoff"""
        if not self.excursion_booking.pickup_required:
            return None
            
        try:
            transport_booking = frappe.get_doc({
                "doctype": "Transport Booking",
                "booking_reference": f"EXC-{self.excursion_booking.booking_number}",
                "booking_type": "Excursion Transfer",
                "booking_party": self.excursion_booking.booking_party,
                "customer": self.excursion_booking.customer,
                "pickup_date": self.excursion_booking.excursion_date,
                "pickup_time": self.excursion_booking.pickup_time,
                "pickup_location": self.excursion_booking.pickup_location,
                "dropoff_location": self.excursion_booking.dropoff_location or self.excursion_booking.pickup_location,
                "passenger_count": self.excursion_booking.total_guests,
                "special_requirements": self.get_combined_requirements(),
                "driver_guide": self.excursion_booking.assigned_guide,
                "vehicle": self.excursion_booking.assigned_vehicle,
                "estimated_arrival_time": self.excursion_booking.estimated_return_time,
                "status": "Confirmed",
                "is_excursion_transport": 1,
                "excursion_booking": self.excursion_booking.name,
                "meeting_point_instructions": self.get_meeting_point_instructions()
            })
            
            transport_booking.insert(ignore_permissions=True)
            transport_booking.submit()
            
            return transport_booking.name
            
        except Exception as e:
            frappe.log_error(f"Transport booking creation error: {str(e)}")
            frappe.msgprint(_("Failed to create transport booking: {0}").format(str(e)))
            return None
    
    def get_combined_requirements(self):
        """Combine all special requirements for transport"""
        requirements = []
        
        if self.excursion_booking.special_requirements:
            requirements.append(f"Special Requirements: {self.excursion_booking.special_requirements}")
            
        if self.excursion_booking.dietary_requirements:
            requirements.append(f"Dietary Requirements: {self.excursion_booking.dietary_requirements}")
            
        if self.excursion_booking.medical_conditions:
            requirements.append(f"Medical Conditions: {self.excursion_booking.medical_conditions}")
            
        if self.excursion_booking.emergency_contact:
            requirements.append(f"Emergency Contact: {self.excursion_booking.emergency_contact}")
            
        return "\n".join(requirements) if requirements else None
    
    def get_meeting_point_instructions(self):
        """Generate meeting point instructions for the driver"""
        instructions = []
        
        instructions.append(f"EXCURSION PICKUP - {self.excursion_booking.excursion_package}")
        instructions.append(f"Guest: {self.excursion_booking.customer_name}")
        instructions.append(f"Contact: {self.excursion_booking.customer_phone}")
        instructions.append(f"Guests: {self.excursion_booking.total_guests} ({self.excursion_booking.adult_count} adults, {self.excursion_booking.child_count or 0} children)")
        
        if self.excursion_booking.transport_notes:
            instructions.append(f"Notes: {self.excursion_booking.transport_notes}")
            
        return "\n".join(instructions)
    
    def update_transport_assignment(self, guide=None, vehicle=None):
        """Update transport booking with guide and vehicle assignments"""
        if not self.excursion_booking.transport_booking:
            return
            
        try:
            transport_doc = frappe.get_doc("Transport Booking", self.excursion_booking.transport_booking)
            
            if guide:
                transport_doc.driver_guide = guide
                # Send notification to driver
                transport_doc.notify_driver()
                
            if vehicle:
                transport_doc.vehicle = vehicle
                
            transport_doc.save()
            
        except Exception as e:
            frappe.log_error(f"Transport assignment update error: {str(e)}")
    
    def cancel_transport_booking(self):
        """Cancel the associated transport booking"""
        if not self.excursion_booking.transport_booking:
            return
            
        try:
            transport_doc = frappe.get_doc("Transport Booking", self.excursion_booking.transport_booking)
            if transport_doc.docstatus == 1:
                transport_doc.cancel()
                frappe.msgprint(_("Transport booking {0} cancelled").format(transport_doc.name))
                
        except Exception as e:
            frappe.log_error(f"Transport cancellation error: {str(e)}")
    
    def get_transport_status(self):
        """Get current transport status"""
        if not self.excursion_booking.transport_booking:
            return None
            
        transport_doc = frappe.get_doc("Transport Booking", self.excursion_booking.transport_booking)
        return {
            "status": transport_doc.status,
            "pickup_confirmation_status": transport_doc.pickup_confirmation_status,
            "driver_guide": transport_doc.driver_guide,
            "vehicle": transport_doc.vehicle,
            "estimated_arrival": transport_doc.estimated_arrival_time
        }

def create_excursion_transport(doc, method):
    """Hook function to create transport booking when excursion booking is submitted"""
    if doc.doctype == "Excursion Booking" and doc.pickup_required:
        transport_manager = ExcursionTransportManager(doc)
        transport_booking = transport_manager.create_transport_booking()
        
        if transport_booking:
            doc.db_set("transport_booking", transport_booking, update_modified=False)

def cancel_excursion_transport(doc, method):
    """Hook function to cancel transport booking when excursion booking is cancelled"""
    if doc.doctype == "Excursion Booking" and doc.transport_booking:
        transport_manager = ExcursionTransportManager(doc)
        transport_manager.cancel_transport_booking()

@frappe.whitelist()
def update_pickup_status(excursion_booking, status, notes=None):
    """Update pickup status from transport booking"""
    doc = frappe.get_doc("Excursion Booking", excursion_booking)
    doc.update_pickup_status(status, notes)
    return {"status": "success", "message": _("Pickup status updated successfully")}

@frappe.whitelist()
def get_transport_details(excursion_booking):
    """Get transport details for an excursion booking"""
    doc = frappe.get_doc("Excursion Booking", excursion_booking)
    transport_manager = ExcursionTransportManager(doc)
    return transport_manager.get_transport_status()

@frappe.whitelist()
def assign_vehicle_to_excursion(excursion_booking, vehicle):
    """Assign vehicle to excursion and update transport booking"""
    doc = frappe.get_doc("Excursion Booking", excursion_booking)
    doc.assign_guide_and_vehicle(vehicle=vehicle)
    
    transport_manager = ExcursionTransportManager(doc)
    transport_manager.update_transport_assignment(vehicle=vehicle)
    
    return {"status": "success", "message": _("Vehicle assigned successfully")}

@frappe.whitelist()
def assign_guide_to_excursion(excursion_booking, guide):
    """Assign guide to excursion and update transport booking"""
    doc = frappe.get_doc("Excursion Booking", excursion_booking)
    doc.assign_guide_and_vehicle(guide=guide)
    
    transport_manager = ExcursionTransportManager(doc)
    transport_manager.update_transport_assignment(guide=guide)
    
    return {"status": "success", "message": _("Guide assigned successfully")}

class ExcursionTransportAutomation:
    """
    Automation utilities for excursion transport management
    """
    
    @staticmethod
    def send_pre_excursion_reminders():
        """Send reminders to guides and customers before excursions"""
        try:
            # Get excursions for tomorrow
            tomorrow = add_to_date(getdate(), days=1)
            
            excursions = frappe.get_all(
                "Excursion Booking",
                filters={
                    "excursion_date": tomorrow,
                    "booking_status": "Confirmed",
                    "reminder_sent": 0
                },
                fields=["name", "customer_email", "assigned_guide"]
            )
            
            for excursion in excursions:
                doc = frappe.get_doc("Excursion Booking", excursion.name)
                
                # Send customer reminder
                if excursion.customer_email:
                    doc.send_reminder_notification()
                
                # Send guide reminder
                if excursion.assigned_guide:
                    ExcursionTransportAutomation.send_guide_reminder(doc)
                    
        except Exception as e:
            frappe.log_error(f"Pre-excursion reminder error: {str(e)}")
    
    @staticmethod
    def send_guide_reminder(excursion_booking):
        """Send reminder to assigned guide"""
        try:
            guide = frappe.get_doc("Safari Guide", excursion_booking.assigned_guide)
            if not guide.email:
                return
                
            frappe.sendmail(
                recipients=[guide.email],
                subject=f"Excursion Assignment Tomorrow - {excursion_booking.booking_number}",
                message=f"""
                <h3>Excursion Assignment Reminder</h3>
                <p>You have an excursion assignment tomorrow:</p>
                
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr><td><strong>Booking:</strong></td><td>{excursion_booking.booking_number}</td></tr>
                    <tr><td><strong>Excursion:</strong></td><td>{excursion_booking.excursion_package}</td></tr>
                    <tr><td><strong>Date:</strong></td><td>{excursion_booking.excursion_date}</td></tr>
                    <tr><td><strong>Pickup Time:</strong></td><td>{excursion_booking.pickup_time}</td></tr>
                    <tr><td><strong>Pickup Location:</strong></td><td>{excursion_booking.pickup_location}</td></tr>
                    <tr><td><strong>Guests:</strong></td><td>{excursion_booking.total_guests}</td></tr>
                    <tr><td><strong>Customer:</strong></td><td>{excursion_booking.customer_name}</td></tr>
                    <tr><td><strong>Contact:</strong></td><td>{excursion_booking.customer_phone}</td></tr>
                </table>
                
                <p>Please be ready and confirm your availability.</p>
                """
            )
            
        except Exception as e:
            frappe.log_error(f"Guide reminder error: {str(e)}")
    
    @staticmethod
    def update_excursion_status():
        """Update excursion status based on current time"""
        try:
            from frappe.utils import now_datetime, get_datetime
            
            current_time = now_datetime()
            
            # Mark excursions as "In Progress" if departure time has passed
            in_progress_excursions = frappe.get_all(
                "Excursion Booking",
                filters={
                    "excursion_date": getdate(),
                    "booking_status": "Confirmed",
                    "excursion_status": "Scheduled"
                },
                fields=["name", "departure_time"]
            )
            
            for excursion in in_progress_excursions:
                departure_datetime = get_datetime(f"{getdate()} {excursion.departure_time}")
                if current_time >= departure_datetime:
                    frappe.db.set_value("Excursion Booking", excursion.name, 
                                      "excursion_status", "In Progress")
            
            # Mark excursions as "Completed" if estimated return time has passed
            completed_excursions = frappe.get_all(
                "Excursion Booking",
                filters={
                    "excursion_date": getdate(),
                    "excursion_status": "In Progress"
                },
                fields=["name", "estimated_return_time"]
            )
            
            for excursion in completed_excursions:
                if excursion.estimated_return_time:
                    return_datetime = get_datetime(f"{getdate()} {excursion.estimated_return_time}")
                    if current_time >= return_datetime:
                        frappe.db.set_value("Excursion Booking", excursion.name, 
                                          "excursion_status", "Completed")
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Excursion status update error: {str(e)}")
