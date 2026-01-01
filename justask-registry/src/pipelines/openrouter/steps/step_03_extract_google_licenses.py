#!/usr/bin/env python3
"""
Google Models License Extraction
Processes filtered models to extract Google models and apply licensing information
Source: 2-filtered-models.json (filtered models data)
Config: google_models_licenses.json (Google license mappings)
Output: 3-google-licenses.json + human readable report
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List
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

def load_filtered_models() -> List[Dict[str, Any]]:
    """Load filtered models from Stage-B"""
    input_file = get_input_file_path('02_filtered_models.json')
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(data, list):
            models = data
        elif isinstance(data, dict) and 'models' in data:
            models = data['models']
        else:
            raise ValueError("Unexpected data format in input file")
        print(f"✓ Loaded {len(models)} filtered models from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load filtered models from {input_file}: {error}")
        return []

def load_google_license_config() -> Dict[str, Any]:
    """Load Google license configuration"""
    config_file = CONFIG_DIR / "google_models_licenses.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded Google license config from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load Google license config from {config_file}: {error}")
        return {}

def is_google_model(model_name: str) -> bool:
    """Check if model is from Google"""
    model_lower = model_name.lower()
    google_indicators = ['google:', 'gemini', 'gemma']
    
    return any(indicator in model_lower for indicator in google_indicators)

def get_google_model_type(model_name: str) -> str:
    """Determine Google model type (gemini or gemma)"""
    model_lower = model_name.lower()
    
    if 'gemini' in model_lower:
        return 'gemini'
    elif 'gemma' in model_lower:
        return 'gemma'
    else:
        return 'gemini'  # Default fallback

def extract_model_name(full_name: str) -> str:
    """Extract clean model name from full name"""
    # Remove provider prefix like "Google:"
    if ':' in full_name:
        model_part = full_name.split(':', 1)[1].strip()
    else:
        model_part = full_name.strip()
    
    # Remove (free) suffix if present
    if model_part.endswith(' (free)'):
        model_part = model_part[:-7].strip()
    
    return model_part

def get_google_license_info(model_name: str, config: Dict[str, Any]) -> Dict[str, str]:
    """Get license information for Google models using config"""
    # Determine model type
    model_type = get_google_model_type(model_name)
    
    # Get license info from config
    google_models = config.get('google_models', {})
    license_info = google_models.get(model_type, {})
    
    if not license_info:
        # Fallback if model type not found
        return {
            'license_info_text': '',
            'license_info_url': '',
            'license_name': 'Google',
            'license_url': 'https://developers.google.com/terms'
        }
    
    return {
        'license_info_text': license_info.get('license_info_text', ''),
        'license_info_url': license_info.get('license_info_url', ''),
        'license_name': license_info.get('license_name', 'Google'),
        'license_url': license_info.get('license_url', 'https://developers.google.com/terms')
    }

def process_google_models(models: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process filtered models to extract Google models with license info"""
    google_models = []
    
    print(f"Processing {len(models)} models to identify Google models...")
    
    for model in models:
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        model_name = model.get('name', '')             # Practical for detection
        
        if is_google_model(model_name):
            # Extract clean model name
            clean_model_name = extract_model_name(model_name)
            
            # Get license information
            license_info = get_google_license_info(model_name, config)
            
            # Create Google model record with all key fields preserved
            google_model = {
                'id': model.get('id', ''),
                'canonical_slug': primary_key,             # Primary identifier
                'name': model_name,
                'hugging_face_id': model.get('hugging_face_id', ''),
                'model_name': clean_model_name,
                'license_info_text': license_info['license_info_text'],
                'license_info_url': license_info['license_info_url'],
                'license_name': license_info['license_name'],
                'license_url': license_info['license_url']
            }
            
            google_models.append(google_model)
    
    print(f"✓ Identified {len(google_models)} Google models")
    return google_models

def save_google_licenses_json(google_models: List[Dict[str, Any]]) -> str:
    """Save Google models with licensing to JSON file using standardized flat array structure"""
    output_file = get_output_file_path('03_google_licenses.json')
    
    # Standardize models to match unified structure
    standardized_models = []
    for model in google_models:
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
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(standardized_models),
                "pipeline_stage": "C_extract_google_licenses"
            },
            "models": standardized_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved Google licenses to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_google_licenses_report(google_models: List[Dict[str, Any]]) -> str:
    """Generate human readable report"""
    report_file = get_output_file_path('03_google_licenses_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("GOOGLE MODELS LICENSE EXTRACTION REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(google_models)}\n")
            f.write(f"  Input        : 02_filtered_models.json\n")
            f.write(f"  Config       : google_models_licenses.json\n")
            f.write(f"  Processor    : step_03_extract_google_licenses.py\n")
            f.write(f"  Output       : 03_google_licenses.json\n\n")
            
            # License distribution
            license_distribution = {}
            for model in google_models:
                license_name = model.get('license_name', 'Unknown')
                license_distribution[license_name] = license_distribution.get(license_name, 0) + 1
            
            f.write(f"LICENSE DISTRIBUTION:\n")
            for license_name in sorted(license_distribution.keys()):
                count = license_distribution[license_name]
                f.write(f"  {license_name}: {count} models\n")
            f.write(f"\nTotal license types: {len(license_distribution)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED GOOGLE MODEL LISTINGS:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by license name then model name
            sorted_models = sorted(
                google_models, 
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
        
        print(f"✓ Google licenses report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    print("Google Models License Extraction")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    # Ensure output directory exists
    ensure_output_dir_exists()

    # Load filtered models from Stage-B
    models = load_filtered_models()
    if not models:
        print("No filtered models loaded")
        return False
    
    # Load Google license configuration
    config = load_google_license_config()
    if not config:
        print("No Google license configuration loaded")
        return False
    
    # Process Google models
    google_models = process_google_models(models, config)
    
    if not google_models:
        print("No Google models found")
        return False
    
    # Save JSON output
    json_success = save_google_licenses_json(google_models)
    
    # Generate report
    report_success = generate_google_licenses_report(google_models)
    
    if json_success and report_success:
        print("="*60)
        print("GOOGLE LICENSE EXTRACTION COMPLETE")
        print(f"Total Google models: {len(google_models)}")
        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("GOOGLE LICENSE EXTRACTION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)