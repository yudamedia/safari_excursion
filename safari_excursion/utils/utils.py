# ~/frappe-bench/apps/safari_excursion/safari_excursion/utils/utils.py

import frappe
from frappe import _

def has_app_permission():
    """Check if user has permission to access the Safari Excursion app
    
    Returns:
        bool: True if user has access, False otherwise
    """
    # Users with these roles can access the app
    authorized_roles = [
        "Safari Manager", 
        "Safari User", 
        "Safari Guide", 
        "Excursion Manager",
        "Excursion Guide",
        "System Manager"
    ]
    
    # Get current user roles
    user_roles = frappe.get_roles(frappe.session.user)
    
    # Check for role intersection
    return any(role in authorized_roles for role in user_roles)

def get_excursion_booking_permissions(doc):
    """Get permission query conditions for Excursion Booking"""
    user_roles = frappe.get_roles()
    
    # Managers can see all bookings
    if any(role in ["Safari Manager", "Excursion Manager", "System Manager"] for role in user_roles):
        return ""
    
    # Guides can only see their assigned bookings
    if "Excursion Guide" in user_roles:
        guide_name = frappe.db.get_value("Safari Guide", {"user": frappe.session.user}, "name")
        if guide_name:
            return f"`tabExcursion Booking`.assigned_guide = '{guide_name}'"
    
    # Regular users can see bookings they created or are assigned to
    return f"`tabExcursion Booking`.owner = '{frappe.session.user}'"

def has_excursion_booking_permission(doc, user=None):
    """Check if user has permission for specific Excursion Booking"""
    if not user:
        user = frappe.session.user
    
    user_roles = frappe.get_roles(user)
    
    # Managers have full access
    if any(role in ["Safari Manager", "Excursion Manager", "System Manager"] for role in user_roles):
        return True
    
    # Guides can access their assigned bookings
    if "Excursion Guide" in user_roles:
        guide_name = frappe.db.get_value("Safari Guide", {"user": user}, "name")
        if guide_name and doc.assigned_guide == guide_name:
            return True
    
    # Users can access bookings they created
    if doc.owner == user:
        return True
    
    return False

def get_available_guides_for_date(date, departure_time=None):
    """Get list of available guides for a specific date and time
    
    Args:
        date (str): Date in YYYY-MM-DD format
        departure_time (str, optional): Time in HH:MM:SS format
        
    Returns:
        list: List of available guides with their details
    """
    # Get all active guides
    guides = frappe.get_all(
        "Safari Guide",
        filters={
            "is_active": 1,
            "availability_status": "Available"
        },
        fields=[
            "name", "guide_name", "email", "phone", "rating",
            "specialization", "languages_spoken"
        ]
    )
    
    # Filter out guides with conflicting assignments
    available_guides = []
    
    for guide in guides:
        # Check for conflicting excursion assignments
        conflicts = frappe.db.count("Excursion Booking", {
            "excursion_date": date,
            "assigned_guide": guide.name,
            "booking_status": ["in", ["Confirmed", "In Progress"]]
        })
        
        if conflicts == 0:
            # Check for conflicting safari assignments (from safari_operations)
            safari_conflicts = frappe.db.count("Safari Booking", {
                "start_date": ["<=", date],
                "end_date": [">=", date],
                "guide": guide.name,
                "status": ["in", ["Confirmed", "In Progress"]]
            }) if frappe.db.exists("DocType", "Safari Booking") else 0
            
            if safari_conflicts == 0:
                available_guides.append(guide)
    
    return available_guides

def get_available_vehicles_for_date(date, min_capacity=1):
    """Get list of available vehicles for a specific date
    
    Args:
        date (str): Date in YYYY-MM-DD format
        min_capacity (int): Minimum required capacity
        
    Returns:
        list: List of available vehicles with their details
    """
    # Get all available vehicles with adequate capacity
    vehicles = frappe.get_all(
        "Vehicle",
        filters={
            "status": "Available",
            "capacity": [">=", min_capacity]
        },
        fields=[
            "name", "vehicle_type", "capacity", "license_plate",
            "fuel_type", "driver_assigned"
        ],
        order_by="capacity"
    )
    
    # Filter out vehicles with conflicting assignments
    available_vehicles = []
    
    for vehicle in vehicles:
        # Check for conflicting excursion assignments
        conflicts = frappe.db.count("Excursion Booking", {
            "excursion_date": date,
            "assigned_vehicle": vehicle.name,
            "booking_status": ["in", ["Confirmed", "In Progress"]]
        })
        
        if conflicts == 0:
            # Check for conflicting transport bookings
            transport_conflicts = frappe.db.count("Transport Booking", {
                "pickup_date": date,
                "vehicle": vehicle.name,
                "status": ["in", ["Confirmed", "In Progress"]]
            }) if frappe.db.exists("DocType", "Transport Booking") else 0
            
            if transport_conflicts == 0:
                available_vehicles.append(vehicle)
    
    return available_vehicles

