# ~/frappe-bench/apps/safari_excursion/safari_excursion/setup/install.py

import frappe
from frappe import _

def before_install():
    """Check dependencies before installation"""
    check_dependencies()

def after_install():
    """Post-installation setup"""
    setup_default_data()
    setup_custom_fields()
    setup_roles_and_permissions()
    setup_notification_templates()

def check_dependencies():
    """Check if required apps are installed"""
    required_apps = ['safari_core', 'safari_transport', 'safari_packages']
    
    for app in required_apps:
        if app not in frappe.get_installed_apps():
            frappe.throw(_("Please install {0} before installing Safari Excursion").format(app))
            
    # Check for required doctypes
    required_doctypes = [
        ("Safari Guest", "safari_core"),
        ("Booking Party", "safari_core"),
        ("Area Location", "safari_core"),
        ("Transport Booking", "safari_transport"),
        ("Vehicle", "safari_transport"),
        ("Safari Guide", "safari_core"),
        ("Safari Package", "safari_packages")
    ]
    
    for doctype, app in required_doctypes:
        if not frappe.db.exists("DocType", doctype):
            frappe.throw(_("Required DocType {0} from {1} not found").format(doctype, app))

def setup_default_data():
    """Setup default excursion categories and data"""
    
    # Create default excursion categories
    categories = [
        {
            "name": "Cultural Tours",
            "description": "Cultural heritage and historical site visits",
            "default_duration": 6,
            "color": "#8B4513"
        },
        {
            "name": "Adventure Activities", 
            "description": "Adventure sports and outdoor activities",
            "default_duration": 8,
            "color": "#228B22"
        },
        {
            "name": "Wildlife Experiences",
            "description": "Wildlife viewing and nature experiences", 
            "default_duration": 10,
            "color": "#DAA520"
        },
        {
            "name": "Marine Activities",
            "description": "Ocean and water-based activities",
            "default_duration": 8,
            "color": "#4682B4"
        },
        {
            "name": "City Tours",
            "description": "Urban exploration and city sightseeing",
            "default_duration": 4,
            "color": "#DC143C"
        }
    ]
    
    for category_data in categories:
        if not frappe.db.exists("Excursion Category", category_data["name"]):
            category = frappe.get_doc({
                "doctype": "Excursion Category",
                "category_name": category_data["name"],
                "description": category_data["description"],
                "default_duration_hours": category_data["default_duration"],
                "category_color": category_data["color"]
            })
            category.insert(ignore_permissions=True)
    
    frappe.db.commit()

def setup_custom_fields():
    """Add custom fields to existing doctypes for excursion integration"""
    
    # Add custom fields to Transport Booking for excursion tracking
    transport_booking_fields = [
        {
            "fieldname": "excursion_booking",
            "label": "Excursion Booking",
            "fieldtype": "Link",
            "options": "Excursion Booking",
            "insert_after": "booking_reference",
            "read_only": 1
        },
        {
            "fieldname": "is_excursion_transport",
            "label": "Is Excursion Transport",
            "fieldtype": "Check",
            "insert_after": "excursion_booking",
            "default": 0
        }
    ]
    
    create_custom_fields("Transport Booking", transport_booking_fields)
    
    # Add custom fields to Safari Guide for excursion specialization
    guide_fields = [
        {
            "fieldname": "excursion_specialties",
            "label": "Excursion Specialties",
            "fieldtype": "Table MultiSelect",
            "options": "Guide Excursion Specialty",
            "insert_after": "guide_skills"
        },
        {
            "fieldname": "preferred_excursion_types",
            "label": "Preferred Excursion Types",
            "fieldtype": "Table MultiSelect", 
            "options": "Guide Preferred Excursion",
            "insert_after": "excursion_specialties"
        }
    ]
    
    create_custom_fields("Safari Guide", guide_fields)

def create_custom_fields(doctype, fields):
    """Helper function to create custom fields"""
    for field_dict in fields:
        if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_dict["fieldname"]}):
            custom_field = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                **field_dict
            })
            custom_field.insert(ignore_permissions=True)

def setup_roles_and_permissions():
    """Setup excursion-specific roles and permissions"""
    
    # Create Excursion Manager role
    if not frappe.db.exists("Role", "Excursion Manager"):
        excursion_manager = frappe.get_doc({
            "doctype": "Role",
            "role_name": "Excursion Manager",
            "desk_access": 1,
            "is_custom": 1
        })
        excursion_manager.insert(ignore_permissions=True)
    
    # Create Excursion Guide role
    if not frappe.db.exists("Role", "Excursion Guide"):
        excursion_guide = frappe.get_doc({
            "doctype": "Role", 
            "role_name": "Excursion Guide",
            "desk_access": 1,
            "is_custom": 1
        })
        excursion_guide.insert(ignore_permissions=True)

def setup_notification_templates():
    """Setup email and SMS templates for excursions"""
    
    templates = [
        {
            "name": "Excursion Booking Confirmation",
            "subject": "Your Excursion Booking Confirmed - {{ doc.booking_number }}",
            "message": """
            <h3>Excursion Booking Confirmation</h3>
            <p>Dear {{ doc.customer_name }},</p>
            <p>Your excursion booking has been confirmed!</p>
            
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr><td><strong>Booking Number:</strong></td><td>{{ doc.booking_number }}</td></tr>
                <tr><td><strong>Excursion:</strong></td><td>{{ doc.excursion_package }}</td></tr>
                <tr><td><strong>Date:</strong></td><td>{{ doc.excursion_date }}</td></tr>
                <tr><td><strong>Pickup Time:</strong></td><td>{{ doc.pickup_time }}</td></tr>
                <tr><td><strong>Pickup Location:</strong></td><td>{{ doc.pickup_location }}</td></tr>
                <tr><td><strong>Total Guests:</strong></td><td>{{ doc.total_guests }}</td></tr>
            </table>
            
            <p>Please be ready at your pickup location 10 minutes before the scheduled time.</p>
            <p>Have a wonderful excursion!</p>
            """,
            "doctype": "Excursion Booking"
        },
        {
            "name": "Excursion Guide Assignment",
            "subject": "New Excursion Assignment - {{ doc.booking_number }}",
            "message": """
            <h3>New Excursion Assignment</h3>
            <p>You have been assigned to guide the following excursion:</p>
            
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr><td><strong>Booking:</strong></td><td>{{ doc.booking_number }}</td></tr>
                <tr><td><strong>Excursion:</strong></td><td>{{ doc.excursion_package }}</td></tr>
                <tr><td><strong>Date:</strong></td><td>{{ doc.excursion_date }}</td></tr>
                <tr><td><strong>Guests:</strong></td><td>{{ doc.total_guests }}</td></tr>
                <tr><td><strong>Pickup:</strong></td><td>{{ doc.pickup_location }} at {{ doc.pickup_time }}</td></tr>
                <tr><td><strong>Customer Contact:</strong></td><td>{{ doc.customer_phone }}</td></tr>
            </table>
            
            <p>Please confirm your availability and review the excursion details.</p>
            """,
            "doctype": "Excursion Booking"
        }
    ]
    
    for template_data in templates:
        if not frappe.db.exists("Email Template", template_data["name"]):
            template = frappe.get_doc({
                "doctype": "Email Template",
                "name": template_data["name"],
                "subject": template_data["subject"],
                "response": template_data["message"],
                "reference_doctype": template_data["doctype"]
            })
            template.insert(ignore_permissions=True)

def setup_integration():
    """Setup integration with other safari apps after installation"""
    frappe.msgprint(_("Safari Excursion app installed successfully and integrated with transport system"))
    frappe.db.commit()
