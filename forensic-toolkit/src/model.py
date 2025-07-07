
import torch
import torch.nn as nn
import torchvision
from typing import Optional, Tuple, Union


class PRNUModel(nn.Module):
    """
    A PyTorch model for device fingerprinting using PRNU analysis.
    The model uses a ResNet50 backbone to extract features and custom heads
    to generate a device signature and compare signature pairs.
    """
    
    def __init__(self):
        super(PRNUModel, self).__init__()

        # 1. Backbone: Use a pretrained ResNet50 from torchvision.
        # We will remove the final classification layer to use it as a feature extractor.
        self.backbone = torchvision.models.resnet50(weights='IMAGENET1K_V1')
        self.backbone.fc = nn.Identity()  # Replaces the final layer with an identity layer.

        # 2. Signature Head: Processes ResNet's output to create a compact device signature.
        # The input dimension is 2048, which is the output size of ResNet50.
        self.prnu_extractor = nn.Sequential(
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Linear(512, 256)  # Final 256-dimensional device signature vector
        )

        # 3. Similarity Head: Takes two concatenated signatures (256 + 256 = 512)
        # and outputs a single similarity score between 0 and 1.
        self.similarity_head = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, x1: torch.Tensor, x2: Optional[torch.Tensor] = None) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        """
        Defines the forward pass. Supports two modes:
        - Signature mode: If only x1 is provided, returns its signature.
        - Comparison mode: If x1 and x2 are provided, returns their similarity score
          and individual signatures.
        
        Args:
            x1 (torch.Tensor): First input image tensor
            x2 (Optional[torch.Tensor]): Second input image tensor for comparison
            
        Returns:
            Union[torch.Tensor, Tuple]: Either signature tensor or (similarity, signature1, signature2)
        """
        features1 = self.backbone(x1)
        signature1 = self.prnu_extractor(features1)

        # If only one image is provided, return its signature.
        if x2 is None:
            return signature1

        # If two images are provided, process the second image and compare.
        features2 = self.backbone(x2)
        signature2 = self.prnu_extractor(features2)

        combined_signatures = torch.cat([signature1, signature2], dim=1)
        similarity = self.similarity_head(combined_signatures)

        return similarity, signature1, signature2
    
    def extract_signature(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract device signature from input image.
        
        Args:
            x (torch.Tensor): Input image tensor
            
        Returns:
            torch.Tensor: 256-dimensional device signature
        """
        with torch.no_grad():
            features = self.backbone(x)
            signature = self.prnu_extractor(features)
        return signature
    
    def compute_similarity(self, sig1: torch.Tensor, sig2: torch.Tensor) -> torch.Tensor:
        """
        Compute similarity between two pre-computed signatures.
        
        Args:
            sig1 (torch.Tensor): First signature tensor
            sig2 (torch.Tensor): Second signature tensor
            
        Returns:
            torch.Tensor: Similarity score between 0 and 1
        """
        combined = torch.cat([sig1, sig2], dim=1)
        return self.similarity_head(combined)