def get_popular_excursion_packages(limit=10, days_back=30):
    """Get most popular excursion packages based on bookings
    
    Args:
        limit (int): Number of packages to return
        days_back (int): Number of days to look back
        
    Returns:
        list: List of popular packages with booking statistics
    """
    from frappe.utils import add_days, getdate
    
    start_date = add_days(getdate(), -days_back)
    
    popular_packages = frappe.db.sql("""
        SELECT 
            ep.name,
            ep.package_name,
            ep.excursion_category,
            ep.duration_hours,
            ep.base_price_adult,
            COUNT(eb.name) as booking_count,
            SUM(eb.total_guests) as total_guests,
            SUM(eb.total_amount) as total_revenue,
            AVG(eb.total_amount) as avg_booking_value
        FROM `tabExcursion Package` ep
        LEFT JOIN `tabExcursion Booking` eb ON ep.name = eb.excursion_package
            AND eb.excursion_date >= %s
            AND eb.booking_status != 'Cancelled'
        WHERE ep.package_status = 'Active'
        GROUP BY ep.name
        ORDER BY booking_count DESC, total_revenue DESC
        LIMIT %s
    """, [start_date, limit], as_dict=True)
    
    return popular_packages

def get_guide_performance_summary(guide_name, days_back=30):
    """Get performance summary for a specific guide
    
    Args:
        guide_name (str): Name of the guide
        days_back (int): Number of days to analyze
        
    Returns:
        dict: Guide performance statistics
    """
    from frappe.utils import add_days, getdate
    
    start_date = add_days(getdate(), -days_back)
    
    # Get guide's excursion statistics
    stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_excursions,
            SUM(eb.total_guests) as total_guests_guided,
            AVG(eo.guide_rating) as avg_rating,
            COUNT(CASE WHEN eb.excursion_status = 'Completed' THEN 1 END) as completed_excursions,
            COUNT(CASE WHEN eb.excursion_status = 'Cancelled' THEN 1 END) as cancelled_excursions
        FROM `tabExcursion Booking` eb
        LEFT JOIN `tabExcursion Operation` eo ON eb.name = eo.excursion_booking
        WHERE eb.assigned_guide = %s
            AND eb.excursion_date >= %s
    """, [guide_name, start_date], as_dict=True)
    
    if stats:
        performance = stats[0]
        # Calculate completion rate
        if performance.total_excursions > 0:
            performance["completion_rate"] = (performance.completed_excursions / performance.total_excursions) * 100
        else:
            performance["completion_rate"] = 0
            
        return performance
    
    return {
        "total_excursions": 0,
        "total_guests_guided": 0,
        "avg_rating": 0,
        "completed_excursions": 0,
        "cancelled_excursions": 0,
        "completion_rate": 0
    }

def calculate_excursion_profitability(excursion_booking):
    """Calculate profitability for an excursion booking
    
    Args:
        excursion_booking (str): Name of the excursion booking
        
    Returns:
        dict: Profitability analysis
    """
    booking = frappe.get_doc("Excursion Booking", excursion_booking)
    
    # Base costs
    costs = {
        "guide_cost": 0,
        "vehicle_cost": 0,
        "fuel_cost": 0,
        "equipment_cost": 0,
        "park_fees": 0,
        "other_costs": 0,
        "total_costs": 0
    }
    
    # Calculate guide cost (assume daily rate or percentage)
    if booking.assigned_guide:
        # This could be enhanced to get actual guide rates
        costs["guide_cost"] = booking.duration_hours * 20  # $20 per hour example
    
    # Calculate vehicle cost
    if booking.assigned_vehicle:
        # This could be enhanced to get actual vehicle rates
        costs["vehicle_cost"] = booking.duration_hours * 15  # $15 per hour example
    
    # Estimate fuel cost based on distance/duration
    costs["fuel_cost"] = booking.duration_hours * 5  # $5 per hour example
    
    # Get additional costs from operation if available
    if booking.excursion_operation:
        operation = frappe.get_doc("Excursion Operation", booking.excursion_operation)
        costs["other_costs"] = operation.additional_costs or 0
    
    costs["total_costs"] = sum(costs.values())
    
    # Calculate profitability
    revenue = booking.total_amount or 0
    profit = revenue - costs["total_costs"]
    profit_margin = (profit / revenue * 100) if revenue > 0 else 0
    
    return {
        "revenue": revenue,
        "costs": costs,
        "profit": profit,
        "profit_margin": profit_margin
    }

@frappe.whitelist()
def get_excursion_analytics(days_back=30):
    """Get comprehensive excursion analytics
    
    Args:
        days_back (int): Number of days to analyze
        
    Returns:
        dict: Analytics data
    """
    try:
        from frappe.utils import add_days, getdate
        
        start_date = add_days(getdate(), -days_back)
        
        # Basic statistics
        total_bookings = frappe.db.count("Excursion Booking", {
            "excursion_date": [">=", start_date]
        })
        
        confirmed_bookings = frappe.db.count("Excursion Booking", {
            "excursion_date": [">=", start_date],
            "booking_status": "Confirmed"
        })
        
        total_revenue = frappe.db.sql("""
            SELECT SUM(total_amount) as revenue
            FROM `tabExcursion Booking`
            WHERE excursion_date >= %s AND booking_status != 'Cancelled'
        """, [start_date])[0][0] or 0
        
        total_guests = frappe.db.sql("""
            SELECT SUM(total_guests) as guests
            FROM `tabExcursion Booking`
            WHERE excursion_date >= %s AND booking_status != 'Cancelled'
        """, [start_date])[0][0] or 0
        
        # Popular packages
        popular_packages = get_popular_excursion_packages(5, days_back)
        
        # Category breakdown
        category_stats = frappe.db.sql("""
            SELECT 
                ep.excursion_category,
                COUNT(eb.name) as booking_count,
                SUM(eb.total_amount) as revenue
            FROM `tabExcursion Package` ep
            LEFT JOIN `tabExcursion Booking` eb ON ep.name = eb.excursion_package
                AND eb.excursion_date >= %s
                AND eb.booking_status != 'Cancelled'
            GROUP BY ep.excursion_category
            ORDER BY booking_count DESC
        """, [start_date], as_dict=True)
        
        return {
            "status": "success",
            "analytics": {
                "summary": {
                    "total_bookings": total_bookings,
                    "confirmed_bookings": confirmed_bookings,
                    "total_revenue": total_revenue,
                    "total_guests": total_guests,
                    "avg_booking_value": total_revenue / confirmed_bookings if confirmed_bookings > 0 else 0
                },
                "popular_packages": popular_packages,
                "category_breakdown": category_stats
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Analytics error: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def validate_excursion_booking_data(data):
    """Validate excursion booking data before saving
    
    Args:
        data (dict): Booking data to validate
        
    Returns:
        dict: Validation result
    """
    try:
        errors = []
        warnings = []
        
        # Required field validation
        required_fields = [
            "excursion_package", "excursion_date", "departure_time",
            "customer_name", "customer_phone", "total_guests", "adult_count"
        ]
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        # Business logic validation
        if data.get("total_guests", 0) != (data.get("adult_count", 0) + data.get("child_count", 0)):
            errors.append("Total guests must equal sum of adults and children")
        
        # Package availability validation
        if data.get("excursion_package") and data.get("excursion_date"):
            package = frappe.get_doc("Excursion Package", data["excursion_package"])
            
            if package.package_status != "Active":
                errors.append("Selected excursion package is not active")
            
            if data.get("total_guests", 0) > package.max_capacity:
                errors.append(f"Total guests exceeds package capacity ({package.max_capacity})")
            
            # Check booking deadline
            from frappe.utils import getdate, add_to_date, now_datetime, time_diff_in_hours
            
            booking_deadline_hours = package.booking_deadline_hours or 24
            excursion_datetime = f"{data['excursion_date']} {data.get('departure_time', '08:00:00')}"
            
            time_until_excursion = time_diff_in_hours(excursion_datetime, now_datetime())
            
            if time_until_excursion < booking_deadline_hours:
                warnings.append(f"Booking is within {booking_deadline_hours} hour deadline")
        
        return {
            "status": "success",
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        frappe.log_error(f"Validation error: {str(e)}")
        return {
            "status": "error",
            "valid": False,
            "message": str(e)
        }
