#!/usr/bin/env python3
"""
Meta Models License Extraction from Stage-1 Data

This script processes the stage-1-api-data-extraction.json file to:
1. Identify Meta models using provider extraction logic
2. Extract licensing information using regex-based version detection
3. Generate comprehensive JSON output with all licensing details

Features:
- Regex-based Llama version extraction (e.g., "Llama 3.1" → "Llama-3.1")
- HuggingFace tree URL construction
- Consistent provider identification with main pipeline
- Comprehensive JSON output with metadata

Source Data: 02_filtered_models.json
Output: 04_meta_licenses.json

Author: Claude Code Assistant
Date: 2025-09-05
"""

import json
import os
import re
from typing import Dict, List, Tuple, Any
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    get_ist_timestamp,
    ensure_output_dir_exists,
    clean_output_directory,
    set_current_pipeline,
    get_project_root,
)
set_current_pipeline('openrouter')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "openrouter"

# =============================================================================
# META LICENSE PROCESSING FUNCTIONS
# =============================================================================

def get_meta_license_info(model_id: str, canonical_slug: str = '') -> Dict[str, str]:
    """Get license information for Meta models using improved Groq logic

    Source file: 02_filtered_models.json
    Source field: 'name' (e.g., "Meta: Llama 3.1 405B Instruct (free)")

    Enhanced regex patterns from Groq pipeline:
    - Llama Guard detection: r'llama[_/-]?guard[_/-]?(\d+)'
    - Version patterns: r'llama[_/-]?(\d+\.\d+)' and r'llama[_/-]?(\d+)'
    - Official Llama license URLs instead of HuggingFace URLs

    Args:
        model_id: The model name from 02_filtered_models.json 'name' field
        canonical_slug: The canonical slug (unused in new logic)

    Returns:
        Dict with license_info_text="", license_info_url="",
        license_name="Llama-{version}", license_url=official Llama URL
    """
    model_lower = model_id.lower()

    # Llama Guard patterns (adapted for OpenRouter format)
    guard_match = re.search(r'llama[\s_/-]?guard[\s_/-]?(\d+)', model_lower)
    if guard_match:
        guard_version = guard_match.group(1)
        return {
            'license_info_text': '',
            'license_info_url': '',
            'license_name': f'LLAMA-{guard_version}',
            'license_url': f'https://www.llama.com/llama{guard_version}/license/'
        }

    # Regular Llama version patterns (adapted for OpenRouter format with spaces)
    version_patterns = [
        r'llama[\s_/-]?(\d+\.\d+)',  # Match "Llama 3.1", "llama-3.1", "meta-llama/llama-3.1", etc.
        r'llama[\s_/-]?(\d+)',       # Match "Llama 4", "llama-4", "meta-llama/llama-4", etc.
    ]

    for pattern in version_patterns:
        match = re.search(pattern, model_lower)
        if match:
            version = match.group(1)
            url_version = version.replace('.', '_')
            return {
                'license_info_text': '',
                'license_info_url': '',
                'license_name': f'LLAMA-{version}',
                'license_url': f'https://www.llama.com/llama{url_version}/license/'
            }

    # Fallback for unknown patterns (keep OpenRouter's simple approach)
    return {
        'license_info_text': '',
        'license_info_url': '',
        'license_name': 'UNKNOWN',
        'license_url': 'Unknown'
    }


def is_meta_model(provider: str, model_id: str) -> bool:
    """Check if model is from Meta"""
    return provider.lower() == 'meta' or 'llama' in model_id.lower()


# =============================================================================
# PROVIDER EXTRACTION FUNCTIONS
# =============================================================================


