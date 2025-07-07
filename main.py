import os
import shutil
import subprocess
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import our new metadata analyzer
from src.metadata_analyzer import MetadataAnalyzer

# --- Application Setup ---
app = FastAPI(title="Forensic Analysis Toolkit")

# Initialize the analyzer once when the app starts
analyzer = MetadataAnalyzer()

# --- Static Files and Templates ---
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend" / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "frontend")

# --- Root Endpoint to Serve the Frontend ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML user interface."""
    return templates.TemplateResponse("index.html", {"request": request})

# --- PRNU Training Pipeline Endpoint ---
@app.post("/upload-for-training")
async def upload_for_training(
    device_name: str = Form(...), files: list[UploadFile] = File(...)
):
    """
    Handles uploading images for PRNU model training.
    """
    if not device_name or not files:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Device name and files are required."},
        )

    safe_device_name = "".join(c for c in device_name if c.isalnum() or c in (' ', '_')).rstrip()
    device_dir = BASE_DIR / "data" / "raw" / safe_device_name
    device_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        file_path = device_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(str(file_path))

    # Placeholder for triggering the pipeline
    print(f"Received {len(saved_files)} files for device '{device_name}'.")
    print("TODO: Trigger preprocess.py, generate_triplets.py, and train.py here.")

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": f"Successfully uploaded {len(saved_files)} files for device '{device_name}'.",
            "device_directory": str(device_dir),
        },
    )

# --- Metadata Analysis Pipeline Endpoint ---
@app.post("/analyze-metadata")
async def analyze_metadata(file: UploadFile = File(...)):
    """
    Handles uploading a single file for metadata forensic analysis.
    """
    if not file:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "A file is required for analysis."},
        )
        
    temp_dir = BASE_DIR / "data" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / f"{time.time()}_{file.filename}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # --- Integration Point ---
        # Call the metadata analyzer with the path to the saved file
        print(f"Analyzing file: {file_path}")
        report = analyzer.analyze(file_path)
        
        return JSONResponse(status_code=200, content=report)

    except Exception as e:
        # Log the exception for debugging
        print(f"An error occurred during metadata analysis: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred during analysis."}
        )
    finally:
        # Clean up the temporary file
        if file_path.exists():
            os.remove(file_path)

