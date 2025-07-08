#PRNU Pipeline Implementation (Core Functionality)
 * PRNU Preprocessing Script (preprocess.py / src/prnu_processor.py): This script needs to be written to extract the PRNU noise pattern from images. This typically involves denoising, filtering, and normalizing the image to isolate the sensor noise.
 * Triplet Generation / Model Training Script (generate_triplets.py, train.py / src/prnu_model.py): This is where your deep learning models (CNNs) for PRNU analysis will be defined and trained. It will involve:
   * Loading images from the data/raw directories.
   * Generating triplets (anchor, positive, negative samples) for contrastive learning.
   * Defining and training a CNN model (e.g., using TensorFlow or PyTorch) to learn the unique PRNU fingerprints.
   * Saving the trained model to the models/ directory.
 * PRNU Inference Logic (src/prnu_model.py or separate inference module): Functions to load a trained PRNU model and use it to analyze a new image, determining its source camera or detecting if its PRNU pattern is inconsistent with an expected source.
 * PRNU Data Acquisition: While you've identified datasets (Dresden, VISION, Forchheim), you'll need to actually download and structure a subset of them in your data/raw directory for initial training.
2. Historical Weather Validation (Real-World Data Integration)
 * Weather API Integration (src/weather_validator.py): Code to connect to a historical weather API (like OpenWeatherMap or WeatherStack). This module will need to take GPS coordinates and a timestamp, query the API, and return weather conditions (e.g., sunny, rainy, temperature).
 * Visual-Weather Correlation (Advanced AI): Logic (potentially within src/weather_validator.py or src/ai_integrations.py) to extract visual features from the image/video (e.g., sky color, presence of shadows) and programmatically compare them against the historical weather data. This is an advanced AI task.
3. AI Integration (Beyond Placeholders)
 * Actual Gemini/LLM Calls (src/ai_integrations.py): Replace the mock functions in src/ai_integrations.py with actual API calls to Google's Gemini (or another LLM) for:
   * Inferring device profiles for new entries in devices.json.
   * Generating comprehensive forensic narratives.
 * Error Handling and Rate Limiting for AI: Implement robust error handling and potentially rate-limiting for your AI API calls to prevent exceeding usage limits or crashing due to network issues.
4. Refinement and Robustness
 * Improved Metadata Parsing: The current metadata_analyzer.py handles common exiftool date formats. However, exiftool can return many variations. More robust parsing logic might be needed for different file types or less common metadata structures.
 * Level 3 Expansion: Currently, Level 3 focuses on JPEG quantization tables. You'll need to:
   * Gather actual quantization table data for various software programs and quality settings to make this robust.
   * Implement Audio Stream Analysis checks for video files.
 * Error Handling in FastAPI: Ensure comprehensive error handling and user-friendly messages for all FastAPI endpoints.
 * Security Considerations: For a production application, considerations like input validation, secure file storage, and API key management (e.g., using environment variables instead of hardcoding) would be crucial.
 * Frontend UI/UX: While the provided main.py has a basic HTML frontend, improving the user interface and user experience (e.g., real-time progress updates via WebSockets, clearer result presentation, file upload validation feedback) would be beneficial.
5. Testing and Validation
 * Unit Tests: Write comprehensive unit tests for each module (metadata_analyzer.py, prnu_processor.py, prnu_model.py, weather_validator.py, ai_integrations.py).
 * Integration Tests: Test the full pipeline flow, from file upload through all analysis levels.
 * Real-world Testing: Test with a diverse set of real images and videos (original and known tampered ones) to validate the system's accuracy.
Next Steps (Prioritized)
 * Implement PRNU Preprocessing and Training Logic (in src/prnu_processor.py and src/prnu_model.py):
   * Action: Start by researching and implementing the core PRNU extraction algorithm (e.g., based on the papers related to Dresden or Forchheim datasets). Then, build the logic for generating triplets and training a basic CNN model.
   * Why: This is a major component of your project and requires significant effort in terms of data handling, signal processing, and machine learning.
 * Integrate PRNU Pipeline with FastAPI (app/main.py):
   * Action: Replace the subprocess.run() placeholders in the /upload-for-training endpoint with actual calls to your newly developed PRNU scripts.
   * Why: Connects the frontend to the backend PRNU processing.
 * Refine MetadataAnalyzer Level 3 (_run_level_3_advanced_heuristics()):
   * Action: Expand the jpeg_quantization_tables data in devices.json with more real-world examples for different software and quality settings. Implement the comparison logic more rigorously (e.g., considering tolerance). Start researching Audio Stream Analysis as mentioned in your plan.
   * Why: This enhances the depth of your tamper detection.
 * Implement Historical Weather Validation (src/weather_validator.py):
   * Action: Choose a historical weather API, sign up for a key, and write the Python code to query it. Integrate this into the MetadataAnalyzer's analyze method (perhaps as another level, e.g., Level 5, or integrated into the narrative generation).
   * Why: Adds a unique and powerful dimension to your forensic analysis by using external data for corroboration.
 * Enable Actual AI Integration (src/ai_integrations.py):
   * Action: Obtain a Gemini API key. Replace the mock functions in src/ai_integrations.py with actual calls to the google.generativeai SDK.
   * Why: Unleashes the power of AI for narrative generation and knowledge base enrichment.
 * Comprehensive Testing:
   * Action: Begin writing unit tests for all modules as you develop them.
   * Why: Ensures code quality, identifies bugs early, and verifies that individual components work as expected.

