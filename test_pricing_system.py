#!/usr/bin/env python3
"""
Test script for the new Safari Excursion pricing system
"""

import frappe
from datetime import date
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pricing_system():
    """Test the new pricing system"""
    print("Testing Safari Excursion Pricing System...")
    
    try:
        # Test 1: Check if new doctypes exist
        print("\n1. Checking new doctypes...")
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
            if frappe.db.exists("DocType", doctype):
                print(f"✓ {doctype} exists")
            else:
                print(f"✗ {doctype} missing")
        
        # Test 2: Check if pricing utility can be imported
        print("\n2. Testing pricing utility import...")
        try:
            from safari_excursion.safari_excursion.utils.pricing_utils import get_excursion_pricing
            print("✓ Pricing utility imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import pricing utility: {e}")
        
        # Test 3: Check if migration utility can be imported
        print("\n3. Testing migration utility import...")
        try:
            from safari_excursion.safari_excursion.utils.migration_utils import run_migration
            print("✓ Migration utility imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import migration utility: {e}")
        
        # Test 4: Check existing excursion packages
        print("\n4. Checking existing excursion packages...")
        packages = frappe.get_all("Excursion Package", fields=["name", "package_name"])
        if packages:
            print(f"✓ Found {len(packages)} existing packages:")
            for package in packages[:5]:  # Show first 5
                print(f"  - {package.package_name} ({package.name})")
        else:
            print("✗ No excursion packages found")
        
        # Test 5: Check if rate configurations exist
        print("\n5. Checking rate configurations...")
        configs = frappe.get_all("Excursion Rate Configuration", fields=["name", "excursion_package"])
        if configs:
            print(f"✓ Found {len(configs)} rate configurations:")
            for config in configs[:5]:  # Show first 5
                print(f"  - {config.excursion_package} ({config.name})")
        else:
            print("✗ No rate configurations found - run migration first")
        
        # Test 6: Check if rate tables exist
        print("\n6. Checking rate tables...")
        local_rates = frappe.get_all("Excursion Local Per Person Rate", fields=["name", "excursion_package"])
        international_rates = frappe.get_all("Excursion International Per Person Rate", fields=["name", "excursion_package"])
        
        print(f"✓ Found {len(local_rates)} local rate tables")
        print(f"✓ Found {len(international_rates)} international rate tables")
        
        # Test 7: Test pricing calculation (if data exists)
        print("\n7. Testing pricing calculation...")
        if configs and local_rates:
            try:
                # Get first available package and rate
                package = frappe.get_doc("Excursion Package", packages[0].name)
                if hasattr(package, 'rate_configuration') and package.rate_configuration:
                    pricing = get_excursion_pricing(
                        excursion_package=package.name,
                        excursion_date=date.today(),
                        adults=2,
                        children=[8, 12],
                        residence_type="International"
                    )
                    print(f"✓ Pricing calculation successful: {pricing['currency']} {pricing['total']}")
                else:
                    print("✗ Package has no rate configuration")
            except Exception as e:
                print(f"✗ Pricing calculation failed: {e}")
        else:
            print("✗ No data available for pricing calculation test")
        
        print("\n" + "="*50)
        print("Pricing system test completed!")
        print("="*50)
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        frappe.log_error(f"Pricing system test failed: {e}")

def test_migration():
    """Test the migration process"""
    print("\nTesting migration process...")
    
    try:
        from safari_excursion.safari_excursion.utils.migration_utils import run_migration
        
        # Check if migration is needed
        packages = frappe.get_all("Excursion Package", fields=["name"])
        configs = frappe.get_all("Excursion Rate Configuration", fields=["name"])
        
        if len(packages) > len(configs):
            print(f"Migration needed: {len(packages)} packages, {len(configs)} configurations")
            response = input("Run migration? (y/n): ")
            if response.lower() == 'y':
                run_migration()
                print("✓ Migration completed")
            else:
                print("Migration skipped")
        else:
            print("✓ No migration needed")
            
    except Exception as e:
        print(f"✗ Migration test failed: {e}")

if __name__ == "__main__":
    # Initialize Frappe
    if not frappe.db:
        frappe.init(site="localhost")
        frappe.connect()
    
    # Run tests
    test_pricing_system()
    test_migration()
    
    print("\nTest script completed!") 