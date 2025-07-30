# ~/frappe-bench/apps/safari_excursion/safari_excursion/utils/driver_pickup_notifications.py

import frappe
from frappe import _
from frappe.utils import getdate, add_days, get_time, now_datetime

def send_driver_pickup_schedule(excursion_booking):
    """Send comprehensive pickup schedule to assigned driver/guide"""
    try:
        booking = frappe.get_doc("Excursion Booking", excursion_booking)
        
        if not booking.assigned_guide:
            return {"status": "error", "message": "No guide assigned"}
        
        guide = frappe.get_doc("Safari Guide", booking.assigned_guide)
        if not guide.email:
            return {"status": "error", "message": "Guide has no email address"}
        
        # Generate pickup schedule
        if booking.pickup_type == "Individual Hotel Pickups":
            schedule_content = generate_individual_pickup_schedule(booking)
        else:
            schedule_content = generate_central_pickup_schedule(booking)
        
        subject = f"Pickup Schedule - {booking.excursion_package} - {booking.excursion_date}"
        
        message = f"""
        <h2>Excursion Pickup Schedule</h2>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h3>Booking Overview</h3>
            <table style="width: 100%;">
                <tr><td><strong>Booking Number:</strong></td><td>{booking.booking_number}</td></tr>
                <tr><td><strong>Excursion:</strong></td><td>{booking.excursion_package}</td></tr>
                <tr><td><strong>Date:</strong></td><td>{booking.excursion_date}</td></tr>
                <tr><td><strong>Departure Time:</strong></td><td>{booking.departure_time}</td></tr>
                <tr><td><strong>Total Guests:</strong></td><td>{booking.total_guests}</td></tr>
                <tr><td><strong>Vehicle:</strong></td><td>{booking.assigned_vehicle or 'TBA'}</td></tr>
            </table>
        </div>
        
        {schedule_content}
        
        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h4>🚨 Important Driver Instructions</h4>
            <ul>
                <li><strong>Call each guest 5 minutes before arrival</strong></li>
                <li><strong>Allow 5 minutes maximum per pickup</strong></li>
                <li><strong>Follow pickup order strictly</strong></li>
                <li><strong>Update pickup status in real-time via phone/app</strong></li>
                <li><strong>If guest not ready after 10 minutes, contact operations immediately</strong></li>
                <li><strong>Keep vehicle clean and presentable</strong></li>
                <li><strong>Have company ID and vehicle permits ready</strong></li>
            </ul>
        </div>
        
        <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h4>📞 Emergency Contacts</h4>
            <p><strong>Operations Manager:</strong> [Operations Phone]</p>
            <p><strong>Customer Service:</strong> [Customer Service Phone]</p>
            <p><strong>Primary Guest Contact:</strong> {booking.customer_phone}</p>
        </div>
        
        <p style="margin-top: 20px; color: #666;">
            Please confirm receipt of this schedule and your availability for the excursion.
        </p>
        """
        
        frappe.sendmail(
            recipients=[guide.email],
            subject=subject,
            message=message,
            reference_doctype=booking.doctype,
            reference_name=booking.name
        )
        
        return {"status": "success", "message": "Pickup schedule sent to driver"}
        
    except Exception as e:
        frappe.log_error(f"Driver pickup schedule error: {str(e)}")
        return {"status": "error", "message": str(e)}

