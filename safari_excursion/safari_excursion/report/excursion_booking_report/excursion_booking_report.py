# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/report/excursion_booking_report/excursion_booking_report.py

import frappe
from frappe import _
from frappe.utils import getdate, flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    """Define report columns"""
    return [
        {
            "label": _("Booking Number"),
            "fieldname": "booking_number",
            "fieldtype": "Link",
            "options": "Excursion Booking",
            "width": 150
        },
        {
            "label": _("Date"),
            "fieldname": "excursion_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Customer"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Package"),
            "fieldname": "excursion_package",
            "fieldtype": "Link",
            "options": "Excursion Package",
            "width": 200
        },
        {
            "label": _("Category"),
            "fieldname": "category",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Status"),
            "fieldname": "booking_status",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Adults"),
            "fieldname": "adult_count",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": _("Children"),
            "fieldname": "child_count",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": _("Total Guests"),
            "fieldname": "total_guests",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Guide"),
            "fieldname": "assigned_guide",
            "fieldtype": "Link",
            "options": "Safari Guide",
            "width": 150
        },
        {
            "label": _("Vehicle"),
            "fieldname": "assigned_vehicle",
            "fieldtype": "Link",
            "options": "Vehicle",
            "width": 120
        },
        {
            "label": _("Base Amount"),
            "fieldname": "base_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Park Fees"),
            "fieldname": "park_fees",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Payment Status"),
            "fieldname": "payment_status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Parks Visited"),
            "fieldname": "parks_visited",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Transport"),
            "fieldname": "transport_booking",
            "fieldtype": "Link",
            "options": "Transport Booking",
            "width": 150
        }
    ]

def get_data(filters):
    """Fetch excursion booking data with filters"""
    conditions = get_conditions(filters)
    
    query = """
        SELECT 
            eb.name as booking_number,
            eb.excursion_date,
            eb.customer_name,
            eb.excursion_package,
            ep.excursion_category as category,
            eb.booking_status,
            eb.adult_count,
            eb.child_count,
            eb.total_guests,
            eb.assigned_guide,
            eb.assigned_vehicle,
            eb.base_amount,
            eb.additional_charges,
            eb.total_amount,
            eb.payment_status,
            eb.transport_booking,
            eb.park_booking,
            eb.currency
        FROM 
            `tabExcursion Booking` eb
        LEFT JOIN `tabExcursion Package` ep ON eb.excursion_package = ep.name
        WHERE 1=1 {conditions}
        ORDER BY eb.excursion_date DESC, eb.creation DESC
    """.format(conditions=conditions)
    
    data = frappe.db.sql(query, as_dict=True)
    
    # Add park fee breakdown and parks visited
    for row in data:
        # Get park fees breakdown
        park_fees = get_park_fees_for_booking(row.booking_number)
        row["park_fees"] = park_fees.get("total_fees", 0)
        row["parks_visited"] = park_fees.get("parks_list", "")
        
        # Format currency values
        for currency_field in ["base_amount", "additional_charges", "total_amount", "park_fees"]:
            if row.get(currency_field):
                row[currency_field] = flt(row[currency_field], 2)
    
    return data

def get_conditions(filters):
    """Build SQL conditions based on filters"""
    conditions = ""
    
    if filters.get("from_date"):
        conditions += f" AND eb.excursion_date >= '{filters['from_date']}'"
    
    if filters.get("to_date"):
        conditions += f" AND eb.excursion_date <= '{filters['to_date']}'"
    
    if filters.get("booking_status"):
        if isinstance(filters["booking_status"], list):
            status_list = "', '".join(filters["booking_status"])
            conditions += f" AND eb.booking_status IN ('{status_list}')"
        else:
            conditions += f" AND eb.booking_status = '{filters['booking_status']}'"
    
    if filters.get("excursion_category"):
        conditions += f" AND ep.excursion_category = '{filters['excursion_category']}'"
    
    if filters.get("excursion_package"):
        conditions += f" AND eb.excursion_package = '{filters['excursion_package']}'"
    
    if filters.get("assigned_guide"):
        conditions += f" AND eb.assigned_guide = '{filters['assigned_guide']}'"
    
    if filters.get("assigned_vehicle"):
        conditions += f" AND eb.assigned_vehicle = '{filters['assigned_vehicle']}'"
    
    if filters.get("payment_status"):
        conditions += f" AND eb.payment_status = '{filters['payment_status']}'"
    
    if filters.get("customer"):
        conditions += f" AND eb.customer = '{filters['customer']}'"
    
    return conditions

def get_park_fees_for_booking(booking_name):
    """Get park fees and parks list for a booking"""
    result = {"total_fees": 0, "parks_list": ""}
    
    try:
        # Get park booking if exists
        park_booking = frappe.db.get_value("Excursion Booking", booking_name, "park_booking")
        
        if park_booking:
            # Get park fee calculations
            park_fees = frappe.get_all(
                "Park Fee Calculation",
                filters={"park_booking": park_booking},
                fields=["total_fee", "national_park"],
                order_by="creation"
            )
            
            if park_fees:
                result["total_fees"] = sum(fee.total_fee for fee in park_fees)
                parks = [fee.national_park for fee in park_fees if fee.national_park]
                result["parks_list"] = ", ".join(parks)
        
        # If no park booking, try to get from package destinations
        if not result["parks_list"]:
            booking = frappe.get_doc("Excursion Booking", booking_name)
            package = frappe.get_doc("Excursion Package", booking.excursion_package)
            
            park_destinations = []
            if hasattr(package, 'destination_locations') and package.destination_locations:
                for dest in package.destination_locations:
                    if dest.location_type in ["National Park", "Marine Park", "Conservancy"]:
                        park_destinations.append(dest.location_name)
            
            result["parks_list"] = ", ".join(park_destinations)
    
    except Exception as e:
        frappe.log_error(f"Error getting park fees for {booking_name}: {str(e)}")
    
    return result