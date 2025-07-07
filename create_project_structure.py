# create_project_structure.py
import os
from pathlib import Path

# Define the root directory name
ROOT_DIR_NAME = "forensic-toolkit"
root_dir = Path(ROOT_DIR_NAME)

# Define the directory structure
dirs_to_create = [
    root_dir / "data" / "raw",
    root_dir / "data" / "temp",
    root_dir / "frontend" / "static",
    root_dir / "models",
    root_dir / "src",
]

# Define the empty files to create
files_to_create = [
    root_dir / "frontend" / "index.html",
    root_dir / "frontend" / "static" / "style.css",
    root_dir / "src" / "__init__.py",
    root_dir / "src" / "preprocess.py",
    root_dir / "src" / "train.py",
    root_dir / "src" / "inference.py",
    root_dir / "src" / "model.py",
    root_dir / "src" / "dataset.py",
    root_dir / "src" / "utils.py",
    root_dir / "src" / "metadata_analyzer.py",
    root_dir / "main.py",
    root_dir / "requirements.txt",
]

# Content for the .gitignore file
gitignore_content = """
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/

# Data and Models - These should not be tracked by Git
data/
models/

# OS-specific
.DS_Store
Thumbs.db
"""

def generate_structure():
    """Creates the directories and files for the project."""
    print(f"Creating project structure for '{ROOT_DIR_NAME}'...")

    # Create directories
    for path in dirs_to_create:
        path.mkdir(parents=True, exist_ok=True)
        print(f"  Created directory: {path}")

    # Create empty files
    for path in files_to_create:
        path.touch()
        print(f"  Created file: {path}")

    # Create .gitignore file with content
    gitignore_path = root_dir / ".gitignore"
    gitignore_path.write_text(gitignore_content)
    print(f"  Created file: {gitignore_path} (with content)")

    print("\nProject structure created successfully!")
    print(f"Navigate into the '{ROOT_DIR_NAME}' directory to start working.")

if __name__ == "__main__":
    generate_structure()