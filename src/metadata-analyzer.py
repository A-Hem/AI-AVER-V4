import json
import logging
from datetime import datetime
from pathlib import Path
import exiftool
from typing import Dict, Any, List, Union

# Define the path to the knowledge base relative to this script
# Assumes project structure: project_root/src/metadata_analyzer.py and
# project_root/database/devices.json
KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent.parent / "database" / "devices.json"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MetadataAnalyzer:
    """
    [span_0](start_span)A class to perform a tiered forensic analysis of a file's metadata.[span_0](end_span)
    [span_1](start_span)It compares file metadata against a known device database to detect tampering.[span_1](end_span)
    """
    def __init__(self):
        [span_2](start_span)self.knowledge_base = self._load_knowledge_base() #[span_2](end_span)
        self.narrative: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.file_path: Path = Path() # Store file path for later use if needed

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Loads the device knowledge base from the JSON file."""
        try:
            with open(KNOWLEDGE_BASE_PATH, 'r') as f:
                logging.info(f"Loading knowledge base from {KNOWLEDGE_BASE_PATH}")
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"CRITICAL: Device knowledge base not found at {KNOWLEDGE_BASE_PATH}.")
            return {}
        except json.JSONDecodeError:
            logging.error("CRITICAL: Device knowledge base is not valid JSON.")
            return {}

    def analyze(self, file_path: Path) -> Dict[str, Any]:
        """
        [span_3](start_span)Runs the full tiered analysis pipeline on a given file.[span_3](end_span)
        Args:
            file_path: The path to the file to be analyzed.
        Returns:
            [span_4](start_span)A dictionary containing the full analysis report.[span_4](end_span)
        """
        self.narrative = [] # Reset for each analysis
        self.metadata = {}  # Reset for each analysis
        self.file_path = file_path

        try:
            # Using ExifToolHelper for improved context management
            [span_5](start_span)with exiftool.ExifToolHelper() as et: #[span_5](end_span)
                # get_metadata returns a list, take the first element for a single file
                self.metadata = et.get_metadata(str(file_path))[0]
        except Exception as e:
            logging.error(f"Failed to extract metadata from {file_path}: {e}")
            return {"error": "Could not extract metadata from file.", "details": str(e)}

        # --- Run the Tiered Analysis ---
        [span_6](start_span)is_level1_flagged = self._run_level_1_integrity_check() #[span_6](end_span)

        if is_level1_flagged:
            # If Level 1 is flagged, proceed to Level 2
            [span_7](start_span)is_level2_flagged_or_ambiguous = self._run_level_2_knowledge_based_analysis() #[span_7](end_span)

            # Condition for Level 3: Level 1 was flagged AND Level 2 was ambiguous or couldn't definitively confirm tampering.
            # For simplicity, let's say if Level 2 detected an inconsistency, we try Level 3 for confirmation.
            # You might want more sophisticated logic here, e.g., based on a 'confidence' score from Level 2.
            # The plan states: "Runs if Level 2 is Ambiguous"
            # For now, if Level 2 found *any* inconsistency, let's try Level 3.
            if is_level2_flagged_or_ambiguous:
                 self._run_level_3_advanced_heuristics()

        # Level 4: AI Knowledge Base Enrichment (Always Runs, ideally after full analysis)
        self._run_level_4_ai_knowledge_base_enrichment()


        return {
            "forensic_narrative": self.narrative,
            "full_metadata": self.metadata,
            "analysis_summary": { # Add a summary for easy access
                "level1_status": "FLAGGED" if is_level1_flagged else "CLEAN",
                "overall_status": "FLAGGED" if any(item['status'] == 'FLAGGED' or item['status'] == 'INCONSISTENCY_DETECTED' for item in self.narrative) else "CLEAN"
            }
        }

    def _run_level_1_integrity_check(self) -> bool:
        """
        [span_8](start_span)Performs basic checks for modification.[span_8](end_span)
        [span_9](start_span)Returns True if tampering is detected, False otherwise.[span_9](end_span)
        """
        logging.info("Running Level 1 Analysis: Integrity Check")
        is_flagged = False

        # Check for third-party software tags
        software_tag = self.metadata.get('EXIF:Software') or self.metadata.get('XMP:CreatorTool')
        if software_tag:
            # Make comparison case-insensitive for common editors
            normalized_software_tag = software_tag.lower()
            known_editors = ["adobe", "gimp", "final cut", "premiere pro", "photoshop"]
            if any(editor in normalized_software_tag for editor in known_editors):
                self.narrative.append({
                    "level": 1,
                    "status": "FLAGGED",
                    "finding": "Third-party software tag detected.",
                    "reason": f"The 'Software' tag is '{software_tag}', indicating processing by external software."
                })
                is_flagged = True

        # Check for timestamp inconsistencies
        try:
            create_date_str = self.metadata.get('EXIF:CreateDate') or self.metadata.get('QuickTime:CreateDate')
            modify_date_str = self.metadata.get('EXIF:ModifyDate') or self.metadata.get('QuickTime:ModifyDate')
            file_mod_date = self.metadata.get('File:FileModifyDate') # File system modification date

            if create_date_str and modify_date_str:
                # Robust parsing for exiftool dates. exiftool often provides 'YYYY:MM:DD HH:MM:SS' or 'YYYY:MM:DD HH:MM:SS.ss+ZZ:ZZ'
                # We'll try to parse the main part and ignore milliseconds/timezone for comparison
                create_date = datetime.strptime(create_date_str.split('+')[0].split('.')[0], '%Y:%m:%d %H:%M:%S')
                modify_date = datetime.strptime(modify_date_str.split('+')[0].split('.')[0], '%Y:%m:%d %H:%M:%S')

                # A small difference (e.g., a few seconds) is normal.
                # Significant difference (e.g., > 1 minute for a simple save, more for extensive editing)
                [span_10](start_span)if (modify_date - create_date).total_seconds() > 60: # More than 60s difference[span_10](end_span)
                    self.narrative.append({
                        "level": 1,
                        "status": "FLAGGED",
                        "finding": "Significant timestamp mismatch.",
                        "reason": f"File ModifyDate ({modify_date}) is significantly later than its CreateDate ({create_date})."
                    })
                    is_flagged = True
                elif (modify_date < create_date): # Modify date should not be before creation date
                     self.narrative.append({
                        "level": 1,
                        "status": "FLAGGED",
                        "finding": "Illogical timestamp order.",
                        "reason": f"File ModifyDate ({modify_date}) is earlier than its CreateDate ({create_date}), which is highly suspicious."
                    })
                     is_flagged = True

            # Additional check: Compare internal timestamps with file system modification time
            if file_mod_date and create_date_str:
                # File:FileModifyDate format is often 'YYYY:MM:DD HH:MM:SS-ZZ:ZZ' or 'YYYY:MM:DD HH:MM:SS+ZZ:ZZ'
                # Need to handle timezone if comparison is sensitive to it, or normalize
                # For simplicity, let's just parse the datetime part
                fs_mod_date = datetime.strptime(file_mod_date.split('+')[0].split('-')[0].split('.')[0], '%Y:%m:%d %H:%M:%S')
                # A fresh original file's internal create/modify dates should be very close to file system mod date.
                # If there's a huge difference, it might indicate copying/moving or modification.
                if 'create_date' in locals() and abs((fs_mod_date - create_date).total_seconds()) > (3600 * 24): # More than 24 hours difference
                    self.narrative.append({
                        "level": 1,
                        "status": "FLAGGED",
                        "finding": "File system modification date discrepancy.",
                        "reason": f"File system modification date ({fs_mod_date}) is significantly different from internal CreateDate ({create_date}), which might indicate copying or external modification."
                    })
                    is_flagged = True

        except (ValueError, TypeError) as e:
            logging.warning(f"Could not parse timestamps in Level 1: {e}")

        if not is_flagged:
            self.narrative.append({
                "level": 1,
                "status": "CLEAN",
                "finding": "High confidence of being an unaltered camera original.",
                "reason": "No third-party software tags or significant timestamp mismatches found."
            })
        return is_flagged

    def _run_level_2_knowledge_based_analysis(self) -> bool:
        """
        [span_11](start_span)Compares file metadata against the device knowledge base.[span_11](end_span)
        Returns True if inconsistencies are detected, False otherwise.
        """
        logging.info("Running Level 2 Analysis: Knowledge-Based Inconsistency Check")
        is_level2_inconsistent = False

        model = self.metadata.get('EXIF:Model') or self.metadata.get('QuickTime:Model')
        # Normalize model name for lookup (e.g., remove 'Apple ' prefix if knowledge base doesn't have it)
        # This is a heuristic and might need tuning
        if model:
            normalized_model = model.replace('Apple ', '').replace('Google ', '')
        else:
            normalized_model = None

        device_profile = None
        if normalized_model and normalized_model in self.knowledge_base:
            device_profile = self.knowledge_base[normalized_model]
        elif model and model in self.knowledge_base: # Try original model name if normalization failed or wasn't needed
            device_profile = self.knowledge_base[model]

        if not device_profile:
            self.narrative.append({
                [span_12](start_span)"level": 2, "status": "UNKNOWN_DEVICE", #[span_12](end_span)
                [span_13](start_span)"finding": "Cannot perform knowledge-based check.", #[span_13](end_span)
                "reason": f"Device model '{model if model else 'N/A'}' not found in the knowledge base." [span_14](start_span)#
            })
            return False # Cannot run Level 2 checks if device is unknown

        # Check 1: Codec Mismatch (for videos)
        # exiftool might give 'MajorBrand', 'CompatibleBrands', 'HandlerType' for video characteristics
        # QuickTime:CompressorID is a good start. Also look for QuickTime:Format or File:MIMEType
        file_codec_id = self.metadata.get('QuickTime:CompressorID') # e.g., 'hev1' for HEVC
        file_mime_type = self.metadata.get('File:MIMEType') # e.g., 'video/mp4'

        expected_video_codec_default = device_profile.get('video_codec_default', '').lower()

        # Simple check for video files only
        if file_mime_type and 'video' in file_mime_type:
            if expected_video_codec_default and file_codec_id:
                # 'hev1' is common for HEVC, 'mp4v' for H.264
                # This needs to be robust for various exiftool outputs vs. simplified codec names in KB
                if 'hevc' in expected_video_codec_default and file_codec_id.lower() not in ['hev1', 'hvc1']:
                    self.narrative.append({
                        "level": 2, "status": "INCONSISTENCY_DETECTED",
                        "finding": "Video codec mismatch.",
                        "details": f"File uses codec ID '{file_codec_id}', but a camera-original '{model}' is expected to use '{expected_video_codec_default}' (e.g. 'hev1')."
                    })
                    is_level2_inconsistent = True
                elif 'h.264/avc' in expected_video_codec_default and file_codec_id.lower() not in ['avc1', 'mp4v']:
                    self.narrative.append({
                        "level": 2, "status": "INCONSISTENCY_DETECTED",
                        "finding": "Video codec mismatch.",
                        "details": f"File uses codec ID '{file_codec_id}', but a camera-original '{model}' is expected to use '{expected_video_codec_default}' (e.g. 'avc1')."
                    })
                    is_level2_inconsistent = True
            elif expected_video_codec_default and not file_codec_id:
                 self.narrative.append({
                        "level": 2, "status": "INCONSISTENCY_DETECTED",
                        "finding": "Video codec missing from metadata.",
                        "details": f"A video codec is expected from a '{model}', but no codec ID found in metadata."
                    })
                 is_level2_inconsistent = True

        # Check 2: Expected Metadata Tags Missing
        missing_tags = []
        for tag in device_profile.get('expected_metadata_tags', []):
            # Check if any key in self.metadata ends with the expected tag (e.g., 'EXIF:Make', 'QuickTime:Model')
            if not any(key.lower().endswith(f":{tag.lower()}") for key in self.metadata.keys()):
                missing_tags.append(tag)

        # Allow for a small number of non-critical tags to be missing
        if len(missing_tags) > 2:
            self.narrative.append({
                "level": 2, "status": "INCONSISTENCY_DETECTED",
                "finding": "Expected metadata tags are missing.",
                "details": f"File is missing critical tags expected from a '{model}', such as: {', '.join(missing_tags[:3])}. "
                           "This often occurs after re-encoding or social media sharing." #[span_14](end_span)
            })
            is_level2_inconsistent = True

        # Check 3: Date Inconsistency (e.g., file creation before device release year)
        create_date_str = self.metadata.get('EXIF:CreateDate') or self.metadata.get('QuickTime:CreateDate')
        if create_date_str and 'release_year' in device_profile:
            try:
                create_year = datetime.strptime(create_date_str.split('+')[0].split('.')[0], '%Y:%m:%d %H:%M:%S').year
                if create_year < device_profile['release_year']:
                    self.narrative.append({
                        "level": 2, "status": "MAJOR_DISCREPANCY_DETECTED",
                        "finding": "File created before device release.",
                        "details": f"File's creation year ({create_year}) is before the known release year ({device_profile['release_year']}) of the '{model}'. This is a massive red flag."
                    })
                    is_level2_inconsistent = True
            except (ValueError, TypeError):
                logging.warning(f"Could not parse create date for release year check: {create_date_str}")

        return is_level2_inconsistent

    def _run_level_3_advanced_heuristics(self):
        """
        To find subtle, low-level software "fingerprints" to confirm the editing environment.
        This level runs if Level 2 was ambiguous or flagged for confirmation.
        """
        logging.info("Running Level 3 Analysis: Advanced Heuristic Confirmation")

        # Focus on JPEG Quantization Table Analysis for images
        file_extension = self.file_path.suffix.lower()
        if file_extension in ['.jpg', '.jpeg']:
            # exiftool provides JPEG Quantization Tables as a string or array of numbers
            # e.g., '16 11 10 16 24 40 51 61 ...'
            jpeg_qt_tag = self.metadata.get('EXIF:JPEGQTables')
            if jpeg_qt_tag:
                # Convert string representation to a list of integers for comparison
                try:
                    # JPEGQTables can be a string like "16 11 10 ..." or "16,11,10,..."
                    # Or it might be returned as an actual list of lists from ExifToolHelper depending on version/config
                    if isinstance(jpeg_qt_tag, str):
                        # Attempt to parse into numbers. It's usually two 64-element tables or flattened
                        # Assuming a flat list of 128 numbers (for 2 tables) for simpler comparison.
                        qt_values = [int(x) for x in jpeg_qt_tag.replace(',', ' ').split() if x.strip().isdigit()]
                        # If exiftool returns them as comma-separated lists, ensure spaces for split
                    elif isinstance(jpeg_qt_tag, list) and all(isinstance(i, int) for i in jpeg_qt_tag):
                        qt_values = jpeg_qt_tag
                    else: # Handle cases where it might be a list of lists already, flatten it
                         qt_values = [item for sublist in jpeg_qt_tag for item in sublist] if isinstance(jpeg_qt_tag, list) and any(isinstance(i, list) for i in jpeg_qt_tag) else []

                    # Compare against known software fingerprints in knowledge base
                    for software_name, software_profile in self.knowledge_base.items():
                        if software_profile.get('type') == 'Software' and 'fingerprints' in software_profile:
                            known_qt = software_profile['fingerprints'].get('jpeg_quantization_tables', {}).get('tables')
                            if known_qt:
                                # Flatten the known_qt list of lists for comparison
                                flattened_known_qt = [item for sublist in known_qt for item in sublist]
                                if len(qt_values) == len(flattened_known_qt):
                                    # Simple exact match check. For real-world, might need tolerance or statistical comparison
                                    match_percentage = sum(1 for a, b in zip(qt_values, flattened_known_qt) if a == b) / len(qt_values) * 100
                                    if match_percentage > 95: # High match indicates strong probability
                                        self.narrative.append({
                                            "level": 3,
                                            "status": "CONFIRMATION",
                                            "finding": "Low-level software fingerprint detected.",
                                            "details": f"JPEG quantization tables ({match_percentage:.2f}% match) are highly consistent with '{software_name}' software."
                                        })
                                        # Once a strong match is found, we might stop or continue to find other matches
                                        # For now, let's just report the first strong match
                                        break
                                else:
                                    logging.debug(f"QT table length mismatch for {software_name}. File: {len(qt_values)}, KB: {len(flattened_known_qt)}")
                except (ValueError, TypeError) as e:
                    logging.warning(f"Could not parse JPEG QT tables for Level 3: {e}")
            else:
                logging.info("No JPEG Quantization Tables found for Level 3 analysis.")
        else:
            logging.info(f"Level 3 JPEG QT analysis skipped for non-JPEG file: {file_extension}")

        # You can add more Level 3 checks here (e.g., Audio Stream Analysis for video files)
        # if file_extension in ['.mp4', '.mov']:
        #     # Example: Check audio bitrate consistency with typical mobile export vs. professional software
        #     audio_bitrate = self.metadata.get('QuickTime:AvgBitrate') # Or similar audio-specific tags
        #     # Compare to known values in devices.json for software like Premiere Pro
        #     pass

    def _run_level_4_ai_knowledge_base_enrichment(self):
        """
        [span_15](start_span)Goal: To make the system smarter with every analysis.[span_15](end_span)
        [span_16](start_span)Process: Sends extracted metadata to an AI model to generate/update device profiles.[span_16](end_span)
        """
        logging.info("Running Level 4 Analysis: AI Knowledge Base Enrichment")

        # This method will primarily interact with an external AI service (like Gemini).
        # For now, it's a placeholder. The actual AI call logic will go into ai_integrations.py

        # Example: Check if the current device model is already in the knowledge base
        model = self.metadata.get('EXIF:Model') or self.metadata.get('QuickTime:Model')
        if model and model not in self.knowledge_base:
            # This is where you'd typically call an AI model to infer a profile
            self.narrative.append({
                "level": 4,
                "status": "KNOWLEDGE_BASE_CANDIDATE",
                "finding": "New device model identified.",
                "details": f"The device model '{model}' is not in the knowledge base. It's a candidate for AI enrichment."
            })
            # In a full implementation, you'd call:
            # from src.ai_integrations import infer_device_profile, update_knowledge_base
            # inferred_profile = infer_device_profile(self.metadata)
            # if inferred_profile:
            #     update_knowledge_base(model, inferred_profile)
            #     self.narrative.append({
            #         "level": 4,
            #         "status": "KNOWLEDGE_BASE_UPDATED",
            #         "details": f"AI-generated profile for '{model}' added to knowledge base."
            #     })
        elif model and model in self.knowledge_base:
            # [span_17](start_span)Even if device exists, AI can find new patterns or enrich existing ones.[span_17](end_span)
            self.narrative.append({
                "level": 4,
                "status": "KNOWLEDGE_BASE_REVIEW_CANDIDATE",
                "finding": "Existing device profile for review/enrichment.",
                [span_18](start_span)"details": f"Analysis of this file for '{model}' can potentially contribute new information to the knowledge base, improving future analyses." #[span_18](end_span)
            })
            # You might still call an AI here to suggest new tags or update existing ones based on this file's metadata.
            # from src.ai_integrations import infer_and_merge_profile
            # infer_and_merge_profile(model, self.metadata)


# Example of how to run this from another script (like main.py)
if __name__ == '__main__':
    # This is for testing purposes only
    # To run this, you need exiftool installed and accessible in your PATH.
    # On macOS: brew install exiftool
    # On Linux: sudo apt-get install libimage-exiftool-perl
    # On Windows: Download from exiftool.org and add to PATH.

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Create a dummy knowledge base for testing
    Path("database").mkdir(exist_ok=True)
    test_kb_path = Path(__file__).resolve().parent.parent / "database" / "devices.json"
    with open(test_kb_path, "w") as f:
        # Using a simplified version of your actual devices.json for local testing here
        f.write(json.dumps({
            "Apple iPhone 15 Pro": {
                "release_year": 2023,
                "known_software_pattern": "iOS",
                "video_codec_default": "HEVC",
                "audio_codec_default": "AAC",
                "expected_metadata_tags": ["Make", "Model", "CreateDate", "LensModel"]
            },
            "Canon EOS 5D Mark IV": {
                "release_year": 2016,
                "known_software_pattern": "Canon",
                "expected_metadata_tags": ["Make", "Model", "LensInfo", "ShutterSpeedValue"]
            },
            "Adobe Photoshop 2024": {
                "type": "Software",
                "vendor": "Adobe",
                "fingerprints": {
                    "jpeg_quantization_tables": {
                        "tables": [
                            [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92, 49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]
                        ]
                    }
                }
            }
        }))


    analyzer = MetadataAnalyzer()

    # --- Create a dummy file for testing. Replace with your actual test file paths. ---
    # To properly test, you'd create a dummy JPG with specific metadata using exiftool or PIL,
    # or use an actual test file.

    # Example 1: Simulate a clean file (create date and modify date close)
    # You would need to create a real image file here for exiftool to work
    # For a quick test, you can 'touch' a file, but it won't have much metadata
    # from PIL import Image
    # img = Image.new('RGB', (100, 100), color = 'red')
    # clean_image_path = Path("./temp_clean_image.jpg")
    # img.save(clean_image_path)
    # This will still likely have 'Pillow' as software tag. For a real test,
    # use an actual camera original image.

    # Create a dummy JPG for testing (requires Pillow)
    try:
        from PIL import Image
        clean_image_path = Path("test_image_clean.jpg")
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(clean_image_path, exif={'Software': 'Apple iOS 17.5.1', 'Make': 'Apple', 'Model': 'Apple iPhone 15 Pro', 'DateTimeOriginal': '2024:06:01 10:00:00', 'ModifyDate': '2024:06:01 10:00:05'})
        logging.info(f"Created dummy clean image: {clean_image_path}")

        edited_image_path = Path("test_image_edited.jpg")
        img_edited = Image.new('RGB', (100, 100), color = 'blue')
        img_edited.save(edited_image_path, exif={'Software': 'Adobe Photoshop 2024', 'Make': 'Apple', 'Model': 'Apple iPhone 15 Pro', 'DateTimeOriginal': '2024:01:01 10:00:00', 'ModifyDate': '2024:06:01 15:30:00'})
        logging.info(f"Created dummy edited image: {edited_image_path}")

        # Test with clean file
        print(f"\n--- Analyzing {clean_image_path} ---")
        report_clean = analyzer.analyze(clean_image_path)
        print(json.dumps(report_clean, indent=2))

        # Test with edited file
        print(f"\n--- Analyzing {edited_image_path} ---")
        report_edited = analyzer.analyze(edited_image_path)
        print(json.dumps(report_edited, indent=2))

        # Test with a non-existent file
        print("\n--- Analyzing non-existent_file.jpg ---")
        report_non_existent = analyzer.analyze(Path("non-existent_file.jpg"))
        print(json.dumps(report_non_existent, indent=2))

    except ImportError:
        logging.error("Pillow is not installed. Cannot create dummy test images. Please install with 'pip install Pillow'.")
        logging.info("Please provide an actual image file path to test:")
        # For manual testing without Pillow:
        # test_file_path = Path("path/to/your/image.jpg")
        # if test_file_path.exists():
        #     report = analyzer.analyze(test_file_path)
        #     print(json.dumps(report, indent=2))
        # else:
        #     logging.warning("No test file provided or found.")
    except Exception as e:
        logging.error(f"An error occurred during testing: {e}")

    finally:
        # Clean up dummy files
        import os
        if 'clean_image_path' in locals() and clean_image_path.exists():
            os.remove(clean_image_path)
        if 'edited_image_path' in locals() and edited_image_path.exists():
            os.remove(edited_image_path)
        if test_kb_path.exists():
            os.remove(test_kb_path)
        if Path("database").exists():
            try:
                Path("database").rmdir()
            except OSError:
                logging.warning("Could not remove 'database' directory. It might not be empty.")

    print("\nMetadataAnalyzer class is defined and ready to be imported.")

