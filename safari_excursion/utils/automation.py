# ~/frappe-bench/apps/safari_excursion/safari_excursion/utils/automation.py

import frappe
from frappe import _
from frappe.utils import getdate, add_days, now_datetime, get_datetime, add_to_date
from safari_excursion.utils.transport_integration import ExcursionTransportAutomation

def send_pre_excursion_reminders():
    """Send reminders to customers and guides before excursions"""
    try:
        ExcursionTransportAutomation.send_pre_excursion_reminders()
        frappe.logger().info("Pre-excursion reminders sent successfully")
    except Exception as e:
        frappe.log_error(f"Pre-excursion reminder error: {str(e)}")

def update_excursion_status():
    """Update excursion status based on current time and progress"""
    try:
        ExcursionTransportAutomation.update_excursion_status()
        frappe.logger().info("Excursion status updated successfully")
    except Exception as e:
        frappe.log_error(f"Excursion status update error: {str(e)}")

def daily_excursion_summary():
    """Send daily summary of excursions to managers"""
    try:
        today = getdate()
        
        # Get today's excursion statistics
        stats = get_daily_excursion_stats(today)
        
        # Get list of managers to notify
        managers = get_excursion_managers()
        
        if not managers:
            return
        
        # Generate summary report
        summary_message = generate_daily_summary_message(stats, today)
        
        # Send email to managers
        frappe.sendmail(
            recipients=[manager.email for manager in managers if manager.email],
            subject=f"Daily Excursion Summary - {today}",
            message=summary_message
        )
        
        frappe.logger().info(f"Daily excursion summary sent to {len(managers)} managers")
        
    except Exception as e:
        frappe.log_error(f"Daily summary error: {str(e)}")

def get_daily_excursion_stats(date):
    """Get daily excursion statistics"""
    stats = {
        "total_bookings": 0,
        "confirmed_bookings": 0,
        "in_progress": 0,
        "completed": 0,
        "cancelled": 0,
        "total_guests": 0,
        "total_revenue": 0,
        "guides_assigned": 0,
        "vehicles_assigned": 0
    }
    
    # Get all bookings for the date
    bookings = frappe.get_all(
        "Excursion Booking",
        filters={"excursion_date": date},
        fields=[
            "booking_status", "excursion_status", "total_guests", 
            "total_amount", "assigned_guide", "assigned_vehicle"
        ]
    )
    
    stats["total_bookings"] = len(bookings)
    
    for booking in bookings:
        if booking.booking_status == "Confirmed":
            stats["confirmed_bookings"] += 1
            stats["total_guests"] += booking.total_guests or 0
            stats["total_revenue"] += booking.total_amount or 0
            
            if booking.assigned_guide:
                stats["guides_assigned"] += 1
            if booking.assigned_vehicle:
                stats["vehicles_assigned"] += 1
        
        if booking.excursion_status == "In Progress":
            stats["in_progress"] += 1
        elif booking.excursion_status == "Completed":
            stats["completed"] += 1
        elif booking.booking_status == "Cancelled":
            stats["cancelled"] += 1
    
    return stats

def get_excursion_managers():
    """Get list of excursion managers"""
    managers = frappe.get_all(
        "User",
        filters={
            "enabled": 1,
            "name": ["in", frappe.get_roles_with_permission("Excursion Booking", "read")]
        },
        fields=["name", "email", "full_name"]
    )
    
    # Filter for managers specifically
    manager_roles = ["Safari Manager", "Excursion Manager", "System Manager"]
    excursion_managers = []
    
    for manager in managers:
        user_roles = frappe.get_roles(manager.name)
        if any(role in manager_roles for role in user_roles):
            excursion_managers.append(manager)
    
    return excursion_managers