def generate_individual_pickup_schedule(booking):
    """Generate schedule for individual hotel pickups"""
    if not booking.guest_pickups:
        return "<p>No pickup schedule created yet.</p>"
    
    schedule_html = """
    <div style="margin: 20px 0;">
        <h3>🏨 Individual Hotel Pickup Schedule</h3>
        <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background-color: #f0f0f0; font-weight: bold;">
                <th style="padding: 10px;">Order</th>
                <th style="padding: 10px;">Time</th>
                <th style="padding: 10px;">Guest Name</th>
                <th style="padding: 10px;">Hotel/Location</th>
                <th style="padding: 10px;">Contact Phone</th>
                <th style="padding: 10px;">Address & Instructions</th>
            </tr>
    """
    
    for pickup in booking.guest_pickups:
        schedule_html += f"""
        <tr>
            <td style="padding: 8px; text-align: center; font-weight: bold; background: #e3f2fd;">#{pickup.pickup_order}</td>
            <td style="padding: 8px; font-weight: bold; color: #d32f2f;">{pickup.estimated_pickup_time}</td>
            <td style="padding: 8px;">{pickup.guest_name}</td>
            <td style="padding: 8px;">
                <strong>{pickup.pickup_location_name}</strong><br>
                <small style="color: #666;">{pickup.pickup_location_type}</small>
            </td>
            <td style="padding: 8px;">
                <strong>{pickup.contact_phone}</strong>
            </td>
            <td style="padding: 8px;">
                <strong>Address:</strong> {pickup.pickup_address}<br>
                {f'<strong>GPS:</strong> {pickup.gps_coordinates}<br>' if pickup.gps_coordinates else ''}
                {f'<strong>Landmark:</strong> {pickup.landmark}<br>' if pickup.landmark else ''}
                <strong>Instructions:</strong> {pickup.meeting_instructions or 'Meet at main entrance'}
                {f'<br><strong>Notes:</strong> {pickup.special_notes}' if pickup.special_notes else ''}
            </td>
        </tr>
        """
    
    schedule_html += """
        </table>
    </div>
    
    <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <h4>🚗 Pickup Process for Each Hotel:</h4>
        <ol>
            <li><strong>Call guest 5 minutes before arrival</strong> using the contact number provided</li>
            <li><strong>Park safely</strong> near the hotel main entrance (avoid blocking traffic)</li>
            <li><strong>Enter hotel lobby</strong> and ask reception to call the guest</li>
            <li><strong>Introduce yourself</strong> clearly: "I'm [Your Name] from [Company] here for [Guest Name]'s excursion"</li>
            <li><strong>Help with luggage</strong> if needed and escort guest to vehicle</li>
            <li><strong>Maximum 5 minutes per pickup</strong> - if guest not ready, contact operations</li>
            <li><strong>Confirm identity</strong> by asking for booking number or excursion name</li>
        </ol>
    </div>
    """
    
    return schedule_html

def generate_central_pickup_schedule(booking):
    """Generate schedule for central pickup point"""
    schedule_html = f"""
    <div style="margin: 20px 0;">
        <h3>📍 Central Pickup Point</h3>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <table style="width: 100%;">
                <tr><td><strong>Pickup Location:</strong></td><td>{booking.pickup_location}</td></tr>
                <tr><td><strong>Pickup Time:</strong></td><td style="font-size: 18px; color: #d32f2f;"><strong>{booking.pickup_time}</strong></td></tr>
                <tr><td><strong>Total Guests:</strong></td><td>{booking.total_guests}</td></tr>
                <tr><td><strong>Primary Contact:</strong></td><td>{booking.customer_phone}</td></tr>
            </table>
        </div>
    </div>
    
    <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <h4>🚗 Central Pickup Process:</h4>
        <ol>
            <li><strong>Arrive 10 minutes early</strong> at the pickup location</li>
            <li><strong>Park in designated area</strong> and display company signage</li>
            <li><strong>Call primary contact</strong> ({booking.customer_phone}) upon arrival</li>
            <li><strong>Hold sign</strong> with excursion name or booking number</li>
            <li><strong>Check guest list</strong> as each person boards the vehicle</li>
            <li><strong>Confirm all guests</strong> are present before departure</li>
            <li><strong>Brief safety instructions</strong> once everyone is aboard</li>
        </ol>
    </div>
    """
    
    return schedule_html

def send_pickup_reminder_to_guests(excursion_booking):
    """Send pickup reminders to all guests the day before"""
    try:
        booking = frappe.get_doc("Excursion Booking", excursion_booking)
        
        # Check if it's the day before the excursion
        tomorrow = add_days(getdate(), 1)
        if getdate(booking.excursion_date) != tomorrow:
            return {"status": "error", "message": "Reminders should be sent the day before"}
        
        if booking.pickup_type == "Individual Hotel Pickups":
            return send_individual_pickup_reminders(booking)
        else:
            return send_central_pickup_reminder(booking)
            
    except Exception as e:
        frappe.log_error(f"Pickup reminder error: {str(e)}")
        return {"status": "error", "message": str(e)}

