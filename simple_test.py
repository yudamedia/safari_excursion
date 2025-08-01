#!/usr/bin/env python3
import frappe

def test_new_doctypes():
    print("Testing new Safari Excursion doctypes...")
    
    # Test if new doctypes exist
    new_doctypes = [
        "Excursion Rate Configuration",
        "Excursion Local Per Person Rate", 
        "Excursion International Per Person Rate",
        "Seasonal Supplement",
        "International Seasonal Supplement",
        "Holiday Surcharge Period",
        "International Holiday Surcharge Period"
    ]
    
    for doctype in new_doctypes:
        exists = frappe.db.exists("DocType", doctype)
        status = "✓" if exists else "✗"
        print(f"{status} {doctype}: {exists}")
    
    print("\nTesting pricing utility import...")
    try:
        from safari_excursion.safari_excursion.utils.pricing_utils import get_excursion_pricing
        print("✓ Pricing utility imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pricing utility: {e}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_new_doctypes() 