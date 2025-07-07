import os
import argparse
import random
import json
from pathlib import Path
import logging
from typing import List, Tuple, Dict
from collections import defaultdict

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.utils import setup_logging, ensure_dir_exists, get_project_root


def collect_images_by_device(data_dir: str) -> Dict[str, List[str]]:
    """
    Collect images organized by device ID
    
    Args:
        data_dir (str): Directory containing training data
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping device IDs to image paths
    """
    logger = logging.getLogger(__name__)
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory {data_dir} not found")
    
    device_images = defaultdict(list)
    
    # Assume directory structure: data_dir/device_id/images/
    for device_dir in data_path.iterdir():
        if device_dir.is_dir():
            device_id = device_dir.name
            
            # Look for images in the device directory and subdirectories
            for img_path in device_dir.rglob("*"):
                if img_path.is_file() and img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                    device_images[device_id].append(str(img_path))
    
    logger.info(f"Found {len(device_images)} devices with images")
    for device_id, images in device_images.items():
        logger.info(f"Device {device_id}: {len(images)} images")
    
    return dict(device_images)


def generate_triplet(device_images: Dict[str, List[str]], anchor_device: str) -> Tuple[str, str, str]:
    """
    Generate a single triplet (anchor, positive, negative)
    
    Args:
        device_images: Dictionary mapping device IDs to image paths
        anchor_device: Device ID for anchor and positive samples
        
    Returns:
        Tuple[str, str, str]: (anchor_path, positive_path, negative_path)
    """
    # Select anchor and positive from same device
    device_imgs = device_images[anchor_device]
    if len(device_imgs) < 2:
        raise ValueError(f"Device {anchor_device} has less than 2 images")
    
    anchor_img, positive_img = random.sample(device_imgs, 2)
    
    # Select negative from different device
    other_devices = [d for d in device_images.keys() if d != anchor_device]
    if not other_devices:
        raise ValueError("Need at least 2 different devices for triplet generation")
    
    negative_device = random.choice(other_devices)
    negative_img = random.choice(device_images[negative_device])
    
    return anchor_img, positive_img, negative_img


def generate_triplets(data_dir: str, output_dir: str, num_triplets: int = 1000) -> None:
    """
    Generate triplets for training
    
    Args:
        data_dir (str): Directory containing training data
        output_dir (str): Directory to save generated triplets
        num_triplets (int): Number of triplets to generate
    """
    logger = setup_logging()
    logger.info(f"Generating {num_triplets} triplets from {data_dir}")
    
    # Collect images by device
    device_images = collect_images_by_device(data_dir)
    
    if len(device_images) < 2:
        raise ValueError("Need at least 2 devices for triplet generation")
    
    # Filter devices with at least 2 images
    valid_devices = {k: v for k, v in device_images.items() if len(v) >= 2}
    if len(valid_devices) < 2:
        raise ValueError("Need at least 2 devices with 2+ images each")
    
    logger.info(f"Using {len(valid_devices)} devices for triplet generation")
    
    # Generate triplets
    triplets = []
    device_list = list(valid_devices.keys())
    
    for i in range(num_triplets):
        # Select anchor device randomly
        anchor_device = random.choice(device_list)
        
        try:
            triplet = generate_triplet(valid_devices, anchor_device)
            triplets.append({
                'triplet_id': i,
                'anchor': triplet[0],
                'positive': triplet[1],
                'negative': triplet[2],
                'anchor_device': anchor_device
            })
            
            if (i + 1) % 100 == 0:
                logger.info(f"Generated {i + 1}/{num_triplets} triplets")
                
        except ValueError as e:
            logger.warning(f"Failed to generate triplet {i}: {e}")
            continue
    
    # Save triplets
    output_path = ensure_dir_exists(output_dir)
    triplets_file = output_path / "triplets.json"
    
    with open(triplets_file, 'w') as f:
        json.dump(triplets, f, indent=2)
    
    logger.info(f"Generated {len(triplets)} triplets saved to {triplets_file}")
    
    # Save summary statistics
    stats_file = output_path / "triplet_stats.json"
    device_counts = defaultdict(int)
    for triplet in triplets:
        device_counts[triplet['anchor_device']] += 1
    
    stats = {
        'total_triplets': len(triplets),
        'num_devices': len(valid_devices),
        'device_distribution': dict(device_counts),
        'generation_params': {
            'requested_triplets': num_triplets,
            'data_directory': data_dir
        }
    }
    
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Statistics saved to {stats_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate triplets for training")
    parser.add_argument("--data_dir", type=str, required=True,
                       help="Directory containing training data")
    parser.add_argument("--output_dir", type=str, required=True,
                       help="Directory to save generated triplets")
    parser.add_argument("--num_triplets", type=int, default=1000,
                       help="Number of triplets to generate")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    random.seed(args.seed)
    
    generate_triplets(args.data_dir, args.output_dir, args.num_triplets)


if __name__ == "__main__":
    main()
