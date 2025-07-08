# app/main.py
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import logging
import json

# Import your MetadataAnalyzer
from src.metadata_analyzer import MetadataAnalyzer
# Import AI integrations
from src.ai_integrations import generate_forensic_narrative, infer_device_profile, update_knowledge_base
# Assuming you'll have PRNU modules later
# from src.prnu_model import train_prnu_model, analyze_prnu

# Setup logging for the FastAPI app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="AI Aver: Forensic Analysis Pipeline",
    description="A web application for PRNU content analysis and metadata forensic analysis."
)

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize Metadata Analyzer
metadata_analyzer = MetadataAnalyzer()

# Directory for uploaded files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Directory for PRNU training data
PRNU_TRAINING_DIR = Path("data/raw")
PRNU_TRAINING_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main HTML page with tabs for different functionalities."""
    # In a real app, you'd load this from templates/
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Aver: Forensic Analysis</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <h1>AI Aver: Forensic Analysis Pipeline</h1>
        <div class="tabs">
            <button class="tablinks active" onclick="openTab(event, 'MetadataAnalysis')">Metadata Analysis</button>
            <button class="tablinks" onclick="openTab(event, 'PRNUTraining')">PRNU Training</button>
            <button class="tablinks" onclick="openTab(event, 'PRNUAnalysis')">PRNU Analysis</button>
        </div>

        <div id="MetadataAnalysis" class="tabcontent" style="display:block;">
            <h2>Metadata Analysis</h2>
            <form action="/analyze-metadata" method="post" enctype="multipart/form-data">
                <label for="metadataFile">Upload Photo/Video for Tampering Analysis:</label>
                <input type="file" name="file" id="metadataFile" accept="image/*,video/*" required>
                <button type="submit">Analyze Metadata</button>
            </form>
            <div id="metadataResult" class="result-box"></div>
        </div>

        <div id="PRNUTraining" class="tabcontent">
            <h2>PRNU Training</h2>
            <form action="/upload-for-training" method="post" enctype="multipart/form-data">
                <label for="deviceName">Device Name (e.g., "iPhone 15 Pro"):</label>
                <input type="text" name="device_name" id="deviceName" required>
                <label for="trainingImages">Upload Multiple Images for Training:</label>
                <input type="file" name="files" id="trainingImages" accept="image/*" multiple required>
                <button type="submit">Start PRNU Training</button>
            </form>
            <div id="prnuTrainingResult" class="result-box"></div>
        </div>

        <div id="PRNUAnalysis" class="tabcontent">
            <h2>PRNU Analysis</h2>
            <p>Coming Soon: Upload an image to analyze its PRNU pattern for source identification or tampering.</p>
            </div>

        <script>
            function openTab(evt, tabName) {
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                }
                tablinks = document.getElementsByClassName("tablinks");
                for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }

            // Basic Fetch API integration for forms
            document.querySelectorAll('form').forEach(form => {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = new FormData(form);
                    const resultBoxId = form.nextElementSibling.id; // Get the next sibling div

                    try {
                        const response = await fetch(form.action, {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        document.getElementById(resultBoxId).innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        if (!response.ok) {
                            alert('Error: ' + (data.detail || 'Unknown error'));
                        }
                    } catch (error) {
                        document.getElementById(resultBoxId).innerHTML = '<p style="color:red;">Error submitting form: ' + error.message + '</p>';
                        console.error('Error:', error);
                    }
                });
            });
        </script>
        <style> /* Basic CSS for demonstration */
            body { font-family: sans-serif; margin: 20px; }
            .tabs { overflow: hidden; border: 1px solid #ccc; background-color: #f1f1f1; }
            .tablinks { background-color: inherit; float: left; border: none; outline: none; cursor: pointer; padding: 14px 16px; transition: 0.3s; font-size: 17px; }
            .tablinks:hover { background-color: #ddd; }
            .tablinks.active { background-color: #ccc; }
            .tabcontent { display: none; padding: 6px 12px; border: 1px solid #ccc; border-top: none; }
            .result-box { background-color: #e6e6e6; border: 1px solid #aaa; padding: 15px; margin-top: 20px; white-space: pre-wrap; overflow-x: auto; max-height: 500px; }
            form { margin-top: 15px; border: 1px solid #eee; padding: 15px; border-radius: 5px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], input[type="file"] { width: calc(100% - 20px); padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
            button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background-color: #45a049; }
        </style>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/analyze-metadata")
async def analyze_metadata(file: UploadFile = File(...)):
    """
    [span_25](start_span)Handles metadata forensics for a single uploaded file.[span_25](end_span)
    [span_26](start_span)Saves the file to a temporary, secure location.[span_26](end_span)
    [span_27](start_span)Executes the Metadata Forensics module.[span_27](end_span)
    [span_28](start_span)Returns the generated JSON report.[span_28](end_span)
    """
    temp_file_path = UPLOAD_DIR / file.filename
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"Received file for metadata analysis: {temp_file_path}")

        # Execute the Metadata Forensics module
        report = metadata_analyzer.analyze(temp_file_path)

        # Generate final narrative using AI if needed (can be integrated into analyzer or here)
        final_narrative = generate_forensic_narrative(report.get("forensic_narrative", []))
        report["forensic_narrative_ai_generated"] = final_narrative

        return JSONResponse(content=report)
    except Exception as e:
        logging.error(f"Error during metadata analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze metadata: {e}")
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink() # Clean up temporary file

@app.post("/upload-for-training")
async def upload_for_training(device_name: str = Form(...), files: List[UploadFile] = File(...)):
    """
    [span_29](start_span)Handles PRNU data ingestion for training.[span_29](end_span)
    [span_30](start_span)Accepts images only (.jpg, .jpeg, .png).[span_30](end_span)
    [span_31](start_span)Creates a new directory inside data/raw/ using the provided device name.[span_31](end_span)
    [span_32](start_span)Saves each uploaded image into this new directory.[span_32](end_span)
    [span_33](start_span)Uses Python's subprocess module to execute command-line scripts: preprocess.py, generate_triplets.py, and train.py.[span_33](end_span)
    [span_34](start_span)Returns a link to the final training run manifest (placeholder for now).[span_34](end_span)
    """
    if not device_name:
        raise HTTPException(status_code=400, detail="Device name is required for PRNU training.")

    device_training_dir = PRNU_TRAINING_DIR / device_name
    device_training_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created training directory: {device_training_dir}")

    saved_files = []
    for file in files:
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            logging.warning(f"Skipping non-image file for PRNU training: {file.filename} ({file.content_type})")
            [span_35](start_span)continue #[span_35](end_span)

        file_path = device_training_dir / file.filename
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))
            logging.info(f"Saved training image: {file_path}")
        except Exception as e:
            logging.error(f"Failed to save training image {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save image {file.filename}: {e}")

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid image files were uploaded for training.")

    # --- Placeholder for triggering PRNU pipeline ---
    # [span_36](start_span)This is where you would call your PRNU scripts using subprocess as planned.[span_36](end_span)
    # Example (assuming src/prnu_processor.py and src/prnu_model.py are command-line scripts):
    # import subprocess
    # try:
    #     logging.info(f"Triggering PRNU preprocessing for device: {device_name}")
    #     subprocess.run(["python", "src/prnu_processor.py", "--device", device_name], check=True)
    #     logging.info(f"Triggering PRNU triplet generation for device: {device_name}")
    #     subprocess.run(["python", "src/prnu_model.py", "--task", "generate_triplets", "--device", device_name], check=True)
    #     logging.info(f"Triggering PRNU training for device: {device_name}")
    #     subprocess.run(["python", "src/prnu_model.py", "--task", "train", "--device", device_name], check=True)
    #     [span_37](start_span)training_status_link = f"/data/training_manifests/{device_name}_latest.json" # Placeholder link[span_37](end_span)
    # except subprocess.CalledProcessError as e:
    #     logging.error(f"PRNU pipeline failed: {e}")
    #     raise HTTPException(status_code=500, detail=f"PRNU training failed for {device_name}: {e}")

    [span_38](start_span)training_status_link = f"/training-status/{device_name}_latest.json" # Mock link for now[span_38](end_span)

    return JSONResponse(content={
        "message": f"Successfully uploaded {len(saved_files)} images for PRNU training of '{device_name}'.",
        "saved_files": saved_files,
        "prnu_pipeline_status": "Triggered (placeholder)",
        [span_39](start_span)"training_manifest_link": training_status_link #[span_39](end_span)
    })

# To run this FastAPI app:
# 1. Save the above as app/main.py
# 2. Make sure src/metadata_analyzer.py and src/ai_integrations.py are in place.
# 3. Create a directory app/static and put a style.css (or leave it blank for now).
# 4. Make sure database/devices.json exists.
# 5. Run from your project root: uvicorn app.main:app --reload