def extract_provider_from_name(name: str) -> Tuple[str, str]:
    """
    Extract provider and clean model name from OpenRouter format.
    
    This function extracts the provider and model name from OpenRouter's
    naming format for consistency across the pipeline.
    
    Args:
        name (str): Raw model name from Stage-1 data
                   Format: "Provider: Model Name (free)"
                   Example: "Meta: Llama 3.1 405B Instruct (free)"
    
    Returns:
        Tuple[str, str]: (provider, clean_model_name)
                        provider: "Meta", "Google", etc.
                        clean_model_name: "Llama 3.1 405B Instruct"
    
    Examples:
        >>> extract_provider_from_name("Meta: Llama 4 Maverick (free)")
        ("Meta", "Llama 4 Maverick")
        
        >>> extract_provider_from_name("Google: Gemini 2.5 Flash (free)")
        ("Google", "Gemini 2.5 Flash")
    """
    
    # Primary format: "Provider: Model Name (free)"
    if ': ' in name:
        provider_part, model_part = name.split(': ', 1)
        provider_part = provider_part.strip()
        
        # Remove (free) suffix if present
        if model_part.endswith(' (free)'):
            model_part = model_part[:-7].strip()
        
        return provider_part, model_part
    
    # Fallback for unexpected format
    # Remove (free) suffix if present
    clean_name = name
    if clean_name.endswith(' (free)'):
        clean_name = clean_name[:-7].strip()
    
    return 'Unknown', clean_name


# =============================================================================
# META MODEL IDENTIFICATION FUNCTIONS
# =============================================================================

