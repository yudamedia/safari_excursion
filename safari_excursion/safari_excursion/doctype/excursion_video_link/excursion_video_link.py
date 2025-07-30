# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_video_link/excursion_video_link.py

import frappe
from frappe import _
from frappe.model.document import Document
import re

class ExcursionVideoLink(Document):
    """
    DocType controller for Excursion Video Link
    
    This controller handles video links for excursions,
    including URL validation and platform-specific formatting.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_video_details()
        self.validate_video_url()
        self.validate_duration()
        self.set_video_platform()
        self.validate_display_order()
    
    def validate_video_details(self):
        """Validate video title and basic details"""
        if not self.video_title:
            frappe.throw(_("Video Title is required"))
        
        if not self.video_url:
            frappe.throw(_("Video URL is required"))
    
    def validate_video_url(self):
        """Validate video URL format"""
        if self.video_url and not self.is_valid_video_url(self.video_url):
            frappe.throw(_("Please enter a valid video URL"))
    
    def validate_duration(self):
        """Validate video duration"""
        if self.duration_seconds is not None:
            if self.duration_seconds < 0:
                frappe.throw(_("Duration cannot be negative"))
            
            if self.duration_seconds > 7200:  # 2 hours max
                frappe.msgprint(_("Warning: Video duration seems very long"), alert=True)
    
    def validate_display_order(self):
        """Validate display order"""
        if self.display_order is not None and self.display_order < 0:
            frappe.throw(_("Display order cannot be negative"))
    
    def set_video_platform(self):
        """Auto-detect video platform from URL"""
        if self.video_url and not self.video_platform:
            self.video_platform = self.detect_video_platform(self.video_url)
    
    def is_valid_video_url(self, url):
        """Check if URL is a valid video URL"""
        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            return False
        
        # Platform-specific validation
        if self.detect_video_platform(url):
            return True
        
        return True  # Allow other URLs as valid
    
    def detect_video_platform(self, url):
        """Detect video platform from URL"""
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return "YouTube"
        elif 'vimeo.com' in url_lower:
            return "Vimeo"
        else:
            return "Direct Link"
    
    def get_video_id(self):
        """Extract video ID from URL"""
        if not self.video_url:
            return None
        
        if self.video_platform == "YouTube":
            return self.extract_youtube_id(self.video_url)
        elif self.video_platform == "Vimeo":
            return self.extract_vimeo_id(self.video_url)
        
        return None
    
    def extract_youtube_id(self, url):
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def extract_vimeo_id(self, url):
        """Extract Vimeo video ID from URL"""
        pattern = r'vimeo\.com/(\d+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def get_embed_url(self):
        """Get embed URL for the video"""
        video_id = self.get_video_id()
        
        if not video_id:
            return self.video_url
        
        if self.video_platform == "YouTube":
            return f"https://www.youtube.com/embed/{video_id}"
        elif self.video_platform == "Vimeo":
            return f"https://player.vimeo.com/video/{video_id}"
        
        return self.video_url
    
    def get_thumbnail_url(self):
        """Get thumbnail URL for the video"""
        video_id = self.get_video_id()
        
        if not video_id:
            return None
        
        if self.video_platform == "YouTube":
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        elif self.video_platform == "Vimeo":
            # Vimeo requires API call for thumbnails, return None for now
            return None
        
        return None
    
    def get_duration_display(self):
        """Get formatted duration display"""
        if not self.duration_seconds:
            return ""
        
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def get_video_summary(self):
        """Get a summary of the video"""
        summary = self.video_title
        
        if self.video_platform:
            summary += f" ({self.video_platform})"
        
        if self.duration_seconds:
            summary += f" - {self.get_duration_display()}"
        
        return summary
    
    def is_youtube_video(self):
        """Check if this is a YouTube video"""
        return self.video_platform == "YouTube"
    
    def is_vimeo_video(self):
        """Check if this is a Vimeo video"""
        return self.video_platform == "Vimeo"
    
    def is_direct_link(self):
        """Check if this is a direct link"""
        return self.video_platform == "Direct Link" 