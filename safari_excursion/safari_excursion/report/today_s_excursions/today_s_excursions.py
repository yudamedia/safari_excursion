import frappe
from frappe import _
from frappe.utils import getdate, nowdate, format_time

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
            "fieldname": "excursion_package",
            "label": _("Package"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "departure_time",
            "label": _("Departure"),
            "fieldtype": "Time",
            "width": 100
        },
        {
            "fieldname": "total_guests",
            "label": _("Guests"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "assigned_guide",
            "label": _("Guide"),
            "fieldtype": "Link",
            "options": "Safari Guide",
            "width": 150
        },
        {
            "fieldname": "assigned_vehicle",
            "label": _("Vehicle"),
            "fieldtype": "Link",
            "options": "Vehicle",
            "width": 120
        },
        {
            "fieldname": "excursion_status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "pickup_location",
            "label": _("Pickup Location"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "customer_name",
            "label": _("Customer"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "customer_phone",
            "label": _("Phone"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "total_amount",
            "label": _("Amount"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "booking_status",
            "label": _("Booking Status"),
            "fieldtype": "Data",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    query = f"""
        SELECT 
            eb.name as booking_number,
            ep.package_name as excursion_package,
            eb.departure_time,
            eb.total_guests,
            eb.assigned_guide,
            eb.assigned_vehicle,
            COALESCE(eb.excursion_status, 'Scheduled') as excursion_status,
            eb.pickup_location,
            eb.customer_name,
            eb.customer_phone,
            eb.total_amount,
            eb.booking_status
        FROM 
            `tabExcursion Booking` eb
        LEFT JOIN `tabExcursion Package` ep ON eb.excursion_package = ep.name
        WHERE 
            eb.excursion_date = CURDATE()
            AND eb.booking_status != 'Cancelled'
            {conditions}
        ORDER BY eb.departure_time ASC, eb.creation ASC
    """
    
    data = frappe.db.sql(query, as_dict=True)
    
    # Add computed fields and formatting
    for row in data:
        # Format departure time
        if row.get('departure_time'):
            row['departure_time'] = format_time(row['departure_time'])
        
        # Add status indicators
        if not row.get('assigned_guide'):
            row['_style'] = 'background-color: #ffe6e6;'  # Light red for unassigned guide
        elif not row.get('assigned_vehicle'):
            row['_style'] = 'background-color: #fff3e0;'  # Light orange for unassigned vehicle
        elif row.get('excursion_status') == 'In Progress':
            row['_style'] = 'background-color: #e8f5e8;'  # Light green for in progress
        
        # Format currency
        if row.get('total_amount'):
            row['total_amount'] = frappe.utils.fmt_money(row['total_amount'])
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters and filters.get("excursion_status"):
        conditions += f" AND eb.excursion_status = '{filters['excursion_status']}'"
    
    if filters and filters.get("assigned_guide"):
        conditions += f" AND eb.assigned_guide = '{filters['assigned_guide']}'"
    
    if filters and filters.get("excursion_package"):
        conditions += f" AND eb.excursion_package = '{filters['excursion_package']}'"
        
    return conditions