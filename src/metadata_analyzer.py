import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Third-party libraries - install with: pip install Pillow exifread python-magic imagehash
import exifread
from PIL import Image
import magic
import hashlib
import imagehash
import re

class MetadataAnalyzer:
    """Extract and analyze metadata for evidence verification."""
    
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.tiff', '.png'}
        self.editing_software_keywords = [
            'photoshop', 'gimp', 'lightroom', 'snapseed', 'affinity', 'corel', 
            'paint.net', 'capture one'
        ]
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract and analyze comprehensive metadata from a file. This is the main public method.

        Args:
            file_path: The path to the file to be analyzed.

        Returns:
            A dictionary containing the extracted and analyzed metadata.
        """
        if not Path(file_path).is_file():
            raise FileNotFoundError(f"File not found at: {file_path}")

        file_extension = Path(file_path).suffix.lower()
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}. Supported formats are {self.supported_formats}")

        # 1. Extract all raw metadata first
        metadata = {
            'file_info': self._get_file_info(file_path),
            'exif_data': self._extract_exif_data(file_path),
            'hash_values': self._calculate_hashes(file_path),
            'perceptual_hash': self._calculate_perceptual_hash(file_path),
        }
        
        # 2. Perform analysis on the collected metadata
        metadata['tampering_analysis'] = self._detect_tampering_indicators(metadata)
        
        return metadata
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Extracts basic file system information."""
        try:
            stat = os.stat(file_path)
            return {
                'file_name': os.path.basename(file_path),
                'file_path': os.path.abspath(file_path),
                'file_size_bytes': stat.st_size,
                'creation_time_os': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modification_time_os': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'file_type_magic': magic.from_file(file_path)
            }
        except Exception as e:
            return {'error': str(e)}

    def _extract_exif_data(self, file_path: str) -> Dict[str, Any]:
        """Extracts EXIF data using the 'exifread' library for more detail."""
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=True)
                if not tags:
                    return {'status': 'No EXIF information found.'}

                exif_data = {}
                for tag, value in tags.items():
                    if tag not in ('JPEGThumbnail', 'TIFFThumbnail'): # Exclude bulky thumbnails
                        exif_data[tag] = str(value)
                return exif_data
        except Exception as e:
            return {'error': str(e)}

    def _calculate_hashes(self, file_path: str) -> Dict[str, str]:
        """Calculates cryptographic hashes of the file for integrity verification."""
        hashes = {}
        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
                hashes['md5'] = hashlib.md5(file_bytes).hexdigest()
                hashes['sha256'] = hashlib.sha256(file_bytes).hexdigest()
        except Exception as e:
            return {'error': str(e)}
        return hashes

    def _calculate_perceptual_hash(self, file_path: str) -> Optional[str]:
        """Calculates the perceptual hash (pHash) of an image to find similar images."""
        try:
            with Image.open(file_path) as img:
                return str(imagehash.phash(img))
        except Exception:
            return None # Fails gracefully if the file is not an image

    def _detect_tampering_indicators(self, all_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes collected metadata for signs of tampering by looking for inconsistencies.
        This is the core analysis engine.
        """
        issues = []
        exif_data = all_metadata.get('exif_data', {})
        file_info = all_metadata.get('file_info', {})

        # Indicator 1: Check for known editing software
        software = exif_data.get('Image Software')
        if software:
            for keyword in self.editing_software_keywords:
                if re.search(keyword, software, re.IGNORECASE):
                    issues.append({
                        'indicator': 'Image Editing Software Detected',
                        'description': f"The 'Software' EXIF tag is '{software}', which indicates potential editing.",
                        'severity': 'Low'
                    })
                    break

        # Indicator 2: Compare EXIF creation date with file system modification date
        exif_dt_str = exif_data.get('EXIF DateTimeOriginal')
        file_mod_dt_str = file_info.get('modification_time_os')
        if exif_dt_str and file_mod_dt_str:
            try:
                # EXIF datetime format is 'YYYY:MM:DD HH:MM:SS'
                exif_dt = datetime.strptime(exif_dt_str, '%Y:%m:%d %H:%M:%S')
                file_mod_dt = datetime.fromisoformat(file_mod_dt_str)
                
                # If the file was modified more than a minute after the picture was taken, flag it.
                if file_mod_dt > exif_dt + timedelta(seconds=60):
                     issues.append({
                        'indicator': 'Timestamp Mismatch',
                        'description': (f"The file was modified on {file_mod_dt}, which is significantly "
                                      f"later than when the photo was taken ({exif_dt})."),
                        'severity': 'High'
                    })
            except (ValueError, TypeError):
                pass # Could not parse dates, skip this check

        # Indicator 3: Check for missing critical EXIF tags for an original image
        critical_tags = ['EXIF DateTimeOriginal', 'Image Make', 'Image Model']
        missing_tags = [tag for tag in critical_tags if tag not in exif_data]
        if missing_tags:
            issues.append({
                'indicator': 'Missing Critical Camera Tags',
                'description': f"Key EXIF tags are missing: {', '.join(missing_tags)}. This can suggest metadata stripping.",
                'severity': 'Medium'
            })

        # Final Summary
        summary = {
            'potential_issues_found': len(issues),
            'summary_text': 'No significant tampering indicators found.' if not issues else f"{len(issues)} potential indicator(s) found.",
            'details': issues
        }
        return summary

