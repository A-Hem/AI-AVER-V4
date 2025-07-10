"""
Advanced tamper detection using multiple techniques
"""
import cv2
import numpy as np
from scipy import ndimage
from skimage import filters, measure
import torch
import torch.nn as nn
from torchvision import transforms

class TamperDetector:
    """Multi-modal tamper detection system"""
    
    def __init__(self):
        self.ela_quality = 90  # JPEG quality for ELA analysis
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def analyze_image_authenticity(self, image_path: str) -> Dict:
        """Comprehensive image authenticity analysis"""
        results = {
            'ela_analysis': self._error_level_analysis(image_path),
            'noise_analysis': self._noise_pattern_analysis(image_path),
            'compression_analysis': self._compression_analysis(image_path),
            'copy_move_detection': self._detect_copy_move(image_path),
            'splicing_detection': self._detect_splicing(image_path)
        }
        
        # Calculate overall authenticity score
        results['authenticity_score'] = self._calculate_authenticity_score(results)
        return results
    
    def _error_level_analysis(self, image_path: str) -> Dict:
        """Perform Error Level Analysis (ELA)"""
        original = cv2.imread(image_path)
        
        # Save image at specified quality
        temp_path = 'temp_ela.jpg'
        cv2.imwrite(temp_path, original, [cv2.IMWRITE_JPEG_QUALITY, self.ela_quality])
        
        # Load compressed image
        compressed = cv2.imread(temp_path)
        
        # Calculate difference
        diff = cv2.absdiff(original, compressed)
        
        # Enhance difference for visualization
        ela_image = cv2.convertScaleAbs(diff, alpha=10)
        
        # Calculate ELA metrics
        ela_variance = np.var(ela_image)
        ela_mean = np.mean(ela_image)
        
        # Clean up
        os.remove(temp_path)
        
        return {
            'ela_variance': float(ela_variance),
            'ela_mean': float(ela_mean),
            'suspicious_regions': self._identify_suspicious_regions(ela_image)
        }
