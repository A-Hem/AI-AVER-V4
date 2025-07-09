# src/ai_integrations.py
import json
import logging
from typing import Dict, Any, Optional

# Assuming you have the Google AI SDK installed: pip install google-generativeai
# from google.generativeai.types import HarmCategory, HarmBlockThreshold
# import google.generativeai as genai

# Configure your Gemini API key (store securely, e.g., in environment variables)
# genai.configure(api_key="YOUR_GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Placeholder for Gemini Model ---
# This is a simplified representation. You'd set up your model with specific
# safety settings and generation configurations.
# model = genai.GenerativeModel('gemini-pro')

def infer_device_profile(metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    [span_19](start_span)Uses an AI model (e.g., Gemini) to infer a device profile from extracted metadata.[span_19](end_span)
    Args:
        metadata: The full metadata dictionary extracted from the file.
    Returns:
        A dictionary representing the inferred device profile, or None if inference fails.
    """
    logging.info("Attempting to infer device profile using AI.")
    prompt = f"""Based on the following image/video metadata, generate a JSON profile for the device model.
    Infer its release year, default codecs (video_codec_default, audio_codec_default),
    and a list of expected metadata tags (expected_metadata_tags) based on the data provided and your general knowledge.
    If a field cannot be reliably inferred, omit it or use a null value.
    The output must be a valid JSON object.

    Metadata:
    {json.dumps(metadata, indent=2)}

    JSON Profile (e.g., for a 'Google Pixel 8 Pro'):
    {{
        "release_year": 2023,
        "known_software_pattern": "Android",
        "video_codec_default": "H.264/AVC",
        "audio_codec_default": "AAC",
        "expected_metadata_tags": ["Make", "Model", "CreateDate", "GPSLatitude", "GPSLongitude", "SubSecTimeOriginal"]
    }}
    """
    try:
        # Example AI call (requires actual setup of genai and a model)
        # response = model.generate_content(
        #     prompt,
        #     safety_settings={
        #         HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        #         HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        #         HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        #         HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        #     }
        # )
        # inferred_json_str = response.text
        # inferred_profile = json.loads(inferred_json_str)

        # For testing without actual AI calls, return a dummy profile
        logging.warning("AI integration is currently mocked. Replace with actual Gemini API calls.")
        if "EXIF:Model" in metadata:
            dummy_model = metadata["EXIF:Model"].replace('Apple ', '') # Simple normalization
            inferred_profile = {
                "release_year": 2024, # Dummy data
                "known_software_pattern": "Generic",
                "video_codec_default": "H.264",
                "audio_codec_default": "AAC",
                "expected_metadata_tags": ["Make", "Model", "Software", "CreateDate"]
            }
            logging.info(f"Mock AI inferred profile for '{dummy_model}'.")
            return inferred_profile
        else:
            logging.warning("Could not infer device model from metadata for mock AI.")
            return None

    except Exception as e:
        logging.error(f"Error during AI inference for device profile: {e}")
        return None

def generate_forensic_narrative(findings_list: List[Dict[str, Any]]) -> str:
    """
    Uses an AI model (e.g., Gemini) to generate a structured forensic narrative
    [span_20](start_span)based on the analysis findings.[span_20](end_span)
    Args:
        findings_list: A list of dictionaries, each representing a finding from the analysis levels.
    Returns:
        A structured string representing the forensic narrative.
    """
    logging.info("Generating forensic narrative using AI.")
    prompt = f"""Based on the following forensic analysis findings, generate a concise and structured narrative.
    Summarize the key findings, including the level of analysis (e.g., Level 1 Integrity Check),
    the status (e.g., FLAGGED, CLEAN, INCONSISTENCY_DETECTED), and the reason/details.
    Focus on potential signs of tampering or inconsistencies.
    If the file appears clean, state that clearly.

    Findings:
    {json.dumps(findings_list, indent=2)}

    Forensic Narrative:
    """
    try:
        # response = model.generate_content(
        #     prompt,
        #     safety_settings={
        #         HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        #         HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        #         HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        #         HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        #     }
        # )
        # return response.text

        # For testing without actual AI calls, return a dummy narrative
        mock_narrative = "Mock AI Narrative: "
        flagged_findings = [f for f in findings_list if f.get('status') not in ['CLEAN', 'KNOWLEDGE_BASE_CANDIDATE', 'KNOWLEDGE_BASE_REVIEW_CANDIDATE']]
        if flagged_findings:
            mock_narrative += "Potential issues detected:\n"
            for f in flagged_findings:
                mock_narrative += f"- Level {f['level']}: {f['finding']} ({f['status']}). Reason: {f.get('reason', f.get('details', 'N/A'))}\n"
        else:
            mock_narrative += "No significant tampering or inconsistencies detected."
        logging.warning("AI narrative generation is currently mocked. Replace with actual Gemini API calls.")
        return mock_narrative

    except Exception as e:
        logging.error(f"Error during AI narrative generation: {e}")
        return "Failed to generate forensic narrative due to an error."

def update_knowledge_base(model_name: str, inferred_profile: Dict[str, Any]):
    """
    [span_21](start_span)Updates the devices.json knowledge base with a new AI-inferred profile.[span_21](end_span)
    [span_22](start_span)If the device already exists, it can merge new information.[span_22](end_span)
    """
    logging.info(f"Attempting to update knowledge base for '{model_name}'.")
    try:
        # Reload current knowledge base to ensure it's up-to-date
        with open(KNOWLEDGE_BASE_PATH, 'r') as f:
            current_kb = json.load(f)

        if model_name in current_kb:
            # Merge existing and inferred (simple merge, can be more complex)
            current_kb[model_name].update(inferred_profile)
            [span_23](start_span)logging.info(f"Merged AI-inferred profile for '{model_name}' into knowledge base.") #[span_23](end_span)
        else:
            current_kb[model_name] = inferred_profile
            [span_24](start_span)logging.info(f"Added AI-inferred profile for new device '{model_name}' to knowledge base.") #[span_24](end_span)

        with open(KNOWLEDGE_BASE_PATH, 'w') as f:
            json.dump(current_kb, f, indent=2)

    except Exception as e:
        logging.error(f"Error updating knowledge base: {e}")

if __name__ == '__main__':
    # Simple test for AI integrations (will use mock functions if AI is not set up)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Dummy metadata for testing
    dummy_metadata = {
        "EXIF:Make": "TestMake",
        "EXIF:Model": "TestModelX",
        "EXIF:CreateDate": "2024:01:15 12:30:00",
        "EXIF:Software": "Some Editing Software"
    }

    # Test infer_device_profile
    inferred = infer_device_profile(dummy_metadata)
    print(f"\nInferred Profile: {json.dumps(inferred, indent=2) if inferred else 'None'}")

    # Test generate_forensic_narrative
    dummy_findings = [
        {"level": 1, "status": "FLAGGED", "finding": "Third-party software tag detected.", "reason": "Software is 'Some Editing Software'."},
        {"level": 2, "status": "INCONSISTENCY_DETECTED", "finding": "Expected metadata tags are missing.", "details": "File is missing critical tags expected."},
        {"level": 4, "status": "KNOWLEDGE_BASE_CANDIDATE", "finding": "New device model identified.", "details": "The device model 'TestModelX' is not in the knowledge base."}
    ]
    narrative = generate_forensic_narrative(dummy_findings)
    print(f"\nGenerated Narrative:\n{narrative}")

    # Test update_knowledge_base (requires database/devices.json to exist and be writable)
    # Ensure database/devices.json exists for this test
    Path("database").mkdir(exist_ok=True)
    with open(KNOWLEDGE_BASE_PATH, "w") as f:
        f.write(json.dumps({"ExistingModel": {"release_year": 2020}}))

    if inferred:
        update_knowledge_base("TestModelX", inferred)
        # Verify update
        with open(KNOWLEDGE_BASE_PATH, 'r') as f:
            updated_kb = json.load(f)
            print(f"\nUpdated KB for TestModelX: {json.dumps(updated_kb.get('TestModelX'), indent=2)}")

    # Clean up dummy files/dirs
    import os
    if KNOWLEDGE_BASE_PATH.exists():
        os.remove(KNOWLEDGE_BASE_PATH)
    if Path("database").exists():
        try:
            Path("database").rmdir()
        except OSError:
            logging.warning("Could not remove 'database' directory. It might not be empty.")

