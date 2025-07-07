
import torch
from torch.utils.data import Dataset
from PIL import Image
import json
import os
from typing import Optional, Callable, Tuple


class PRNUDataset(Dataset):
    """
    Dataset class for PRNU-based device identification using triplets.
    
    This dataset loads triplets of images (anchor, positive, negative) where:
    - Anchor and positive are from the same device
    - Negative is from a different device
    """
    
    def __init__(self, json_path: str, transform: Optional[Callable] = None):
        """
        Initialize the PRNUDataset.
        
        Args:
            json_path (str): Path to the JSON file containing triplet information
            transform (Optional[Callable]): Optional transform to be applied to images
        """
        self.json_path = json_path
        self.transform = transform
        
        # Load triplets from JSON file
        with open(json_path, 'r') as f:
            self.triplets = json.load(f)
        
        print(f"Loaded {len(self.triplets)} triplets from {json_path}")
    
    def __len__(self) -> int:
        """
        Return the total number of triplets in the dataset.
        
        Returns:
            int: Number of triplets
        """
        return len(self.triplets)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Get a triplet of images at the given index.
        
        Args:
            idx (int): Index of the triplet to retrieve
            
        Returns:
            Tuple[torch.Tensor, torch.Tensor, torch.Tensor]: (anchor, positive, negative) images
        """
        if idx >= len(self.triplets):
            raise IndexError(f"Index {idx} out of range for dataset of size {len(self.triplets)}")
        
        # Get triplet paths
        triplet = self.triplets[idx]
        anchor_path = triplet['anchor']
        positive_path = triplet['positive']
        negative_path = triplet['negative']
        
        # Load images and convert to RGB
        try:
            anchor_img = Image.open(anchor_path).convert('RGB')
            positive_img = Image.open(positive_path).convert('RGB')
            negative_img = Image.open(negative_path).convert('RGB')
        except Exception as e:
            raise RuntimeError(f"Error loading images for triplet {idx}: {e}")
        
        # Apply transforms if provided
        if self.transform is not None:
            anchor_img = self.transform(anchor_img)
            positive_img = self.transform(positive_img)
            negative_img = self.transform(negative_img)
        
        return anchor_img, positive_img, negative_img
    
    def get_triplet_info(self, idx: int) -> dict:
        """
        Get metadata information for a triplet.
        
        Args:
            idx (int): Index of the triplet
            
        Returns:
            dict: Triplet metadata including paths and device information
        """
        if idx >= len(self.triplets):
            raise IndexError(f"Index {idx} out of range for dataset of size {len(self.triplets)}")
        
        return self.triplets[idx]
