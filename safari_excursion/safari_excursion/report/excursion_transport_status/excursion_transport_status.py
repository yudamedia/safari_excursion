import frappe
from frappe import _
from frappe.utils import getdate, format_time

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "booking_number",
            "label": _("Booking #"),
            "fieldtype": "Link",
            "options": "Excursion Booking",
            "width": 120
        },
        {
            "fieldname": "excursion_date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "departure_time",
            "label": _("Departure"),
            "fieldtype": "Time",
            "width": 100
        },
        {
            "fieldname": "customer_name",
            "label": _("Customer"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "pickup_required",
            "label": _("Pickup Required"),
            "fieldtype": "Check",
            "width": 120
        },
        {
            "fieldname": "pickup_location",
            "label": _("Pickup Location"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "pickup_time",
            "label": _("Pickup Time"),
            "fieldtype": "Time",
            "width": 100
        },
        {
            "fieldname": "assigned_vehicle",
            "label": _("Vehicle"),
            "fieldtype": "Link",
            "options": "Vehicle",
            "width": 120
        },
        {
            "fieldname": "assigned_guide",
            "label": _("Driver/Guide"),
            "fieldtype": "Link",
            "options": "Safari Guide",
            "width": 150
        },
        {
            "fieldname": "pickup_confirmation_status",
            "label": _("Pickup Status"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "transport_booking",
            "label": _("Transport Booking"),
            "fieldtype": "Link",
            "options": "Transport Booking",
            "width": 140
        },
        {
            "fieldname": "total_guests",
            "label": _("Guests"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "contact_number",
            "label": _("Customer Phone"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "excursion_package",
            "label": _("Package"),
            "fieldtype": "Data",
            "width": 180
        }
    ]

def get_data(filters):
    from_date = filters.get("from_date", getdate())
    to_date = filters.get("to_date", getdate())
    
    conditions = get_conditions(filters, from_date, to_date)
    
    query = f"""
        SELECT 
            eb.name as booking_number,
            eb.excursion_date,
            eb.departure_time,
            eb.customer_name,
            eb.pickup_required,
            eb.pickup_location,
            eb.pickup_time,
            eb.assigned_vehicle,
            eb.assigned_guide,
            COALESCE(eb.pickup_confirmation_status, 'Pending') as pickup_confirmation_status,
            eb.transport_booking,
            eb.total_guests,
            eb.customer_phone as contact_number,
            ep.package_name as excursion_package,
            eb.booking_status,
            eb.excursion_status,
            v.license_plate as vehicle_plate,
            sg.contact_number as guide_contact
        FROM 
            `tabExcursion Booking` eb
        LEFT JOIN `tabExcursion Package` ep ON eb.excursion_package = ep.name
        LEFT JOIN `tabVehicle` v ON eb.assigned_vehicle = v.name
        LEFT JOIN `tabSafari Guide` sg ON eb.assigned_guide = sg.name
        WHERE 
            {conditions}
        ORDER BY eb.excursion_date ASC, eb.departure_time ASC, eb.pickup_time ASC
    """
    
    data = frappe.db.sql(query, as_dict=True)
    
    # Add computed fields and formatting
    for row in data:
        # Format times
        if row.get('departure_time'):
            row['departure_time'] = format_time(row['departure_time'])
        if row.get('pickup_time'):
            row['pickup_time'] = format_time(row['pickup_time'])
        
        # Add vehicle plate to display
        if row.get('vehicle_plate') and row.get('assigned_vehicle'):
            row['assigned_vehicle'] = f"{row['assigned_vehicle']} ({row['vehicle_plate']})"
        
        # Add guide contact to display
        if row.get('guide_contact') and row.get('assigned_guide'):
            row['assigned_guide'] = f"{row['assigned_guide']} ({row['guide_contact']})"
        
        # Add status-based styling
        pickup_status = row.get('pickup_confirmation_status', 'Pending')
        if pickup_status == 'Failed':
            row['_style'] = 'background-color: #ffebee;'  # Light red
        elif pickup_status == 'Completed':
            row['_style'] = 'background-color: #e8f5e8;'  # Light green
        elif pickup_status == 'In Transit':
            row['_style'] = 'background-color: #e3f2fd;'  # Light blue
        elif pickup_status == 'Pending' and row.get('pickup_required'):
            row['_style'] = 'background-color: #fff3e0;'  # Light orange
        
        # Add alerts for missing assignments
        alerts = []
        if row.get('pickup_required') and not row.get('assigned_vehicle'):
            alerts.append("No Vehicle")
        if row.get('pickup_required') and not row.get('assigned_guide'):
            alerts.append("No Driver")
        if row.get('pickup_required') and not row.get('pickup_time'):
            alerts.append("No Pickup Time")
        
        if alerts:
            row['_alerts'] = " | ".join(alerts)
    
    return data

def get_conditions(filters, from_date, to_date):
    conditions = f"eb.excursion_date BETWEEN '{from_date}' AND '{to_date}'"
    conditions += " AND eb.booking_status != 'Cancelled'"
    
    if filters.get("pickup_confirmation_status"):
        conditions += f" AND eb.pickup_confirmation_status = '{filters['pickup_confirmation_status']}'"
    
    if filters.get("assigned_vehicle"):
        conditions += f" AND eb.assigned_vehicle = '{filters['assigned_vehicle']}'"
    
    if filters.get("pickup_required"):
        conditions += " AND eb.pickup_required = 1"
    
    if filters.get("booking_status"):
        status_list = filters.get("booking_status")
        if isinstance(status_list, list):
            status_condition = "', '".join(status_list)
            conditions += f" AND eb.booking_status IN ('{status_condition}')"
        else:
            conditions += f" AND eb.booking_status = '{status_list}'"
    
    return conditions