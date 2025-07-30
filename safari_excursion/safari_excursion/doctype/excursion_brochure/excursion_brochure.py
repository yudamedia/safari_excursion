# ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_brochure/excursion_brochure.py

import frappe
from frappe import _
from frappe.model.document import Document
import os
import re

class ExcursionBrochure(Document):
    """
    DocType controller for Excursion Brochure
    
    This controller handles brochure files for excursions,
    including file management, type validation, and language support.
    """
    
    def validate(self):
        """Validate document before saving"""
        self.validate_brochure_details()
        self.validate_file_information()
        self.validate_language()
        self.set_file_type_from_filename()
        self.calculate_file_size()
    
    def validate_brochure_details(self):
        """Validate brochure title and basic details"""
        if not self.brochure_title:
            frappe.throw(_("Brochure Title is required"))
        
        if not self.brochure_file:
            frappe.throw(_("Brochure File is required"))
    
    def validate_file_information(self):
        """Validate file information"""
        if self.file_size_mb is not None and self.file_size_mb < 0:
            frappe.throw(_("File size cannot be negative"))
        
        if self.file_size_mb is not None and self.file_size_mb > 100:
            frappe.msgprint(_("Warning: File size is very large ({0} MB)").format(self.file_size_mb), alert=True)
    
    def validate_language(self):
        """Validate language selection"""
        valid_languages = [
            "English", "Swahili", "French", "German", "Spanish", "Italian", "Other"
        ]
        
        if self.language and self.language not in valid_languages:
            frappe.throw(_("Invalid language selected"))
    
    def set_file_type_from_filename(self):
        """Auto-detect file type from filename if not set"""
        if self.brochure_file and not self.file_type:
            self.file_type = self.detect_file_type(self.brochure_file)
    
    def detect_file_type(self, filename):
        """Detect file type from filename extension"""
        if not filename:
            return "Other"
        
        # Extract file extension
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Map extensions to file types
        extension_map = {
            '.pdf': 'PDF',
            '.doc': 'DOC',
            '.docx': 'DOCX',
            '.jpg': 'JPG',
            '.jpeg': 'JPG',
            '.png': 'PNG',
            '.gif': 'Other',
            '.bmp': 'Other',
            '.txt': 'Other'
        }
        
        return extension_map.get(file_extension, 'Other')
    
    def calculate_file_size(self):
        """Calculate file size from attached file"""
        if self.brochure_file:
            try:
                file_path = frappe.get_doc("File", {"file_url": self.brochure_file}).get_full_path()
                if os.path.exists(file_path):
                    file_size_bytes = os.path.getsize(file_path)
                    self.file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
            except:
                # If file doesn't exist or can't be accessed, leave file_size_mb as is
                pass
    
    def get_brochure_summary(self):
        """Get a summary of the brochure"""
        summary = self.brochure_title
        
        if self.file_type:
            summary += f" ({self.file_type})"
        
        if self.language and self.language != "English":
            summary += f" - {self.language}"
        
        if self.file_size_mb:
            summary += f" - {self.file_size_mb} MB"
        
        return summary
    
    def get_file_info(self):
        """Get formatted file information"""
        file_info = []
        
        if self.file_type:
            file_info.append(f"Type: {self.file_type}")
        
        if self.language:
            file_info.append(f"Language: {self.language}")
        
        if self.file_size_mb:
            file_info.append(f"Size: {self.file_size_mb} MB")
        
        return " | ".join(file_info) if file_info else "No file info"
    
    def get_language_icon(self):
        """Get appropriate icon for the language"""
        language_icons = {
            "English": "🇺🇸",
            "Swahili": "🇹🇿",
            "French": "🇫🇷",
            "German": "🇩🇪",
            "Spanish": "🇪🇸",
            "Italian": "🇮🇹",
            "Other": "🌐"
        }
        
        return language_icons.get(self.language, "🌐")
    
    def get_file_type_icon(self):
        """Get appropriate icon for the file type"""
        type_icons = {
            "PDF": "📄",
            "DOC": "📝",
            "DOCX": "📝",
            "JPG": "🖼️",
            "PNG": "🖼️",
            "Other": "📎"
        }
        
        return type_icons.get(self.file_type, "📎")
    
    def is_pdf_file(self):
        """Check if this is a PDF file"""
        return self.file_type == "PDF"
    
    def is_document_file(self):
        """Check if this is a document file"""
        return self.file_type in ["DOC", "DOCX"]
    
    def is_image_file(self):
        """Check if this is an image file"""
        return self.file_type in ["JPG", "PNG"]
    
    def is_english_language(self):
        """Check if this is in English"""
        return self.language == "English"
    
    def is_local_language(self):
        """Check if this is in a local language (Swahili)"""
        return self.language == "Swahili"
    
    def get_download_url(self):
        """Get download URL for the brochure file"""
        if self.brochure_file:
            return f"/api/method/frappe.utils.file_manager.download_file?file_url={self.brochure_file}"
        return None
    
    def get_file_extension(self):
        """Get file extension from filename"""
        if not self.brochure_file:
            return ""
        
        return os.path.splitext(self.brochure_file)[1].lower()
    
    def is_large_file(self):
        """Check if file is considered large (>10MB)"""
        return self.file_size_mb and self.file_size_mb > 10
    
    def get_file_size_display(self):
        """Get formatted file size display"""
        if not self.file_size_mb:
            return "Size unknown"
        
        if self.file_size_mb < 1:
            return f"{self.file_size_mb * 1024:.0f} KB"
        else:
            return f"{self.file_size_mb} MB"
    
    def validate_file_access(self):
        """Validate that the file is accessible"""
        if self.brochure_file:
            try:
                file_doc = frappe.get_doc("File", {"file_url": self.brochure_file})
                if not file_doc.exists():
                    frappe.throw(_("Brochure file is not accessible"))
            except:
                frappe.throw(_("Invalid brochure file reference")) 