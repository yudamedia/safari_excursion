# Safari Excursion Pricing Restructure

## Overview

The Safari Excursion app has been restructured to implement a modular, currency-based pricing system similar to the Safari Accommodation app. This new system provides better flexibility for managing different pricing rules based on age, residence type, and currency.

## Key Changes

### 1. New Pricing Structure

#### Before (Simple Pricing)
- Single currency per excursion package
- Basic adult/child pricing
- Simple seasonal percentage changes
- Limited age brackets

#### After (Modular Currency-Based Pricing)
- Separate pricing for Local (KES) and International (USD) customers
- Configurable child age brackets with specific rates
- Seasonal supplements and holiday surcharges
- Group discount tiers
- Modular rate tables

### 2. New Doctypes

#### Core Configuration
- **Excursion Rate Configuration**: Central configuration for pricing models and policies
- **Excursion Local Per Person Rate**: Local currency (KES) pricing table
- **Excursion International Per Person Rate**: International currency (USD) pricing table

#### Supporting Doctypes
- **Seasonal Supplement**: Local currency seasonal rate adjustments
- **International Seasonal Supplement**: International currency seasonal rate adjustments
- **Holiday Surcharge Period**: Local currency holiday surcharges
- **International Holiday Surcharge Period**: International currency holiday surcharges

### 3. Updated Doctypes

#### Excursion Package
- Removed: `base_price_adult`, `base_price_child`, `currency`, `seasonal_pricing`
- Added: `rate_configuration` (link to rate configuration)

#### Excursion Booking
- Added: `residence_type` (Local/International)
- Updated: Pricing calculation to use new currency-based system

## Implementation Details

### Rate Configuration

The **Excursion Rate Configuration** serves as the central hub for pricing setup:

```json
{
  "excursion_package": "EXP-001",
  "pricing_model": "Per Person",
  "has_child_rates": true,
  "child_rate_type": "Fixed Rate",
  "has_seasonal_supplements": false,
  "has_holiday_surcharges": false,
  "has_group_discounts": true
}
```

### Currency-Based Rate Tables

#### Local Rates (KES)
- Default currency: KES
- Used for local residents
- Separate rate table per season

#### International Rates (USD)
- Default currency: USD
- Used for international tourists
- Separate rate table per season

### Child Rate Structure

Child rates can be configured as:
- **Fixed Rate**: Specific amount per child
- **Percentage of Adult Rate**: Percentage of adult rate

Age brackets are configurable with min/max ages and corresponding rates.

### Supplements and Surcharges

#### Seasonal Supplements
- Fixed amount or percentage adjustments
- Can be reductions or additions
- Separate for adults and children

#### Holiday Surcharges
- Date-based surcharges
- Fixed amount or percentage adjustments
- Separate for adults and children

### Group Discounts

Configurable discount tiers based on group size:
- Minimum and maximum group sizes
- Discount percentage per tier
- Automatic calculation in bookings

## Migration Process

### 1. Run Migration Script

```python
from safari_excursion.safari_excursion.utils.migration_utils import run_migration
run_migration()
```

### 2. Migration Steps

1. **Create Rate Configurations**: For each existing excursion package
2. **Create Rate Tables**: Local and international rate tables
3. **Convert Existing Pricing**: Transfer old pricing to new structure
4. **Create Default Season**: If no seasons exist
5. **Currency Conversion**: Approximate conversion for existing rates

### 3. Post-Migration Tasks

1. **Verify Data**: Check all migrated pricing
2. **Update Exchange Rates**: Use proper exchange rates instead of approximations
3. **Configure Seasons**: Set up proper seasonal pricing
4. **Test Bookings**: Ensure new pricing system works correctly

## Usage Examples

### Creating a New Excursion Package

1. **Create Excursion Package**
   ```python
   package = frappe.get_doc({
       "doctype": "Excursion Package",
       "package_name": "Safari Game Drive",
       "package_code": "SGD-001",
       "rate_configuration": "ERC-SGD-001"
   })
   ```

2. **Create Rate Configuration**
   ```python
   config = frappe.get_doc({
       "doctype": "Excursion Rate Configuration",
       "excursion_package": "SGD-001",
       "pricing_model": "Per Person",
       "has_child_rates": True,
       "child_rate_type": "Fixed Rate"
   })
   ```

3. **Create Rate Tables**
   ```python
   # Local rates
   local_rate = frappe.get_doc({
       "doctype": "Excursion Local Per Person Rate",
       "excursion_package": "SGD-001",
       "season": "High Season",
       "adult_rate": 5000  # KES
   })
   
   # International rates
   international_rate = frappe.get_doc({
       "doctype": "Excursion International Per Person Rate",
       "excursion_package": "SGD-001",
       "season": "High Season",
       "adult_rate": 50  # USD
   })
   ```

### Calculating Pricing in Bookings

```python
from safari_excursion.safari_excursion.utils.pricing_utils import get_excursion_pricing

pricing = get_excursion_pricing(
    excursion_package="SGD-001",
    excursion_date=date(2025, 1, 15),
    adults=2,
    children=[8, 12],
    residence_type="International",
    group_size=4
)

print(f"Total: {pricing['currency']} {pricing['total']}")
```

## Benefits

### 1. Flexibility
- Separate pricing for different customer types
- Configurable age brackets
- Seasonal and holiday adjustments

### 2. Scalability
- Modular design allows easy addition of new pricing rules
- Currency-specific supplements and surcharges
- Group discount tiers

### 3. Consistency
- Similar structure to Safari Accommodation
- Standardized pricing calculations
- Reusable components

### 4. Maintainability
- Clear separation of concerns
- Centralized configuration
- Easy to extend and modify

## Future Enhancements

1. **Dynamic Exchange Rates**: Integration with currency exchange APIs
2. **Advanced Supplements**: Equipment rentals, guide fees, etc.
3. **Bulk Pricing**: Import/export pricing data
4. **Pricing Analytics**: Reports and insights on pricing performance
5. **A/B Testing**: Test different pricing strategies

## Support

For questions or issues with the new pricing system, refer to:
- Safari Accommodation pricing documentation
- Migration utility functions
- Pricing calculation examples
- System administrator for complex configurations 