import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "guide_name",
            "label": _("Guide Name"),
            "fieldtype": "Link",
            "options": "Safari Guide",
            "width": 180
        },
        {
            "fieldname": "availability_status",
            "label": _("Availability"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "today_assignments",
            "label": _("Today's Assignments"),
            "fieldtype": "Int",
            "width": 140
        },
        {
            "fieldname": "week_assignments",
            "label": _("This Week"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "guide_languages",
            "label": _("Languages"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "specializations",
            "label": _("Specializations"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "contact_number",
            "label": _("Contact"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "next_assignment",
            "label": _("Next Assignment"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "next_assignment_package",
            "label": _("Next Package"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "total_bookings_month",
            "label": _("Month Total"),
            "fieldtype": "Int",
            "width": 100
        }
    ]

def get_data(filters):
    from_date = filters.get("from_date", getdate())
    to_date = filters.get("to_date", add_days(getdate(), 7))
    
    # Base conditions for guide filtering
    guide_conditions = "sg.status = 'Active'"
    
    if filters and filters.get("availability_status"):
        guide_conditions += f" AND sg.availability_status = '{filters['availability_status']}'"
    
    if filters and filters.get("guide_name"):
        guide_conditions += f" AND sg.name = '{filters['guide_name']}'"
    
    # Get all guides with basic info
    guides_query = f"""
        SELECT 
            sg.name as guide_name,
            sg.availability_status,
            sg.guide_languages,
            sg.specializations,
            sg.contact_number,
            sg.guide_name as full_name
        FROM 
            `tabSafari Guide` sg
        WHERE 
            {guide_conditions}
        ORDER BY sg.guide_name
    """
    
    guides = frappe.db.sql(guides_query, as_dict=True)
    
    data = []
    today = getdate()
    month_start = today.replace(day=1)
    
    for guide in guides:
        # Count today's assignments
        today_count = frappe.db.count("Excursion Booking", {
            "assigned_guide": guide.guide_name,
            "excursion_date": today,
            "booking_status": ["!=", "Cancelled"]
        })
        
        # Count this week's assignments
        week_count = frappe.db.count("Excursion Booking", {
            "assigned_guide": guide.guide_name,
            "excursion_date": ["between", [from_date, to_date]],
            "booking_status": ["!=", "Cancelled"]
        })
        
        # Count this month's total bookings
        month_count = frappe.db.count("Excursion Booking", {
            "assigned_guide": guide.guide_name,
            "excursion_date": ["between", [month_start, today]],
            "booking_status": ["!=", "Cancelled"]
        })
        
        # Get next assignment details
        next_assignment_data = frappe.db.get_value("Excursion Booking", {
            "assigned_guide": guide.guide_name,
            "excursion_date": [">", today],
            "booking_status": ["!=", "Cancelled"]
        }, ["excursion_date", "excursion_package"], order_by="excursion_date ASC")
        
        next_assignment = None
        next_package = None
        if next_assignment_data:
            next_assignment = next_assignment_data[0]
            # Get package name
            if next_assignment_data[1]:
                next_package = frappe.db.get_value("Excursion Package", next_assignment_data[1], "package_name")
        
        row_data = {
            "guide_name": guide.guide_name,
            "availability_status": guide.availability_status,
            "today_assignments": today_count,
            "week_assignments": week_count,
            "total_bookings_month": month_count,
            "guide_languages": guide.guide_languages,
            "specializations": guide.specializations,
            "contact_number": guide.contact_number,
            "next_assignment": next_assignment,
            "next_assignment_package": next_package
        }
        
        # Add styling based on availability and assignments
        if guide.availability_status == "Unavailable":
            row_data['_style'] = 'background-color: #ffebee;'  # Light red
        elif today_count == 0 and guide.availability_status == "Available":
            row_data['_style'] = 'background-color: #e8f5e8;'  # Light green
        elif today_count > 2:
            row_data['_style'] = 'background-color: #fff3e0;'  # Light orange for overloaded
        
        data.append(row_data)
    
    return data