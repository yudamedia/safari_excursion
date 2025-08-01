import frappe
from datetime import date
from typing import List, Dict, Optional

class ExcursionPricingCalculator:
    def __init__(self, excursion_package: str, excursion_date: date, residence_type: str = "International"):
        self.excursion_package = excursion_package
        self.excursion_date = excursion_date
        self.residence_type = residence_type
        self.rate_config = self._get_rate_configuration()
    
    def _get_rate_configuration(self) -> Optional[Dict]:
        """Get the rate configuration for the excursion package"""
        try:
            rate_config = frappe.get_doc("Excursion Rate Configuration", 
                                        {"excursion_package": self.excursion_package})
            return rate_config.as_dict()
        except frappe.DoesNotExistError:
            return None
    
    def _get_season(self) -> Optional[str]:
        """Get the season for the excursion date"""
        try:
            seasons = frappe.get_all("Excursion Season", 
                                   filters={"is_active": 1},
                                   fields=["name", "start_date", "end_date"])
            
            for season in seasons:
                if season.start_date <= self.excursion_date <= season.end_date:
                    return season.name
            return None
        except Exception:
            return None
    
    def _get_base_rate(self, season: str) -> Optional[Dict]:
        """Get the base rate for the season and residence type"""
        try:
            if self.residence_type == "Local":
                rate_table = "Excursion Local Per Person Rate"
                currency = "KES"
            else:
                rate_table = "Excursion International Per Person Rate"
                currency = "USD"
            
            rates = frappe.get_all(rate_table,
                                 filters={"excursion_package": self.excursion_package,
                                         "season": season},
                                 fields=["adult_rate"])
            
            if rates:
                return {
                    "adult_rate": rates[0].adult_rate,
                    "currency": currency
                }
            return None
        except Exception:
            return None
    
    def calculate_pricing(self, adults: int, children: List[int] = None, group_size: int = None) -> Dict:
        """Calculate the total pricing for the excursion"""
        if not self.rate_config:
            return {"error": "No rate configuration found"}
        
        season = self._get_season()
        if not season:
            frappe.throw(f"No season found for date {self.excursion_date}")
        
        base_rate = self._get_base_rate(season)
        if not base_rate:
            return {"error": "No base rate found for the season"}
        
        adult_total = adults * base_rate["adult_rate"]
        child_total = 0
        
        if children:
            for age in children:
                child_rate = self._get_child_rate(age, base_rate)
                child_total += child_rate
        
        # Calculate final total
        total = adult_total + child_total
        
        return {
            "currency": base_rate["currency"],
            "adult_total": adult_total,
            "child_total": child_total,
            "total": total
        }
    
    def _get_child_rate(self, age: int, base_rate: Dict) -> float:
        """Get the child rate for a specific age"""
        if not self.rate_config.get("has_child_rates"):
            return 0.0
        
        for bracket in self.rate_config.get("child_age_brackets", []):
            if bracket.min_age <= age <= bracket.max_age:
                if self.rate_config.get("child_rate_type") == "Fixed Rate":
                    return bracket.rate_value
                elif self.rate_config.get("child_rate_type") == "Percentage of Adult Rate":
                    return base_rate.get("adult_rate", 0) * (bracket.rate_value / 100)
        
        return 0.0

def get_excursion_pricing(excursion_package: str, excursion_date: date, 
                         adults: int, children: List[int] = None,
                         residence_type: str = "International", 
                         group_size: int = None) -> Dict:
    """Convenience function to get excursion pricing"""
    calculator = ExcursionPricingCalculator(excursion_package, excursion_date, residence_type)
    return calculator.calculate_pricing(adults, children, group_size)
