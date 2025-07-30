import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionItineraryItem(Document):
    def validate(self):
        if not self.time_slot:
            frappe.throw(_("Time Slot is required"))
        if not self.activity_title:
            frappe.throw(_("Activity Title is required"))
        if self.duration_minutes is not None and self.duration_minutes <= 0:
            frappe.throw(_("Duration must be greater than 0"))
    
    def get_itinerary_summary(self):
        summary = f"{self.time_slot} - {self.activity_title}"
        if self.duration_minutes:
            summary += f" ({self.duration_minutes} min)"
        if self.is_optional:
            summary += " - OPTIONAL"
        return summary
    
    def is_optional_activity(self):
        return bool(self.is_optional)
    
    def get_duration_display(self):
        if not self.duration_minutes:
            return "Duration not specified"
        
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours} hours"
        else:
            return f"{minutes} minutes"
    
    def get_activity_type(self):
        if self.is_optional:
            return "Optional"
        else:
            return "Required" 