def identify_meta_models(stage1_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify Meta models from Stage-B filtered models data using provider extraction.
    
    This function filters the complete Stage-B dataset to find only Meta models,
    using the same identification logic as the main OpenRouter pipeline for
    consistency and accuracy.
    
    Args:
        stage1_data (List[Dict]): Complete Stage-B filtered models data from JSON file
    
    Returns:
        List[Dict]: Filtered list containing only Meta models with additional
                   provider information added for processing
    
    Processing Logic:
        1. Iterate through all models in Stage-B data
        2. Extract provider from 'name' field using colon-splitting logic
        3. Filter for models where provider exactly equals "Meta"
        4. Add extracted provider info to model data for downstream processing
    """
    
    meta_models = []
    
    print(f"Scanning {len(stage1_data)} models for Meta provider...")
    
    for model in stage1_data:
        name = model.get('name', '')
        
        if not name:
            continue  # Skip models without names
            
        # Extract provider from model name
        provider, clean_model_name = extract_provider_from_name(name)
        
        # Filter for Meta models specifically
        if provider == 'Meta':
            # Add extracted information to model data
            enhanced_model = model.copy()
            enhanced_model['extracted_provider'] = provider
            enhanced_model['extracted_model_name'] = clean_model_name
            
            meta_models.append(enhanced_model)
    
    print(f"Found {len(meta_models)} Meta models")
    return meta_models


# =============================================================================
# LICENSE INFORMATION GENERATION
# =============================================================================

def generate_license_information(meta_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate complete license information for Meta models.
    
    This function processes each identified Meta model through the
    meta_licensing_mapping.py module to extract comprehensive licensing
    details using the established regex and URL construction logic.
    
    Args:
        meta_models (List[Dict]): Meta models from identify_meta_models()
    
    Returns:
        List[Dict]: Meta models with complete licensing information added
    
    License Processing:
        1. Use full 'name' field as model_id for regex version extraction
        2. Use 'canonical_slug' for HuggingFace tree URL construction
        3. Generate all 4 license fields via get_meta_license_info()
        4. Preserve original model data alongside license information
        
    License Fields Generated:
        - license_info_text: "" (blank for all Meta models)
        - license_info_url: "" (blank for all Meta models)
        - license_name: "Llama-{version}" (extracted via regex)
        - license_url: "https://huggingface.co/{canonical_slug}/tree/main"
    """
    
    licensed_models = []
    
    print(f"Generating license information for {len(meta_models)} Meta models...")
    
    for model in meta_models:
        # Get required fields for license processing
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        model_name = model.get('name', '')  # Practical for regex processing
        canonical_slug = model.get('canonical_slug', '')  # For HF URL construction
        
        print(f"Processing: {model_name}")
        
        # Generate license information using meta_licensing_mapping.py
        license_info = get_meta_license_info(
            model_id=model_name,
            canonical_slug=canonical_slug
        )
        
        # Create model record with all key fields preserved
        licensed_model = {
            'id': model.get('id', ''),
            'canonical_slug': primary_key,             # Primary identifier
            'name': model_name,
            'hugging_face_id': model.get('hugging_face_id', ''),
            'model_name': model.get('extracted_model_name', 'Unknown'),
            'license_info_text': license_info.get('license_info_text', ''),
            'license_info_url': license_info.get('license_info_url', ''),
            'license_name': license_info.get('license_name', 'Unknown'),
            'license_url': license_info.get('license_url', 'Unknown')
        }
        
        licensed_models.append(licensed_model)
        
        # Log the license extraction results for verification
        print(f"  License Name: {license_info.get('license_name', 'Unknown')}")
        print(f"  License URL: {license_info.get('license_url', 'Unknown')}")
    
    return licensed_models


# =============================================================================
# DATA LOADING AND SAVING FUNCTIONS
# =============================================================================

def load_stage1_data() -> List[Dict[str, Any]]:
    """
    Load Stage-B filtered models data from JSON file.
    
    Returns:
        List[Dict]: Complete Stage-B filtered models data
        
    Raises:
        FileNotFoundError: If 02_filtered_models.json not found
        json.JSONDecodeError: If JSON file is malformed
    """
    
    stage1_file = get_input_file_path('02_filtered_models.json')
    
    print(f"Loading Stage-B data from: {stage1_file}")
    
    try:
        with open(stage1_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(file_data, list):
            data = file_data
        elif isinstance(file_data, dict) and 'models' in file_data:
            data = file_data['models']
        else:
            raise ValueError("Unexpected data format in input file")
        
        print(f"Successfully loaded {len(data)} models from Stage-B")
        return data
        
    except FileNotFoundError:
        print(f"ERROR: Stage-B file not found: {stage1_file}")
        print("Please ensure the models filter has been run to generate Stage-B data")
        raise
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in Stage-B file: {e}")
        raise


def save_meta_licensing_results(licensed_models: List[Dict[str, Any]]) -> str:
    """
    Save Meta models with licensing information to JSON output file using standardized flat array structure.
    
    Args:
        licensed_models (List[Dict]): Meta models with complete license info
        
    Returns:
        str: Output filename
    """
    
    output_file = get_output_file_path('04_meta_licenses.json')
    
    # Standardize models to match unified structure
    standardized_models = []
    for model in licensed_models:
        standardized_model = {
            'id': model.get('id', ''),
            'canonical_slug': model.get('canonical_slug', ''),
            'original_name': model.get('name', ''),
            'hugging_face_id': model.get('hugging_face_id', ''),
            'clean_model_name': model.get('model_name', ''),
            'license_info_text': model.get('license_info_text', ''),
            'license_info_url': model.get('license_info_url', ''),
            'license_name': model.get('license_name', ''),
            'license_url': model.get('license_url', '')
        }
        standardized_models.append(standardized_model)
    
    print(f"Saving results to: {output_file}")
    
    # Create output data with metadata
    output_data = {
        "metadata": {
            "generated_at": get_ist_timestamp(),
            "total_models": len(standardized_models),
            "pipeline_stage": "D_extract_meta_licenses"
        },
        "models": standardized_models
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully saved {len(licensed_models)} Meta models with licensing information")
    
    return output_file

def generate_meta_licenses_report(licensed_models: List[Dict[str, Any]]) -> str:
    """
    Generate human-readable report of Meta models with licensing information
    
    Args:
        licensed_models: List of Meta models with complete license info
        
    Returns:
        str: Report filename
    """
    
    report_file = get_output_file_path('04_meta_licenses_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("META MODELS LICENSE EXTRACTION REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(licensed_models)}\n")
            f.write(f"  Input        : 02_filtered_models.json\n")
            f.write(f"  Processor    : step_04_extract_meta_licenses.py\n")
            f.write(f"  Output       : 04_meta_licenses.json\n\n")
            
            # License Statistics
            license_stats = {}
            for model in licensed_models:
                license_name = model.get('license_name', 'Unknown')
                license_stats[license_name] = license_stats.get(license_name, 0) + 1
            
            f.write(f"LICENSE BREAKDOWN:\n")
            for license_name in sorted(license_stats.keys()):
                count = license_stats[license_name]
                f.write(f"  {license_name}: {count} models\n")
            f.write(f"\nTotal license types: {len(license_stats)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED META MODELS WITH LICENSES:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by license name then model name
            sorted_models = sorted(
                licensed_models, 
                key=lambda x: (x.get('license_name', ''), x.get('model_name', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Standardized field ordering: identifiers → names → licenses
                f.write(f"  ID: {model.get('id', '')}\n")
                f.write(f"  Original Name: {model.get('name', '')}\n")
                f.write(f"  HuggingFace ID: {model.get('hugging_face_id', '')}\n")
                f.write(f"  Canonical Slug: {model.get('canonical_slug', '')}\n")
                f.write(f"  Clean Model Name: {model.get('model_name', '')}\n")
                f.write(f"  License Info Text: {model.get('license_info_text', '')}\n")
                f.write(f"  License Info URL: {model.get('license_info_url', '')}\n")
                f.write(f"  License Name: {model.get('license_name', '')}\n")
                f.write(f"  License URL: {model.get('license_url', '')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Meta licenses report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""


# =============================================================================
# MAIN EXECUTION FUNCTIONS
# =============================================================================

def main():
    """
    Main execution function for Meta license extraction.
    
    Execution Flow:
        1. Load Stage-1 API data
        2. Identify Meta models using provider extraction
        3. Generate licensing information for each Meta model
        4. Save comprehensive results to JSON file
        5. Provide execution summary and statistics
    
    This function orchestrates the complete process and provides
    detailed logging for monitoring and debugging purposes.
    """
    
    print("=" * 80)
    print("META MODELS LICENSE EXTRACTION FROM STAGE-1 DATA")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    # Ensure output directory exists
    ensure_output_dir_exists()

    try:
        # Step 1: Load Stage-1 data
        print("STEP 1: Loading Stage-1 API data...")
        stage1_data = load_stage1_data()
        print()
        
        # Step 2: Identify Meta models
        print("STEP 2: Identifying Meta models...")
        meta_models = identify_meta_models(stage1_data)
        
        if not meta_models:
            print("WARNING: No Meta models found in Stage-1 data")
            print("Please verify that Stage-1 data contains Meta models")
            return False
        print()
        
        # Step 3: Generate license information
        print("STEP 3: Generating license information...")
        licensed_models = generate_license_information(meta_models)
        print()
        
        # Step 4: Save results
        print("STEP 4: Saving results...")
        output_file = save_meta_licensing_results(licensed_models)
        report_file = generate_meta_licenses_report(licensed_models)
        print()
        
        # Execution Summary
        print("=" * 80)
        print("EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Total models in Stage-1: {len(stage1_data)}")
        print(f"Meta models identified: {len(meta_models)}")
        print(f"Models with licensing: {len(licensed_models)}")
        print(f"JSON output: {output_file}")
        print(f"Report output: {report_file}")
        print(f"Completed at: {datetime.now().isoformat()}")
        print()
        
        # License Summary Statistics
        license_names = [model.get('license_name', 'Unknown') for model in licensed_models]
        license_stats = {}
        for name in license_names:
            license_stats[name] = license_stats.get(name, 0) + 1
        
        print("LICENSE STATISTICS:")
        print("-" * 40)
        for license_name, count in sorted(license_stats.items()):
            print(f"  {license_name}: {count} models")
        
        print("\nSUCCESS: Meta license extraction completed successfully")
        return True
        
    except Exception as e:
        print(f"ERROR: Meta license extraction failed: {e}")
        print("Please check the error details above and retry")
        return False


if __name__ == "__main__":
    """
    Script entry point with error handling and exit code management.
    
    Usage:
        python3 extract_meta_licenses_stage1.py
        
    Exit Codes:
        0: Success - All Meta models processed successfully
        1: Failure - Error occurred during processing
        
    Prerequisites:
        - stage-1-api-data-extraction.json must exist
        - meta_licensing_mapping.py must be importable
        - Write permissions for output directory
    """
    
    success = main()
    sys.exit(0 if success else 1)