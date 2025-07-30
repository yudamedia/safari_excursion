# ~/frappe-bench/apps/safari_excursion/safari_excursion/utils/notifications.py

import frappe
from frappe import _

def send_booking_confirmation(doc, method):
    """Send booking confirmation email to customer"""
    if doc.doctype != "Excursion Booking":
        return
    
    try:
        if doc.customer_email:
            subject = f"Excursion Booking Confirmed - {doc.booking_number}"
            
            message = f"""
            <h3>Excursion Booking Confirmation</h3>
            <p>Dear {doc.customer_name},</p>
            <p>Your excursion booking has been confirmed!</p>
            
            <table border="1" style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr><td><strong>Booking Number:</strong></td><td>{doc.booking_number}</td></tr>
                <tr><td><strong>Excursion:</strong></td><td>{doc.excursion_package}</td></tr>
                <tr><td><strong>Date:</strong></td><td>{doc.excursion_date}</td></tr>
                <tr><td><strong>Departure Time:</strong></td><td>{doc.departure_time}</td></tr>
                <tr><td><strong>Total Guests:</strong></td><td>{doc.total_guests}</td></tr>
                <tr><td><strong>Total Amount:</strong></td><td>${doc.total_amount}</td></tr>
            </table>
            
            {f'<p><strong>Pickup Location:</strong> {doc.pickup_location}</p>' if doc.pickup_location else ''}
            {f'<p><strong>Pickup Time:</strong> {doc.pickup_time}</p>' if doc.pickup_time else ''}
            
            <p>We will send you a reminder the day before your excursion.</p>
            <p>Have a wonderful experience with us!</p>
            """
            
            frappe.sendmail(
                recipients=[doc.customer_email],
                subject=subject,
                message=message,
                reference_doctype=doc.doctype,
                reference_name=doc.name
            )
            
            # Mark confirmation as sent
            doc.db_set("confirmation_sent", 1, update_modified=False)
            
    except Exception as e:
        frappe.log_error(f"Booking confirmation email error: {str(e)}")

def send_operation_start_notification(doc, method):
    """Send notification when excursion operation starts"""
    if doc.doctype != "Excursion Operation":
        return
    
    try:
        # Get the related excursion booking
        if doc.excursion_booking:
            booking = frappe.get_doc("Excursion Booking", doc.excursion_booking)
            
            # Send notification to customer if operation is starting
            if doc.operation_status == "In Progress" and booking.customer_email:
                subject = f"Your Excursion Has Started - {booking.booking_number}"
                
                message = f"""
                <h3>Excursion Started</h3>
                <p>Dear {booking.customer_name},</p>
                <p>Your excursion has begun! We hope you have a wonderful experience.</p>
                
                <p><strong>Excursion:</strong> {booking.excursion_package}</p>
                <p><strong>Guide:</strong> {doc.assigned_guide or 'Assigned guide'}</p>
                <p><strong>Expected Return:</strong> {booking.estimated_return_time or 'As scheduled'}</p>
                
                <p>Enjoy your adventure!</p>
                """
                
                frappe.sendmail(
                    recipients=[booking.customer_email],
                    subject=subject,
                    message=message,
                    reference_doctype=booking.doctype,
                    reference_name=booking.name
                )
                
    except Exception as e:
        frappe.log_error(f"Operation start notification error: {str(e)}")

def send_guide_assignment_notification(guide_name, excursion_booking):
    """Send notification to guide when assigned to excursion"""
    try:
        guide = frappe.get_doc("Safari Guide", guide_name)
        booking = frappe.get_doc("Excursion Booking", excursion_booking)
        
        if not guide.email:
            return
        
        subject = f"New Excursion Assignment - {booking.booking_number}"
        
        message = f"""
        <h3>New Excursion Assignment</h3>
        <p>You have been assigned to guide the following excursion:</p>
        
        <table border="1" style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr><td><strong>Booking:</strong></td><td>{booking.booking_number}</td></tr>
            <tr><td><strong>Excursion:</strong></td><td>{booking.excursion_package}</td></tr>
            <tr><td><strong>Date:</strong></td><td>{booking.excursion_date}</td></tr>
            <tr><td><strong>Departure Time:</strong></td><td>{booking.departure_time}</td></tr>
            <tr><td><strong>Guests:</strong></td><td>{booking.total_guests} ({booking.adult_count} adults, {booking.child_count or 0} children)</td></tr>
            <tr><td><strong>Customer:</strong></td><td>{booking.customer_name}</td></tr>
            <tr><td><strong>Contact:</strong></td><td>{booking.customer_phone}</td></tr>
        </table>
        
        {f'<p><strong>Pickup Location:</strong> {booking.pickup_location}</p>' if booking.pickup_location else ''}
        {f'<p><strong>Pickup Time:</strong> {booking.pickup_time}</p>' if booking.pickup_time else ''}
        {f'<p><strong>Special Requirements:</strong> {booking.special_requirements}</p>' if booking.special_requirements else ''}
        
        <p>Please confirm your availability and review the excursion details.</p>
        """
        
        frappe.sendmail(
            recipients=[guide.email],
            subject=subject,
            message=message,
            reference_doctype=booking.doctype,
            reference_name=booking.name
        )
        
    except Exception as e:
        frappe.log_error(f"Guide assignment notification error: {str(e)}")

