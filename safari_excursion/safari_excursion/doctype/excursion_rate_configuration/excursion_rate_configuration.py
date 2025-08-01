import frappe
from frappe.model.document import Document

class ExcursionRateConfiguration(Document):
    def validate(self):
        self.validate_child_age_brackets()
        self.validate_group_discount_tiers()
    
    def validate_child_age_brackets(self):
        if self.has_child_rates and self.child_age_brackets:
            # Check for overlapping age brackets
            age_brackets = []
            for bracket in self.child_age_brackets:
                age_brackets.append({
                    'min_age': bracket.min_age,
                    'max_age': bracket.max_age
                })
            
            # Sort by min_age
            age_brackets.sort(key=lambda x: x['min_age'])
            
            # Check for gaps or overlaps
            for i in range(len(age_brackets) - 1):
                current = age_brackets[i]
                next_bracket = age_brackets[i + 1]
                
                if current['max_age'] + 1 != next_bracket['min_age']:
                    frappe.throw(f"Age brackets must be consecutive without gaps. "
                               f"Current bracket ends at {current['max_age']}, "
                               f"next bracket starts at {next_bracket['min_age']}")
    
    def validate_group_discount_tiers(self):
        if self.has_group_discounts and self.group_discount_tiers:
            # Check for overlapping group sizes
            group_sizes = []
            for tier in self.group_discount_tiers:
                group_sizes.append({
                    'min_size': tier.min_group_size,
                    'max_size': tier.max_group_size,
                    'discount_percentage': tier.discount_percentage
                })
            
            # Sort by min_size
            group_sizes.sort(key=lambda x: x['min_size'])
            
            # Check for gaps or overlaps
            for i in range(len(group_sizes) - 1):
                current = group_sizes[i]
                next_tier = group_sizes[i + 1]
                
                if current['max_size'] + 1 != next_tier['min_size']:
                    frappe.throw(f"Group size tiers must be consecutive without gaps. "
                               f"Current tier ends at {current['max_size']}, "
                               f"next tier starts at {next_tier['min_size']}")
    
    def on_submit(self):
        # Create rate tables if they don't exist
        self.create_rate_tables()
    
    def create_rate_tables(self):
        """Create local and international rate tables for this configuration"""
        # This would be implemented to create the actual rate tables
        # based on the configuration
        pass 