import argparse
import json
import logging
import sys
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

# Import the shared utility function
from src.utils import calculate_sha256

def setup_logging(log_path: Path):
    """
    Sets up a logger to output to both console and a file.
    This creates a permanent, auditable record of the preprocessing run.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Logging initialized.")

def validate_image(image_path: Path, min_resolution: int = 256) -> (bool, str):
    """
    Validates if a file is a usable image.
    
    Args:
        image_path: Path to the image file.
        min_resolution: The minimum height and width required.
        
    Returns:
        A tuple of (is_valid, reason_string).
    """
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return False, "File could not be read by OpenCV."
        
        h, w, _ = img.shape
        if h < min_resolution or w < min_resolution:
            return False, f"Image resolution {w}x{h} is below minimum of {min_resolution}x{min_resolution}."
            
        return True, "Image is valid."
    except Exception as e:
        return False, f"An error occurred during validation: {e}"

def process_device_images(device_id: str, source_dir: Path, output_dir: Path, params: dict) -> list:
    """
    Processes all images for a single device.
    
    Args:
        device_id: The identifier for the camera device.
        source_dir: The directory containing the raw images for this device.
        output_dir: The base directory to save processed noise patterns.
        params: A dictionary of processing parameters for forensic logging.
        
    Returns:
        A list of metadata dictionaries for each processed image.
    """
    device_output_dir = output_dir / device_id
    device_output_dir.mkdir(parents=True, exist_ok=True)
    
    image_files = list(source_dir.glob('*.jpg')) + list(source_dir.glob('*.jpeg')) + list(source_dir.glob('*.png'))
    logging.info(f"Found {len(image_files)} images for device '{device_id}'.")

    device_metadata = []

    for image_path in tqdm(image_files, desc=f"Processing {device_id}"):
        file_record = {
            "source_path": str(image_path),
            "device_id": device_id,
            "input_sha256": calculate_sha256(image_path)
        }

        is_valid, reason = validate_image(image_path, params['min_resolution'])
        if not is_valid:
            logging.warning(f"Skipping invalid image {image_path}: {reason}")
            file_record.update({"status": "rejected", "reason": reason})
            device_metadata.append(file_record)
            continue

        try:
            # 1. Standardization
            img_gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            img_standard = cv2.resize(
                img_gray, 
                (params['target_size'], params['target_size']), 
                interpolation=cv2.INTER_LANCZOS4
            )

            # 2. Denoising
            img_denoised = cv2.fastNlMeansDenoising(
                img_standard, 
                h=params['denoising_h'],
                templateWindowSize=7,
                searchWindowSize=21
            )

            # 3. Noise Residual Calculation
            noise_residual = img_standard.astype(np.float32) - img_denoised.astype(np.float32)
            
            # 4. Save processed pattern
            output_filename = f"{image_path.stem}.npy"
            output_path = device_output_dir / output_filename
            np.save(output_path, noise_residual)

            file_record.update({
                "status": "processed",
                "output_path": str(output_path),
                "output_sha256": calculate_sha256(output_path)
            })
            device_metadata.append(file_record)

        except Exception as e:
            logging.error(f"Failed to process {image_path}: {e}")
            file_record.update({"status": "error", "reason": str(e)})
            device_metadata.append(file_record)
            
    return device_metadata


def main():
    """Main preprocessing function."""
    parser = argparse.ArgumentParser(description="Forensic Preprocessing Pipeline for PRNU Analysis")
    parser.add_argument("--input_dir", type=str, required=True, help="Path to the root directory of raw images, organized by device folders.")
    parser.add_argument("--output_dir", type=str, required=True, help="Path to the directory to save processed data and logs.")
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    log_file = output_path / "_log.txt"
    setup_logging(log_file)
    
    run_params = {
        "target_size": 512,
        "min_resolution": 256,
        "denoising_h": 10,
        "interpolation_method": "LANCZOS4",
        "denoising_filter": "fastNlMeansDenoising"
    }
    logging.info(f"Starting preprocessing run with parameters: {json.dumps(run_params, indent=2)}")

    manifest = {
        "run_parameters": run_params,
        "processed_files": []
    }

    device_dirs = [d for d in input_path.iterdir() if d.is_dir()]
    if not device_dirs:
        logging.error(f"No device folders found in {input_path}. Please organize images in subdirectories.")
        sys.exit(1)

    logging.info(f"Found {len(device_dirs)} device directories to process.")

    for device_dir in device_dirs:
        device_id = device_dir.name
        device_metadata = process_device_images(device_id, device_dir, output_path, run_params)
        manifest["processed_files"].extend(device_metadata)

    manifest_path = output_path / "_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=4)
        
    logging.info(f"Preprocessing complete. Manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()

