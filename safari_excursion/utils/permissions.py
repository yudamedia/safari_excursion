# -*- coding: utf-8 -*-
# Copyright (c) 2025, Safari Management and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_permission_query_conditions(user=None):
    """
    Get permission query conditions for Excursion Booking
    
    This function is called by ERPNext to filter records based on user permissions.
    It returns SQL conditions that are automatically added to queries.
    
    Args:
        user (str): Username to check permissions for. Defaults to current user.
        
    Returns:
        str: SQL WHERE conditions to filter records
    """
    if not user:
        user = frappe.session.user
        
    # Skip permission filtering for Administrator
    if user == "Administrator":
        return ""
        
    user_roles = frappe.get_roles(user)
    
    # Managers and System Managers can see all bookings
    manager_roles = ["Safari Manager", "Excursion Manager", "System Manager"]
    if any(role in manager_roles for role in user_roles):
        return ""
    
    # Guides can only see their assigned bookings
    if "Excursion Guide" in user_roles:
        guide_name = frappe.db.get_value("Safari Guide", {"user": user}, "name")
        if guide_name:
            return f"`tabExcursion Booking`.assigned_guide = '{guide_name}'"
        else:
            # If guide record not found, show no bookings
            return "1=0"
    
    # Safari Users can see bookings they created or are assigned as customer
    if "Safari User" in user_roles:
        conditions = []
        
        # Bookings they created
        conditions.append(f"`tabExcursion Booking`.owner = '{user}'")
        
        # Bookings where they are the customer (if customer has user field)
        customer = frappe.db.get_value("Customer", {"user": user}, "name")
        if customer:
            conditions.append(f"`tabExcursion Booking`.customer = '{customer}'")
        
        # Join conditions with OR
        if conditions:
            return f"({' OR '.join(conditions)})"
    
    # Default: Users can only see bookings they created
    return f"`tabExcursion Booking`.owner = '{user}'"

def has_permission(doc, user=None, permission_type=None):
    """
    Check if user has permission for specific Excursion Booking document
    
    This function is called for individual document access control.
    
    Args:
        doc: The Excursion Booking document
        user (str): Username to check permissions for. Defaults to current user.
        permission_type (str): Type of permission (read, write, delete, etc.)
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user:
        user = frappe.session.user
    
    # Skip permission check for Administrator
    if user == "Administrator":
        return True
    
    # Handle string document name vs document object
    if isinstance(doc, str):
        doc = frappe.get_doc("Excursion Booking", doc)
    
    user_roles = frappe.get_roles(user)
    
    # Managers have full access to all bookings
    manager_roles = ["Safari Manager", "Excursion Manager", "System Manager"]
    if any(role in manager_roles for role in user_roles):
        return True
    
    # Guides can access their assigned bookings
    if "Excursion Guide" in user_roles:
        guide_name = frappe.db.get_value("Safari Guide", {"user": user}, "name")
        if guide_name and doc.assigned_guide == guide_name:
            return True
    
    # Users can access bookings they created
    if doc.owner == user:
        return True
    
    # Customer can view their own bookings
    if doc.customer:
        customer_user = frappe.db.get_value("Customer", doc.customer, "user")
        if customer_user == user:
            return True
    
    # Check if user is the primary guest or in guest list
    if hasattr(doc, 'primary_guest') and doc.primary_guest:
        primary_guest_user = frappe.db.get_value("Safari Guest", doc.primary_guest, "user")
        if primary_guest_user == user:
            return True
    
    # Check if user is in the guest list
    if hasattr(doc, 'guests') and doc.guests:
        for guest_row in doc.guests:
            if guest_row.guest:
                guest_user = frappe.db.get_value("Safari Guest", guest_row.guest, "user")
                if guest_user == user:
                    return True
    
    # For certain permission types, allow read access to Safari Users
    if permission_type in ["read", "print"] and "Safari User" in user_roles:
        # Additional read permissions for Safari Users can be defined here
        pass
    
    # Default: No permission
    return False

def get_excursion_package_permissions(user=None):
    """
    Get permission query conditions for Excursion Package
    
    Args:
        user (str): Username to check permissions for. Defaults to current user.
        
    Returns:
        str: SQL WHERE conditions to filter records
    """
    if not user:
        user = frappe.session.user
        
    # Skip permission filtering for Administrator
    if user == "Administrator":
        return ""
        
    user_roles = frappe.get_roles(user)
    
    # Managers can see all packages
    manager_roles = ["Safari Manager", "Excursion Manager", "System Manager"]
    if any(role in manager_roles for role in user_roles):
        return ""
    
    # Only show published packages to non-managers
    return "`tabExcursion Package`.is_published = 1"

def can_create_excursion_booking(user=None):
    """
    Check if user can create new excursion bookings
    
    Args:
        user (str): Username to check permissions for. Defaults to current user.
        
    Returns:
        bool: True if user can create bookings, False otherwise
    """
    if not user:
        user = frappe.session.user
        
    # Skip check for Administrator
    if user == "Administrator":
        return True
        
    user_roles = frappe.get_roles(user)
    
    # Roles that can create bookings
    create_roles = ["Safari Manager", "Excursion Manager", "Safari User", "System Manager"]
    return any(role in create_roles for role in user_roles)

def can_modify_excursion_booking(doc, user=None):
    """
    Check if user can modify an excursion booking
    
    Args:
        doc: The Excursion Booking document
        user (str): Username to check permissions for. Defaults to current user.
        
    Returns:
        bool: True if user can modify the booking, False otherwise
    """
    if not user:
        user = frappe.session.user
        
    # Skip check for Administrator
    if user == "Administrator":
        return True
    
    # Handle string document name vs document object
    if isinstance(doc, str):
        doc = frappe.get_doc("Excursion Booking", doc)
    
    user_roles = frappe.get_roles(user)
    
    # Managers can always modify
    manager_roles = ["Safari Manager", "Excursion Manager", "System Manager"]
    if any(role in manager_roles for role in user_roles):
        return True
    
    # Check booking status - completed bookings might be restricted
    if doc.booking_status == "Completed":
        # Only managers can modify completed bookings
        return False
    
    # Guides can modify their assigned bookings (limited fields)
    if "Excursion Guide" in user_roles:
        guide_name = frappe.db.get_value("Safari Guide", {"user": user}, "name")
        if guide_name and doc.assigned_guide == guide_name:
            return True
    
    # Users can modify bookings they created (before confirmation)
    if doc.owner == user and doc.booking_status in ["Draft", "Pending"]:
        return True
    
    return False

# Utility functions for permission checking

def get_user_guide_name(user=None):
    """Get the Safari Guide name for a user"""
    if not user:
        user = frappe.session.user
    return frappe.db.get_value("Safari Guide", {"user": user}, "name")

def get_user_customer_name(user=None):
    """Get the Customer name for a user"""
    if not user:
        user = frappe.session.user
    return frappe.db.get_value("Customer", {"user": user}, "name")

def is_booking_accessible_to_user(booking_name, user=None):
    """
    Quick check if a booking is accessible to a user
    
    Args:
        booking_name (str): Name of the Excursion Booking
        user (str): Username to check permissions for. Defaults to current user.
        
    Returns:
        bool: True if accessible, False otherwise
    """
    try:
        doc = frappe.get_doc("Excursion Booking", booking_name)
        return has_permission(doc, user, "read")
    except frappe.DoesNotExistError:
        return False
    except frappe.PermissionError:
        return False