def generate_daily_summary_message(stats, date):
    """Generate daily summary email message"""
    message = f"""
    <h3>Daily Excursion Summary - {date}</h3>
    
    <table border="1" style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <tr style="background-color: #f0f0f0;">
            <td style="padding: 10px;"><strong>Metric</strong></td>
            <td style="padding: 10px;"><strong>Count</strong></td>
        </tr>
        <tr>
            <td style="padding: 8px;">Total Bookings</td>
            <td style="padding: 8px;">{stats['total_bookings']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;">Confirmed Bookings</td>
            <td style="padding: 8px;">{stats['confirmed_bookings']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;">In Progress</td>
            <td style="padding: 8px;">{stats['in_progress']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;">Completed</td>
            <td style="padding: 8px;">{stats['completed']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;">Cancelled</td>
            <td style="padding: 8px;">{stats['cancelled']}</td>
        </tr>
        <tr style="background-color: #f9f9f9;">
            <td style="padding: 8px;"><strong>Total Guests</strong></td>
            <td style="padding: 8px;"><strong>{stats['total_guests']}</strong></td>
        </tr>
        <tr style="background-color: #f9f9f9;">
            <td style="padding: 8px;"><strong>Total Revenue</strong></td>
            <td style="padding: 8px;"><strong>${stats['total_revenue']:,.2f}</strong></td>
        </tr>
        <tr>
            <td style="padding: 8px;">Guides Assigned</td>
            <td style="padding: 8px;">{stats['guides_assigned']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;">Vehicles Assigned</td>
            <td style="padding: 8px;">{stats['vehicles_assigned']}</td>
        </tr>
    </table>
    
    <h4>Action Items:</h4>
    <ul>
    """
    
    # Add action items based on statistics
    if stats['confirmed_bookings'] > stats['guides_assigned']:
        unassigned_guides = stats['confirmed_bookings'] - stats['guides_assigned']
        message += f"<li>⚠️ {unassigned_guides} bookings need guide assignment</li>"
    
    if stats['confirmed_bookings'] > stats['vehicles_assigned']:
        unassigned_vehicles = stats['confirmed_bookings'] - stats['vehicles_assigned']
        message += f"<li>⚠️ {unassigned_vehicles} bookings need vehicle assignment</li>"
    
    if stats['in_progress'] > 0:
        message += f"<li>📍 {stats['in_progress']} excursions currently in progress</li>"
    
    if stats['cancelled'] > 0:
        message += f"<li>❌ {stats['cancelled']} cancellations today - review refund process</li>"
    
    message += """
    </ul>
    
    <p>Access the full dashboard: <a href="{}/app/safari-excursion">Safari Excursion Workspace</a></p>
    """.format(frappe.utils.get_url())
    
    return message

def vehicle_availability_check():
    """Check vehicle availability for upcoming excursions"""
    try:
        tomorrow = add_days(getdate(), 1)
        
        # Get tomorrow's confirmed bookings without vehicles
        unassigned_bookings = frappe.get_all(
            "Excursion Booking",
            filters={
                "excursion_date": tomorrow,
                "booking_status": "Confirmed",
                "assigned_vehicle": ["is", "not set"]
            },
            fields=["name", "booking_number", "excursion_package", "total_guests"]
        )
        
        if not unassigned_bookings:
            return
        
        # Get available vehicles
        available_vehicles = get_available_vehicles_for_date(tomorrow)
        
        # Send notification to managers
        managers = get_excursion_managers()
        if managers:
            send_vehicle_assignment_notification(unassigned_bookings, available_vehicles, managers, tomorrow)
        
        frappe.logger().info(f"Vehicle availability check completed for {tomorrow}")
        
    except Exception as e:
        frappe.log_error(f"Vehicle availability check error: {str(e)}")

def get_available_vehicles_for_date(date):
    """Get available vehicles for a specific date"""
    # Get all vehicles
    all_vehicles = frappe.get_all(
        "Vehicle",
        filters={"status": "Available"},
        fields=["name", "vehicle_type", "capacity", "license_plate"]
    )
    
    # Get vehicles already assigned for the date
    assigned_vehicles = frappe.get_all(
        "Excursion Booking",
        filters={
            "excursion_date": date,
            "booking_status": "Confirmed",
            "assigned_vehicle": ["is", "set"]
        },
        fields=["assigned_vehicle"]
    )
    
    assigned_vehicle_names = [v.assigned_vehicle for v in assigned_vehicles]
    
    # Filter available vehicles
    available_vehicles = [v for v in all_vehicles if v.name not in assigned_vehicle_names]
    
    return available_vehicles

