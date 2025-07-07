import hashlib
from pathlib import Path

def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file to ensure its integrity.
    
    This function is central to the forensic pipeline, providing a way to
    create a verifiable fingerprint of any piece of data.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        SHA-256 hash of the file as a lowercase hex string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read the file in 4KB chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# Add other shared utility functions here as the project grows.
# For example, a function to load and validate a manifest file could go here.