def send_vehicle_assignment_notification(vehicle_name, excursion_booking):
    """Send notification when vehicle is assigned to excursion"""
    try:
        vehicle = frappe.get_doc("Vehicle", vehicle_name)
        booking = frappe.get_doc("Excursion Booking", excursion_booking)
        
        # If vehicle has a driver assigned, notify them
        if vehicle.driver_assigned:
            driver_email = frappe.db.get_value("Safari Guide", vehicle.driver_assigned, "email")
            
            if driver_email:
                subject = f"Vehicle Assignment - Excursion {booking.booking_number}"
                
                message = f"""
                <h3>Vehicle Assignment Notification</h3>
                <p>Your vehicle {vehicle.license_plate} has been assigned to an excursion:</p>
                
                <table border="1" style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr><td><strong>Booking:</strong></td><td>{booking.booking_number}</td></tr>
                    <tr><td><strong>Date:</strong></td><td>{booking.excursion_date}</td></tr>
                    <tr><td><strong>Departure Time:</strong></td><td>{booking.departure_time}</td></tr>
                    <tr><td><strong>Customer:</strong></td><td>{booking.customer_name}</td></tr>
                    <tr><td><strong>Passengers:</strong></td><td>{booking.total_guests}</td></tr>
                </table>
                
                <p>Please ensure the vehicle is ready and available for the scheduled time.</p>
                """
                
                frappe.sendmail(
                    recipients=[driver_email],
                    subject=subject,
                    message=message,
                    reference_doctype=booking.doctype,
                    reference_name=booking.name
                )
                
    except Exception as e:
        frappe.log_error(f"Vehicle assignment notification error: {str(e)}")

@frappe.whitelist()
def send_excursion_reminder(excursion_booking):
    """Send reminder notification for upcoming excursion"""
    try:
        booking = frappe.get_doc("Excursion Booking", excursion_booking)
        
        if not booking.customer_email:
            return {"status": "error", "message": "Customer email not available"}
        
        subject = f"Excursion Reminder - Tomorrow - {booking.booking_number}"
        
        message = f"""
        <h3>Excursion Reminder</h3>
        <p>Dear {booking.customer_name},</p>
        <p>This is a reminder about your excursion tomorrow:</p>
        
        <table border="1" style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr><td><strong>Excursion:</strong></td><td>{booking.excursion_package}</td></tr>
            <tr><td><strong>Date:</strong></td><td>{booking.excursion_date}</td></tr>
            <tr><td><strong>Departure Time:</strong></td><td>{booking.departure_time}</td></tr>
            <tr><td><strong>Total Guests:</strong></td><td>{booking.total_guests}</td></tr>
        </table>
        
        {f'<p><strong>Pickup Time:</strong> {booking.pickup_time}</p>' if booking.pickup_time else ''}
        {f'<p><strong>Pickup Location:</strong> {booking.pickup_location}</p>' if booking.pickup_location else ''}
        {f'<p><strong>Guide:</strong> {booking.get_guide_name()}</p>' if booking.assigned_guide else ''}
        
        <p><strong>What to bring:</strong></p>
        <ul>
            <li>Comfortable walking shoes</li>
            <li>Sun protection (hat, sunscreen)</li>
            <li>Camera</li>
            <li>Water bottle</li>
            {f'<li>{booking.special_requirements}</li>' if booking.special_requirements else ''}
        </ul>
        
        <p>Please be ready 10 minutes before pickup time.</p>
        <p>Looking forward to providing you with an amazing experience!</p>
        """
        
        frappe.sendmail(
            recipients=[booking.customer_email],
            subject=subject,
            message=message,
            reference_doctype=booking.doctype,
            reference_name=booking.name
        )
        
        # Mark reminder as sent
        booking.db_set("reminder_sent", 1)
        
        return {"status": "success", "message": "Reminder sent successfully"}
        
    except Exception as e:
        frappe.log_error(f"Excursion reminder error: {str(e)}")
        return {"status": "error", "message": str(e)}