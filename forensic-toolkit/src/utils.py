import hashlib
import logging
from pathlib import Path
from typing import Union


def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file to ensure its integrity.

    This function is central to the forensic pipeline, providing a way to
    create a verifiable fingerprint of any piece of data.

    Args:
        file_path: Path to the file.

    Returns:
        [span_0](start_span)SHA-256 hash of the file as a lowercase hex string.[span_0](end_span)
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read the file in 4KB chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        logging.Logger: Configured logger
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def ensure_dir_exists(dir_path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't

    Args:
        dir_path: Path to directory

    Returns:
        Path: Path object to the directory
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_project_root() -> Path:
    """
    Get the project root directory

    Returns:
        Path: Path to project root
    """
    return Path(__file__).parent.parent