def send_vehicle_assignment_notification(unassigned_bookings, available_vehicles, managers, date):
    """Send vehicle assignment notification to managers"""
    message = f"""
    <h3>Vehicle Assignment Required - {date}</h3>
    
    <p>The following excursion bookings need vehicle assignment:</p>
    
    <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
        <tr style="background-color: #f0f0f0;">
            <td style="padding: 8px;"><strong>Booking</strong></td>
            <td style="padding: 8px;"><strong>Package</strong></td>
            <td style="padding: 8px;"><strong>Guests</strong></td>
        </tr>
    """
    
    for booking in unassigned_bookings:
        message += f"""
        <tr>
            <td style="padding: 6px;">{booking.booking_number}</td>
            <td style="padding: 6px;">{booking.excursion_package}</td>
            <td style="padding: 6px;">{booking.total_guests}</td>
        </tr>
        """
    
    message += "</table>"
    
    if available_vehicles:
        message += """
        <h4>Available Vehicles:</h4>
        <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background-color: #f0f0f0;">
                <td style="padding: 8px;"><strong>Vehicle</strong></td>
                <td style="padding: 8px;"><strong>Type</strong></td>
                <td style="padding: 8px;"><strong>Capacity</strong></td>
            </tr>
        """
        
        for vehicle in available_vehicles:
            message += f"""
            <tr>
                <td style="padding: 6px;">{vehicle.license_plate}</td>
                <td style="padding: 6px;">{vehicle.vehicle_type}</td>
                <td style="padding: 6px;">{vehicle.capacity}</td>
            </tr>
            """
        
        message += "</table>"
    else:
        message += "<p><strong>⚠️ No vehicles available for this date!</strong></p>"
    
    message += f"""
    <p>Please assign vehicles promptly to ensure smooth operations.</p>
    <p>Access the assignment interface: <a href="{frappe.utils.get_url()}/app/safari-excursion">Safari Excursion Workspace</a></p>
    """
    
    frappe.sendmail(
        recipients=[manager.email for manager in managers if manager.email],
        subject=f"Vehicle Assignment Required - {date}",
        message=message
    )

def weekly_excursion_report():
    """Generate weekly excursion performance report"""
    try:
        # Get date range for the past week
        end_date = getdate()
        start_date = add_days(end_date, -7)
        
        # Generate report data
        report_data = generate_weekly_report_data(start_date, end_date)
        
        # Send to managers
        managers = get_excursion_managers()
        if managers:
            send_weekly_report(report_data, start_date, end_date, managers)
        
        frappe.logger().info(f"Weekly excursion report generated for {start_date} to {end_date}")
        
    except Exception as e:
        frappe.log_error(f"Weekly report error: {str(e)}")

def generate_weekly_report_data(start_date, end_date):
    """Generate weekly report data"""
    data = {
        "summary": {},
        "top_packages": [],
        "guide_performance": [],
        "daily_breakdown": []
    }
    
    # Get summary statistics
    bookings = frappe.get_all(
        "Excursion Booking",
        filters={
            "excursion_date": ["between", [start_date, end_date]]
        },
        fields=[
            "excursion_date", "booking_status", "excursion_status", 
            "total_guests", "total_amount", "excursion_package", "assigned_guide"
        ]
    )
    
    data["summary"] = {
        "total_bookings": len(bookings),
        "confirmed_bookings": len([b for b in bookings if b.booking_status == "Confirmed"]),
        "completed_excursions": len([b for b in bookings if b.excursion_status == "Completed"]),
        "total_guests": sum(b.total_guests or 0 for b in bookings if b.booking_status != "Cancelled"),
        "total_revenue": sum(b.total_amount or 0 for b in bookings if b.booking_status != "Cancelled"),
        "cancellation_rate": len([b for b in bookings if b.booking_status == "Cancelled"]) / len(bookings) * 100 if bookings else 0
    }
    
    return data

