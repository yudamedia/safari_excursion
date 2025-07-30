# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_gallery_image/excursion_gallery_image.py

import frappe
from frappe import _
from frappe.model.document import Document

class ExcursionGalleryImage(Document):
    """
    DocType controller for Excursion Gallery Image
    
    This controller handles gallery images for excursions,
    including image management, display ordering, and featured status.
    """
    
    def validate(self):
        """Validate document before saving"""
        if not self.image:
            frappe.throw(_("Image is required"))
        
        if not self.image_title:
            frappe.throw(_("Image Title is required"))
    
        if self.display_order is not None and self.display_order < 0:
            frappe.throw(_("Display order cannot be negative"))
    
    def get_image_summary(self):
        """Get a summary of the gallery image"""
        summary = self.image_title
        
        if self.is_featured:
            summary += " - FEATURED"
        
        if self.photographer:
            summary += f" - By {self.photographer}"
        
        return summary
    
    def is_featured_image(self):
        """Check if this is a featured image"""
        return bool(self.is_featured)
    
    def get_image_url(self):
        """Get the image URL"""
        if not self.image:
            return None
        
        return self.image
    
    def get_caption_display(self):
        """Get formatted caption display"""
        if not self.caption:
            return self.image_title
        
        return f"{self.image_title} - {self.caption}"
    
    def get_photographer_info(self):
        """Get photographer information"""
        if not self.photographer:
            return "Unknown photographer"
        
        return self.photographer
    
    def get_display_priority(self):
        """Get display priority for sorting"""
        if self.is_featured:
            return 1  # Highest priority
        elif self.display_order:
            return self.display_order
        else:
            return 999  # Lowest priority
    
    def get_image_info(self):
        """Get comprehensive image information"""
        return {
            "title": self.image_title,
            "url": self.get_image_url(),
            "caption": self.caption,
            "photographer": self.photographer,
            "is_featured": self.is_featured,
            "display_order": self.display_order,
            "priority": self.get_display_priority()
        }
    
    def mark_as_featured(self):
        """Mark image as featured"""
        self.is_featured = 1
        self.save()
        frappe.msgprint(_("Image marked as featured"))
    
    def unmark_as_featured(self):
        """Unmark image as featured"""
        self.is_featured = 0
        self.save()
        frappe.msgprint(_("Image unmarked as featured"))
    
    def has_caption(self):
        """Check if image has a caption"""
        return bool(self.caption)
    
    def has_photographer(self):
        """Check if image has photographer info"""
        return bool(self.photographer)
    
    def get_image_type(self):
        """Get image type classification"""
        if self.is_featured:
            return "Featured"
        elif self.display_order and self.display_order <= 5:
            return "Primary"
        else:
            return "Gallery" 