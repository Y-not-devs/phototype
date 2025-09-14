"""
PDF Excerpt Extraction Service
Extracts text snippets from PDF that correspond to JSON fields
"""
import os
import re
import json
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

class PDFExcerptExtractor:
    def __init__(self, pdf_path: str, json_data: dict):
        self.pdf_path = pdf_path
        self.json_data = json_data
        self.pdf_text = ""
        self.excerpts = {}
        
    def extract_pdf_text(self) -> str:
        """Extract all text from PDF"""
        if not pdfplumber:
            print("Warning: pdfplumber not installed. Install with: pip install pdfplumber")
            return ""
            
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                self.pdf_text = "\n".join(text_parts)
                return self.pdf_text
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def find_text_excerpt(self, search_text: str, context_length: int = 100) -> Optional[str]:
        """Find excerpt from PDF text that contains the search text"""
        if not search_text or not self.pdf_text:
            return None
            
        # Clean and normalize text for searching
        clean_search = re.sub(r'\s+', ' ', str(search_text).strip())
        clean_pdf = re.sub(r'\s+', ' ', self.pdf_text)
        
        # Try exact match first
        if clean_search.lower() in clean_pdf.lower():
            start_idx = clean_pdf.lower().find(clean_search.lower())
            start = max(0, start_idx - context_length)
            end = min(len(clean_pdf), start_idx + len(clean_search) + context_length)
            excerpt = clean_pdf[start:end].strip()
            return f"...{excerpt}..." if start > 0 or end < len(clean_pdf) else excerpt
        
        # Try partial matching for complex strings
        words = clean_search.split()
        if len(words) > 1:
            # Try progressively smaller word combinations
            for i in range(len(words), 0, -1):
                for j in range(len(words) - i + 1):
                    partial = " ".join(words[j:j+i])
                    if len(partial) > 10 and partial.lower() in clean_pdf.lower():
                        start_idx = clean_pdf.lower().find(partial.lower())
                        start = max(0, start_idx - context_length)
                        end = min(len(clean_pdf), start_idx + len(partial) + context_length)
                        excerpt = clean_pdf[start:end].strip()
                        return f"...{excerpt}..." if start > 0 or end < len(clean_pdf) else excerpt
        
        return None
    
    def extract_field_excerpts(self, fields: dict, prefix: str = "") -> dict:
        """Recursively extract excerpts for all fields"""
        excerpts = {}
        
        for key, value in fields.items():
            field_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recursively process nested objects
                nested_excerpts = self.extract_field_excerpts(value, field_path)
                excerpts.update(nested_excerpts)
            elif isinstance(value, list):
                # Process list items
                for i, item in enumerate(value):
                    item_path = f"{field_path}[{i}]"
                    if isinstance(item, dict):
                        nested_excerpts = self.extract_field_excerpts(item, item_path)
                        excerpts.update(nested_excerpts)
                    else:
                        excerpt = self.find_text_excerpt(str(item))
                        if excerpt:
                            excerpts[item_path] = {
                                'value': str(item),
                                'excerpt': excerpt,
                                'field_type': 'array_item'
                            }
            else:
                # Process leaf values
                excerpt = self.find_text_excerpt(str(value))
                if excerpt:
                    excerpts[field_path] = {
                        'value': str(value),
                        'excerpt': excerpt,
                        'field_type': type(value).__name__
                    }
        
        return excerpts
    
    def generate_excerpts(self) -> dict:
        """Generate all excerpts for the JSON data"""
        if not self.pdf_text:
            self.extract_pdf_text()
        
        if not self.pdf_text:
            return {}
        
        # Extract excerpts for the fields
        if 'fields' in self.json_data:
            self.excerpts = self.extract_field_excerpts(self.json_data['fields'])
        else:
            # If no 'fields' key, process the entire data structure
            self.excerpts = self.extract_field_excerpts(self.json_data)
        
        return self.excerpts

def extract_pdf_excerpts(pdf_path: str, json_data: dict) -> dict:
    """Main function to extract PDF excerpts"""
    extractor = PDFExcerptExtractor(pdf_path, json_data)
    return extractor.generate_excerpts()