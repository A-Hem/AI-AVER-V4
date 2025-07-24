"""
Advanced metadata analysis for evidence verification
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import exifread
from PIL import Image
from PIL.ExifTags import TAGS
import magic
import hashlib
import imagehash

class MetadataAnalyzer:
    """Extract and analyze metadata for evidence verification"""
    
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.pdf', '.doc', '.docx'}
    
    def extract_comprehensive_metadata(self, file_path: str) -> Dict:
        """Extract all available metadata from file"""
        metadata = {
            'file_info': self._get_file_info(file_path),
            'exif_data': self._extract_exif_data(file_path),
            'hash_values': self._calculate_hashes(file_path),
            'perceptual_hash': self._calculate_perceptual_hash(file_path),
            'tampering_indicators': self._detect_tampering_indicators(file_path),
            'timeline_data': self._extract_timeline_data(file_path)
        }
        return metadata
    
    def _detect_tampering_indicators(self, file_path: str) -> Dict:
        """Detect potential tampering indicators"""
        indicators = {
            'metadata_inconsistencies': [],
            'timestamp_anomalies': [],
            'hash_mismatches': [],
            'exif_modifications': []
        }
        
        # Check for metadata inconsistencies
        try:
            with Image.open(file_path) as img:
                exif_dict = img._getexif()
                if exif_dict:
                    # Check for suspicious software entries
                    software_tag = next((v for k, v in exif_dict.items() 
                                       if TAGS.get(k) == 'Software'), None)
                    if software_tag and 'photoshop' in software_tag.lower():
                        indicators['exif_modifications'].append('Photoshop editing detected')
        except Exception as e:
            indicators['metadata_inconsistencies'].append(f'EXIF read error: {str(e)}')
        
        return indicators
