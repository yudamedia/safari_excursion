# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_booking/excursion_booking.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_to_date, time_diff_in_hours, get_time, now_datetime
from safari_excursion.utils.pricing_calculator import ExcursionPricingCalculator
from safari_excursion.utils.transport_integration import ExcursionTransportManager

class ExcursionBooking(Document):
    """
    DocType controller for Excursion Booking
    
    This controller handles the creation and management of excursion bookings,
    integrates with the transport system for pickup/dropoff logistics,
    and manages guest communications.
    """
    
    def autoname(self):
        """Set booking number automatically"""
        if not self.booking_number:
            # Generate format: EXB-YYYY-MM-#####
            from frappe.model.naming import make_autoname
            self.name = make_autoname("EXB-.YYYY.-.MM.-.#####")
            self.booking_number = self.name
    
    def validate(self):
        """Validate document before saving"""
        self.validate_excursion_package()
        self.validate_capacity()
        self.validate_timing()
        self.validate_guests()
        self.calculate_pricing()
        self.set_estimated_times()
        self.validate_pickup_requirements()
    
    def validate_excursion_package(self):
        """Validate excursion package availability and details"""
        if not self.excursion_package:
            frappe.throw(_("Excursion Package is required"))
            
        package = frappe.get_doc("Excursion Package", self.excursion_package)
        
        if package.package_status != "Active":
            frappe.throw(_("Selected excursion package is not active"))
            
        # Set duration from package
        self.duration_hours = package.duration_hours
        
        # Check if excursion is available on selected date
        if not self.is_package_available_on_date(package):
            frappe.throw(_("Excursion package is not available on the selected date"))
    
    def validate_capacity(self):
        """Validate guest count against package capacity"""
        if not self.total_guests:
            self.total_guests = (self.adult_count or 0) + (self.child_count or 0)
        
        if self.total_guests <= 0:
            frappe.throw(_("Total guests must be greater than 0"))
            
        package = frappe.get_doc("Excursion Package", self.excursion_package)
        if self.total_guests > package.max_capacity:
            frappe.throw(_("Total guests ({0}) exceeds package capacity ({1})").format(
                self.total_guests, package.max_capacity))
    
    def validate_timing(self):
        """Validate excursion timing and booking deadline"""
        if not self.excursion_date:
            frappe.throw(_("Excursion Date is required"))
            
        if getdate(self.excursion_date) < getdate():
            frappe.throw(_("Excursion date cannot be in the past"))
            
        # Check booking deadline
        package = frappe.get_doc("Excursion Package", self.excursion_package)
        booking_deadline_hours = package.booking_deadline_hours or 24
        
        excursion_datetime = f"{self.excursion_date} {self.departure_time or '08:00:00'}"
        current_datetime = now_datetime()
        
        time_until_excursion = time_diff_in_hours(excursion_datetime, current_datetime)
        
        if time_until_excursion < booking_deadline_hours:
            frappe.throw(_("Booking must be made at least {0} hours before excursion time").format(
                booking_deadline_hours))
    
    def validate_guests(self):
        """Validate guest details"""
        if self.guests:
            guest_count = len(self.guests)
            if guest_count != self.total_guests:
                frappe.throw(_("Number of guest records ({0}) does not match total guests ({1})").format(
                    guest_count, self.total_guests))
    
    def validate_pickup_requirements(self):
        """Validate pickup location if pickup is required"""
        if self.pickup_required:
            if not self.pickup_location:
                frappe.throw(_("Pickup Location is required when pickup is enabled"))
            if not self.pickup_time:
                frappe.throw(_("Pickup Time is required when pickup is enabled"))
    
    def calculate_pricing(self):
        """Calculate total pricing for the excursion"""
        calculator = ExcursionPricingCalculator(self)
        pricing_details = calculator.calculate_total_price()
        
        self.base_amount = pricing_details.get('base_amount', 0)
        self.child_discount = pricing_details.get('child_discount', 0)
        self.group_discount = pricing_details.get('group_discount', 0)
        self.additional_charges = pricing_details.get('additional_charges', 0)
        self.total_amount = pricing_details.get('total_amount', 0)
        
        # Calculate balance due
        self.balance_due = self.total_amount - (self.deposit_amount or 0)
    
    def set_estimated_times(self):
        """Set estimated pickup and return times"""
        if self.departure_time and self.duration_hours:
            # Calculate estimated return time
            departure_datetime = f"{self.excursion_date} {self.departure_time}"
            return_datetime = add_to_date(departure_datetime, hours=self.duration_hours)
            self.estimated_return_time = get_time(return_datetime)
            
            # Set pickup time (usually 30-60 minutes before departure)
            if self.pickup_required and not self.pickup_time:
                pickup_datetime = add_to_date(departure_datetime, minutes=-45)
                self.pickup_time = get_time(pickup_datetime)
    
    def is_package_available_on_date(self, package):
        """Check if package is available on the selected date"""
        # Check day of week availability
        excursion_day = getdate(self.excursion_date).strftime('%A')
        
        if package.available_days:
            available_days = [day.day for day in package.available_days]
            if excursion_day not in available_days:
                return False
        
        # Check seasonal availability
        if package.seasonal_availability:
            for season in package.seasonal_availability:
                if (getdate(season.start_date) <= getdate(self.excursion_date) <= 
                    getdate(season.end_date)):
                    return season.is_available
        
        return True
    
    def on_submit(self):
        """Actions to perform when booking is submitted"""
        self.booking_status = "Confirmed"
        self.create_transport_booking()
        self.create_park_booking()
        self.send_confirmation_notifications()
        self.create_excursion_operation()
        
    def create_park_booking(self):
        """Create park booking if excursion visits parks"""
        try:
            from safari_excursion.utils.parks_integration import ExcursionParkFeeCalculator
            
            park_calculator = ExcursionParkFeeCalculator(self)
            if park_calculator.has_park_visits():
                park_booking = park_calculator.create_park_booking()
                
                if park_booking:
                    self.park_booking = park_booking
                    frappe.msgprint(_("Park booking {0} created successfully").format(
                        park_booking))
                    
                    # Update pricing with park fees
                    park_fees = park_calculator.calculate_park_fees()
                    if park_fees["total_fees"] > 0:
                        self.additional_charges = (self.additional_charges or 0) + park_fees["total_fees"]
                        self.total_amount = (self.base_amount or 0) - (self.child_discount or 0) - (self.group_discount or 0) + self.additional_charges
                        self.balance_due = self.total_amount - (self.deposit_amount or 0)
                        
                        frappe.msgprint(_("Park fees of ${0} added to booking").format(
                            park_fees["total_fees"]))
        except Exception as e:
            frappe.log_error(f"Park booking creation error: {str(e)}")
            frappe.msgprint(_("Warning: Could not create park booking. Please create manually if required."))
        
    def create_transport_booking(self):
        """Create transport booking for pickup and dropoff"""
        if self.pickup_required:
            transport_manager = ExcursionTransportManager(self)
            transport_booking = transport_manager.create_transport_booking()
            
            if transport_booking:
                self.transport_booking = transport_booking
                frappe.msgprint(_("Transport booking {0} created successfully").format(
                    transport_booking))
    
    def create_excursion_operation(self):
        """Create excursion operation record for daily tracking"""
        operation = frappe.get_doc({
            "doctype": "Excursion Operation",
            "excursion_booking": self.name,
            "excursion_package": self.excursion_package,
            "operation_date": self.excursion_date,
            "departure_time": self.departure_time,
            "guest_count": self.total_guests,
            "assigned_guide": self.assigned_guide,
            "assigned_vehicle": self.assigned_vehicle,
            "operation_status": "Scheduled"
        })
        
        operation.insert(ignore_permissions=True)
        self.excursion_operation = operation.name
        
        frappe.msgprint(_("Excursion operation {0} created successfully").format(
            operation.name))
    
    def send_confirmation_notifications(self):
        """Send booking confirmation to customer and guide"""
        try:
            # Send customer confirmation
            if self.customer_email:
                self.send_customer_confirmation()
                self.confirmation_sent = 1
            
            # Send guide notification if guide is assigned
            if self.assigned_guide:
                self.send_guide_notification()
                
        except Exception as e:
            frappe.log_error(f"Notification error: {str(e)}")
            frappe.msgprint(_("Booking confirmed but notification failed. Please check email settings."))
    
    def send_customer_confirmation(self):
        """Send booking confirmation email to customer"""
        template = frappe.get_doc("Email Template", "Excursion Booking Confirmation")
        
        subject = frappe.render_template(template.subject, {"doc": self})
        message = frappe.render_template(template.response, {"doc": self})
        
        frappe.sendmail(
            recipients=[self.customer_email],
            subject=subject,
            message=message,
            reference_doctype=self.doctype,
            reference_name=self.name
        )
    
    def send_guide_notification(self):
        """Send assignment notification to guide"""
        guide = frappe.get_doc("Safari Guide", self.assigned_guide)
        if not guide.email:
            return
            
        template = frappe.get_doc("Email Template", "Excursion Guide Assignment")
        
        subject = frappe.render_template(template.subject, {"doc": self})
        message = frappe.render_template(template.response, {"doc": self})
        
        frappe.sendmail(
            recipients=[guide.email],
            subject=subject,
            message=message,
            reference_doctype=self.doctype,
            reference_name=self.name
        )
    
    def on_cancel(self):
        """Actions to perform when booking is cancelled"""
        self.booking_status = "Cancelled"
        self.cancellation_date = now_datetime()
        
        # Cancel related transport booking
        if self.transport_booking:
            transport_doc = frappe.get_doc("Transport Booking", self.transport_booking)
            if transport_doc.docstatus == 1:
                transport_doc.cancel()
        
        # Cancel related park booking
        if self.park_booking:
            try:
                park_doc = frappe.get_doc("Park Booking", self.park_booking)
                if park_doc.docstatus == 1:
                    park_doc.cancel()
            except Exception as e:
                frappe.log_error(f"Park booking cancellation error: {str(e)}")
                
        # Cancel related excursion operation
        if self.excursion_operation:
            operation_doc = frappe.get_doc("Excursion Operation", self.excursion_operation)
            if operation_doc.docstatus == 1:
                operation_doc.cancel()
        
        # Send cancellation notifications
        self.send_cancellation_notifications()
    
    def send_cancellation_notifications(self):
        """Send cancellation notifications to customer and guide"""
        try:
            # Notify customer
            if self.customer_email:
                frappe.sendmail(
                    recipients=[self.customer_email],
                    subject=f"Excursion Booking Cancelled - {self.booking_number}",
                    message=f"""
                    <p>Dear {self.customer_name},</p>
                    <p>Your excursion booking {self.booking_number} for {self.excursion_package} 
                    on {self.excursion_date} has been cancelled.</p>
                    <p>Reason: {self.cancellation_reason or 'Not specified'}</p>
                    <p>Refund details will be communicated separately if applicable.</p>
                    """
                )
            
            # Notify guide
            if self.assigned_guide:
                guide = frappe.get_doc("Safari Guide", self.assigned_guide)
                if guide.email:
                    frappe.sendmail(
                        recipients=[guide.email],
                        subject=f"Excursion Assignment Cancelled - {self.booking_number}",
                        message=f"""
                        <p>The excursion assignment for booking {self.booking_number} 
                        on {self.excursion_date} has been cancelled.</p>
                        <p>You are no longer required for this excursion.</p>
                        """
                    )
                    
        except Exception as e:
            frappe.log_error(f"Cancellation notification error: {str(e)}")
    
    def update_pickup_status(self, status, notes=None):
        """Update pickup confirmation status"""
        valid_statuses = ["Pending", "Confirmed", "Guest Located", "In Transit", "Completed"]
        
        if status not in valid_statuses:
            frappe.throw(_("Invalid pickup status: {0}").format(status))
            
        old_status = self.pickup_confirmation_status
        self.pickup_confirmation_status = status
        
        if status == "In Transit":
            self.excursion_status = "In Progress"
        elif status == "Completed":
            self.excursion_status = "Completed"
            
        if notes:
            if not self.transport_notes:
                self.transport_notes = notes
            else:
                self.transport_notes += f"\n\nStatus Update: {notes}"
                
        self.save()
        
        # Send status update notifications
        self.send_status_update_notification(old_status, status)
    
    def send_status_update_notification(self, old_status, new_status):
        """Send status update notifications"""
        try:
            if new_status == "Guest Located" and self.customer_email:
                frappe.sendmail(
                    recipients=[self.customer_email],
                    subject=f"Your Guide Has Arrived - {self.booking_number}",
                    message=f"""
                    <p>Dear {self.customer_name},</p>
                    <p>Your guide has arrived at the pickup location for your excursion.</p>
                    <p>Guide: {self.get_guide_name()}</p>
                    <p>Vehicle: {self.get_vehicle_details()}</p>
                    <p>Please proceed to the meeting point.</p>
                    """
                )
            
            elif new_status == "In Transit" and self.customer_email:
                frappe.sendmail(
                    recipients=[self.customer_email],
                    subject=f"Excursion Started - {self.booking_number}",
                    message=f"""
                    <p>Dear {self.customer_name},</p>
                    <p>Your excursion has begun! We hope you have a wonderful experience.</p>
                    <p>Expected return time: {self.estimated_return_time}</p>
                    """
                )
                
        except Exception as e:
            frappe.log_error(f"Status update notification error: {str(e)}")
    
    def get_guide_name(self):
        """Get assigned guide name"""
        if self.assigned_guide:
            return frappe.db.get_value("Safari Guide", self.assigned_guide, "guide_name")
        return "Not assigned"
    
    def get_vehicle_details(self):
        """Get assigned vehicle details"""
        if self.assigned_vehicle:
            vehicle = frappe.get_doc("Vehicle", self.assigned_vehicle)
            return f"{vehicle.vehicle_type} - {vehicle.license_plate}"
        return "Not assigned"
    
    def get_primary_guest_contact(self):
        """Get primary guest contact details for transport notifications"""
        contact_info = []
        if self.customer_phone:
            contact_info.append(f"Phone: {self.customer_phone}")
        if self.customer_email:
            contact_info.append(f"Email: {self.customer_email}")
        return " | ".join(contact_info) if contact_info else "Contact details not available"
    
    @frappe.whitelist()
    def assign_guide_and_vehicle(self, guide=None, vehicle=None):
        """Assign guide and vehicle to excursion"""
        if guide:
            # Check guide availability
            if self.is_guide_available(guide):
                self.assigned_guide = guide
                self.send_guide_notification()
            else:
                frappe.throw(_("Guide {0} is not available on {1}").format(
                    guide, self.excursion_date))
        
        if vehicle:
            # Check vehicle availability
            if self.is_vehicle_available(vehicle):
                self.assigned_vehicle = vehicle
            else:
                frappe.throw(_("Vehicle {0} is not available on {1}").format(
                    vehicle, self.excursion_date))
        
        self.save()
        
        # Update transport booking if exists
        if self.transport_booking:
            transport_doc = frappe.get_doc("Transport Booking", self.transport_booking)
            if guide and not transport_doc.driver_guide:
                transport_doc.driver_guide = guide
            if vehicle and not transport_doc.vehicle:
                transport_doc.vehicle = vehicle
            transport_doc.save()
    
    def is_guide_available(self, guide):
        """Check if guide is available on excursion date"""
        # Check for conflicting assignments
        conflicts = frappe.db.count("Excursion Booking", {
            "assigned_guide": guide,
            "excursion_date": self.excursion_date,
            "booking_status": ["in", ["Confirmed", "In Progress"]],
            "name": ["!=", self.name]
        })
        
        return conflicts == 0
    
    def is_vehicle_available(self, vehicle):
        """Check if vehicle is available on excursion date"""
        # Check for conflicting assignments
        conflicts = frappe.db.count("Excursion Booking", {
            "assigned_vehicle": vehicle,
            "excursion_date": self.excursion_date,
            "booking_status": ["in", ["Confirmed", "In Progress"]],
            "name": ["!=", self.name]
        })
        
        return conflicts == 0
    
    @frappe.whitelist()
    def send_reminder_notification(self):
        """Send pre-excursion reminder to customer"""
        if not self.customer_email:
            frappe.throw(_("Customer email not available"))
            
        try:
            frappe.sendmail(
                recipients=[self.customer_email],
                subject=f"Excursion Reminder - Tomorrow - {self.booking_number}",
                message=f"""
                <h3>Excursion Reminder</h3>
                <p>Dear {self.customer_name},</p>
                <p>This is a reminder about your excursion tomorrow:</p>
                
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr><td><strong>Excursion:</strong></td><td>{self.excursion_package}</td></tr>
                    <tr><td><strong>Date:</strong></td><td>{self.excursion_date}</td></tr>
                    <tr><td><strong>Pickup Time:</strong></td><td>{self.pickup_time}</td></tr>
                    <tr><td><strong>Pickup Location:</strong></td><td>{self.pickup_location}</td></tr>
                    <tr><td><strong>Guide:</strong></td><td>{self.get_guide_name()}</td></tr>
                </table>
                
                <p>Please be ready 10 minutes before pickup time.</p>
                <p>Looking forward to providing you with an amazing experience!</p>
                """
            )
            
            self.reminder_sent = 1
            self.save()
            frappe.msgprint(_("Reminder sent successfully"))
            
        except Exception as e:
            frappe.log_error(f"Reminder notification error: {str(e)}")
            frappe.throw(_("Failed to send reminder notification"))

def validate_capacity_and_timing(doc, method):
    """Validation hook called from hooks.py"""
    # This function is called as a document event hook
    # Additional validations can be added here if needed
    pass