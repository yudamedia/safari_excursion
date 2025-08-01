import frappe
from datetime import date

def migrate_excursion_pricing():
    """
    Migration script to convert old excursion pricing to new currency-based system
    """
    frappe.msgprint("Starting excursion pricing migration...")
    
    # Get all excursion packages
    packages = frappe.get_all("Excursion Package", fields=["name", "base_price_adult", "base_price_child", "currency"])
    
    for package in packages:
        try:
            # Create rate configuration
            create_rate_configuration(package)
            
            # Create rate tables
            create_rate_tables(package)
            
            frappe.msgprint(f"Migrated pricing for package: {package.name}")
            
        except Exception as e:
            frappe.msgprint(f"Error migrating package {package.name}: {str(e)}", indicator="red")
    
    frappe.msgprint("Migration completed!")

def create_rate_configuration(package):
    """Create rate configuration for a package"""
    # Check if rate configuration already exists
    existing_config = frappe.get_all("Excursion Rate Configuration", 
                                   filters={"excursion_package": package.name})
    
    if existing_config:
        return existing_config[0].name
    
    # Create new rate configuration
    config = frappe.get_doc({
        "doctype": "Excursion Rate Configuration",
        "excursion_package": package.name,
        "pricing_model": "Per Person",
        "has_child_rates": 1 if package.base_price_child else 0,
        "child_rate_type": "Fixed Rate" if package.base_price_child else None,
        "has_seasonal_supplements": 0,
        "has_holiday_surcharges": 0,
        "has_group_discounts": 0
    })
    
    config.insert()
    return config.name

def create_rate_tables(package):
    """Create rate tables for a package"""
    # Get default season (create if doesn't exist)
    default_season = get_or_create_default_season()
    
    # Create local rate table
    create_local_rate_table(package, default_season)
    
    # Create international rate table
    create_international_rate_table(package, default_season)

def get_or_create_default_season():
    """Get or create a default season"""
    default_season = frappe.get_all("Excursion Season", 
                                  filters={"season_name": "Default Season"})
    
    if default_season:
        return default_season[0].name
    
    # Create default season
    season = frappe.get_doc({
        "doctype": "Excursion Season",
        "season_name": "Default Season",
        "start_date": date(2020, 1, 1),
        "end_date": date(2030, 12, 31),
        "description": "Default season for migrated packages"
    })
    
    season.insert()
    return season.name

def create_local_rate_table(package, season):
    """Create local rate table"""
    # Check if local rate table already exists
    existing_local = frappe.get_all("Excursion Local Per Person Rate",
                                   filters={
                                       "excursion_package": package.name,
                                       "season": season
                                   })
    
    if existing_local:
        return existing_local[0].name
    
    # Convert currency to KES if needed
    if package.currency == "USD":
        # Simple conversion (in real scenario, you'd use exchange rates)
        adult_rate = package.base_price_adult * 100  # Approximate USD to KES
        child_rate = package.base_price_child * 100 if package.base_price_child else 0
    else:
        adult_rate = package.base_price_adult
        child_rate = package.base_price_child
    
    local_rate = frappe.get_doc({
        "doctype": "Excursion Local Per Person Rate",
        "excursion_package": package.name,
        "season": season,
        "currency": "KES",
        "adult_rate": adult_rate
    })
    
    local_rate.insert()
    return local_rate.name

def create_international_rate_table(package, season):
    """Create international rate table"""
    # Check if international rate table already exists
    existing_international = frappe.get_all("Excursion International Per Person Rate",
                                          filters={
                                              "excursion_package": package.name,
                                              "season": season
                                          })
    
    if existing_international:
        return existing_international[0].name
    
    # Convert currency to USD if needed
    if package.currency == "KES":
        # Simple conversion (in real scenario, you'd use exchange rates)
        adult_rate = package.base_price_adult / 100  # Approximate KES to USD
        child_rate = package.base_price_child / 100 if package.base_price_child else 0
    else:
        adult_rate = package.base_price_adult
        child_rate = package.base_price_child
    
    international_rate = frappe.get_doc({
        "doctype": "Excursion International Per Person Rate",
        "excursion_package": package.name,
        "season": season,
        "currency": "USD",
        "adult_rate": adult_rate
    })
    
    international_rate.insert()
    return international_rate.name

def cleanup_old_pricing_fields():
    """Remove old pricing fields from excursion package"""
    # This would be done after migration is complete
    # and all data has been verified
    pass

@frappe.whitelist()
def run_migration():
    """Run the migration (callable from UI)"""
    try:
        migrate_excursion_pricing()
        frappe.msgprint("Migration completed successfully!", indicator="green")
    except Exception as e:
        frappe.msgprint(f"Migration failed: {str(e)}", indicator="red")
        frappe.log_error(f"Excursion pricing migration failed: {str(e)}") 