def send_weekly_report(report_data, start_date, end_date, managers):
    """Send weekly performance report"""
    summary = report_data["summary"]
    
    message = f"""
    <h3>Weekly Excursion Performance Report</h3>
    <p><strong>Period:</strong> {start_date} to {end_date}</p>
    
    <h4>Key Metrics:</h4>
    <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
        <tr>
            <td style="padding: 8px;"><strong>Total Bookings</strong></td>
            <td style="padding: 8px;">{summary['total_bookings']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;"><strong>Confirmed Bookings</strong></td>
            <td style="padding: 8px;">{summary['confirmed_bookings']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;"><strong>Completed Excursions</strong></td>
            <td style="padding: 8px;">{summary['completed_excursions']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;"><strong>Total Guests</strong></td>
            <td style="padding: 8px;">{summary['total_guests']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;"><strong>Total Revenue</strong></td>
            <td style="padding: 8px;">${summary['total_revenue']:,.2f}</td>
        </tr>
        <tr>
            <td style="padding: 8px;"><strong>Cancellation Rate</strong></td>
            <td style="padding: 8px;">{summary['cancellation_rate']:.1f}%</td>
        </tr>
    </table>
    
    <p>For detailed analysis and trends, visit the <a href="{base_url}/app/safari-excursion">Safari Excursion Dashboard</a></p>
    """.format(base_url=frappe.utils.get_url())
    
    frappe.sendmail(
        recipients=[manager.email for manager in managers if manager.email],
        subject=f"Weekly Excursion Report - {start_date} to {end_date}",
        message=message
    )