def send_individual_pickup_reminders(booking):
    """Send individual pickup reminders to each guest"""
    sent_count = 0
    
    for pickup in booking.guest_pickups:
        if pickup.contact_phone:
            # Get guest email if available
            guest_email = get_guest_email_by_name(booking, pickup.guest_name)
            
            if guest_email:
                try:
                    subject = f"Pickup Reminder - Tomorrow - {booking.excursion_package}"
                    
                    message = f"""
                    <h3>Excursion Pickup Reminder</h3>
                    <p>Dear {pickup.guest_name},</p>
                    
                    <p>This is a reminder about your excursion pickup tomorrow:</p>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h4>Your Pickup Details</h4>
                        <table style="width: 100%;">
                            <tr><td><strong>Excursion:</strong></td><td>{booking.excursion_package}</td></tr>
                            <tr><td><strong>Date:</strong></td><td>{booking.excursion_date}</td></tr>
                            <tr><td><strong>Pickup Time:</strong></td><td style="font-size: 18px; color: #d32f2f;"><strong>{pickup.estimated_pickup_time}</strong></td></tr>
                            <tr><td><strong>Pickup Location:</strong></td><td>{pickup.pickup_location_name}</td></tr>
                            <tr><td><strong>Your Pickup Order:</strong></td><td>#{pickup.pickup_order}</td></tr>
                        </table>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h4>📋 Tomorrow's Checklist</h4>
                        <ul>
                            <li>✅ Be ready 5 minutes before pickup time</li>
                            <li>✅ Keep your phone on - driver will call you</li>
                            <li>✅ Wait in hotel lobby/reception area</li>
                            <li>✅ Bring water bottle and sun protection</li>
                            <li>✅ Have comfortable walking shoes</li>
                            <li>✅ Bring camera for amazing photos</li>
                        </ul>
                    </div>
                    
                    <p><strong>Meeting Instructions:</strong><br>
                    {pickup.meeting_instructions or 'Meet at hotel main lobby/reception'}</p>
                    
                    <p>Looking forward to an amazing excursion with you!</p>
                    """
                    
                    frappe.sendmail(
                        recipients=[guest_email],
                        subject=subject,
                        message=message,
                        reference_doctype=booking.doctype,
                        reference_name=booking.name
                    )
                    
                    sent_count += 1
                    
                except Exception as e:
                    frappe.log_error(f"Individual pickup reminder error for {pickup.guest_name}: {str(e)}")
    
    return {
        "status": "success",
        "message": f"Pickup reminders sent to {sent_count} guests"
    }

def get_guest_email_by_name(booking, guest_name):
    """Get guest email by name from booking party"""
    if not booking.booking_party:
        return None
    
    try:
        booking_party = frappe.get_doc("Booking Party", booking.booking_party)
        
        # Check primary guest
        if booking_party.primary_guest:
            guest = frappe.get_doc("Safari Guest", booking_party.primary_guest)
            if guest.guest_name == guest_name:
                return guest.email
        
        # Check other guests
        for guest_row in booking_party.guests or []:
            guest = frappe.get_doc("Safari Guest", guest_row.guest)
            if guest.guest_name == guest_name:
                return guest.email
        
        # Fallback to customer email
        return booking.customer_email
        
    except Exception as e:
        frappe.log_error(f"Guest email lookup error: {str(e)}")
        return booking.customer_email

@frappe.whitelist()
def send_driver_pickup_schedule_now(excursion_booking):
    """Whitelisted method to send pickup schedule to driver"""
    return send_driver_pickup_schedule(excursion_booking)

@frappe.whitelist()
def send_pickup_reminders_now(excursion_booking):
    """Whitelisted method to send pickup reminders"""
    return send_pickup_reminder_to_guests(excursion_booking)