@frappe.whitelist()
def get_excursion_dashboard_data():
    """Get dashboard data for excursion management"""
    try:
        today = getdate()
        
        # Today's statistics
        today_stats = get_daily_excursion_stats(today)
        
        # Upcoming excursions (next 7 days)
        upcoming_excursions = frappe.get_all(
            "Excursion Booking",
            filters={
                "excursion_date": ["between", [today, add_days(today, 7)]],
                "booking_status": "Confirmed"
            },
            fields=[
                "name", "booking_number", "excursion_date", "departure_time",
                "excursion_package", "total_guests", "assigned_guide", "assigned_vehicle"
            ],
            order_by="excursion_date, departure_time"
        )
        
        # Unassigned bookings
        unassigned_guides = len([e for e in upcoming_excursions if not e.assigned_guide])
        unassigned_vehicles = len([e for e in upcoming_excursions if not e.assigned_vehicle])
        
        # Popular packages (this month)
        month_start = today.replace(day=1)
        popular_packages = frappe.db.sql("""
            SELECT excursion_package, COUNT(*) as booking_count, SUM(total_amount) as revenue
            FROM `tabExcursion Booking`
            WHERE excursion_date >= %s AND booking_status != 'Cancelled'
            GROUP BY excursion_package
            ORDER BY booking_count DESC
            LIMIT 5
        """, [month_start], as_dict=True)
        
        return {
            "status": "success",
            "data": {
                "today_stats": today_stats,
                "upcoming_excursions": upcoming_excursions,
                "unassigned_guides": unassigned_guides,
                "unassigned_vehicles": unassigned_vehicles,
                "popular_packages": popular_packages
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Dashboard data error: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def auto_assign_resources():
    """Automatically assign guides and vehicles based on availability"""
    try:
        tomorrow = add_days(getdate(), 1)
        
        # Get unassigned bookings for tomorrow
        unassigned_bookings = frappe.get_all(
            "Excursion Booking",
            filters={
                "excursion_date": tomorrow,
                "booking_status": "Confirmed",
                "docstatus": 1
            },
            fields=["name", "total_guests", "departure_time", "excursion_package"]
        )
        
        assignments_made = 0
        
        for booking_data in unassigned_bookings:
            booking = frappe.get_doc("Excursion Booking", booking_data.name)
            
            # Auto-assign guide if not assigned
            if not booking.assigned_guide:
                available_guide = find_available_guide(tomorrow, booking.departure_time)
                if available_guide:
                    booking.assigned_guide = available_guide
                    assignments_made += 1
            
            # Auto-assign vehicle if not assigned
            if not booking.assigned_vehicle:
                available_vehicle = find_available_vehicle(tomorrow, booking.total_guests)
                if available_vehicle:
                    booking.assigned_vehicle = available_vehicle
                    assignments_made += 1
            
            if booking.assigned_guide or booking.assigned_vehicle:
                booking.save()
        
        return {
            "status": "success",
            "message": f"Auto-assignment completed. {assignments_made} assignments made.",
            "assignments_made": assignments_made
        }
        
    except Exception as e:
        frappe.log_error(f"Auto-assignment error: {str(e)}")
        return {"status": "error", "message": str(e)}

def find_available_guide(date, departure_time):
    """Find an available guide for the given date and time"""
    # Get all active guides
    guides = frappe.get_all(
        "Safari Guide",
        filters={"is_active": 1, "availability_status": "Available"},
        fields=["name"]
    )
    
    for guide in guides:
        # Check if guide has any conflicting assignments
        conflicts = frappe.db.count("Excursion Booking", {
            "excursion_date": date,
            "assigned_guide": guide.name,
            "booking_status": ["in", ["Confirmed", "In Progress"]]
        })
        
        if conflicts == 0:
            return guide.name
    
    return None

def find_available_vehicle(date, guest_count):
    """Find an available vehicle with sufficient capacity"""
    # Get vehicles with adequate capacity
    vehicles = frappe.get_all(
        "Vehicle",
        filters={
            "status": "Available",
            "capacity": [">=", guest_count]
        },
        fields=["name", "capacity"],
        order_by="capacity"  # Prefer smaller vehicles that still fit
    )
    
    for vehicle in vehicles:
        # Check if vehicle has any conflicting assignments
        conflicts = frappe.db.count("Excursion Booking", {
            "excursion_date": date,
            "assigned_vehicle": vehicle.name,
            "booking_status": ["in", ["Confirmed", "In Progress"]]
        })
        
        if conflicts == 0:
            return vehicle.name
    
    return None

@frappe.whitelist()
def send_mass_reminders():
    """Send reminders to all customers with excursions tomorrow"""
    try:
        tomorrow = add_days(getdate(), 1)
        
        bookings = frappe.get_all(
            "Excursion Booking",
            filters={
                "excursion_date": tomorrow,
                "booking_status": "Confirmed",
                "reminder_sent": 0,
                "customer_email": ["is", "set"]
            },
            fields=["name"]
        )
        
        sent_count = 0
        for booking_data in bookings:
            try:
                booking = frappe.get_doc("Excursion Booking", booking_data.name)
                booking.send_reminder_notification()
                sent_count += 1
            except Exception as e:
                frappe.log_error(f"Individual reminder error for {booking_data.name}: {str(e)}")
                continue
        
        return {
            "status": "success",
            "message": f"Reminders sent to {sent_count} customers",
            "sent_count": sent_count
        }
        
    except Exception as e:
        frappe.log_error(f"Mass reminder error: {str(e)}")
        return {"status": "error", "message": str(e)}

def cleanup_old_data():
    """Clean up old excursion data (run monthly)"""
    try:
        # Delete old excursion operations (older than 1 year)
        cutoff_date = add_days(getdate(), -365)
        
        old_operations = frappe.get_all(
            "Excursion Operation",
            filters={"operation_date": ["<", cutoff_date]},
            fields=["name"]
        )
        
        for operation in old_operations:
            frappe.delete_doc("Excursion Operation", operation.name, force=True)
        
        # Archive old bookings (older than 2 years) - mark as archived instead of deleting
        archive_date = add_days(getdate(), -730)
        
        frappe.db.sql("""
            UPDATE `tabExcursion Booking`
            SET booking_status = 'Archived'
            WHERE excursion_date < %s AND booking_status != 'Archived'
        """, [archive_date])
        
        frappe.db.commit()
        frappe.logger().info(f"Data cleanup completed. Deleted {len(old_operations)} old operations")
        
    except Exception as e:
        frappe.log_error(f"Data cleanup error: {str(e)}")

# Scheduled task functions that are called from hooks.py
def hourly_excursion_updates():
    """Hourly automation tasks"""
    send_pre_excursion_reminders()
    update_excursion_status()

def daily_excursion_tasks():
    """Daily automation tasks"""
    daily_excursion_summary()
    vehicle_availability_check()

def weekly_excursion_tasks():
    """Weekly automation tasks"""
    weekly_excursion_report()

def monthly_excursion_tasks():
    """Monthly automation tasks"""
    cleanup_old_data()
