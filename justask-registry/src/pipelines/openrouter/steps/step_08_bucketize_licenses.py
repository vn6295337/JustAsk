#!/usr/bin/env python3
"""
Other License Names Bucketizer
Categorizes models into opensource vs custom license buckets based on license matching
Source: 07_standardized_licenses.json (standardized license data)
Reference: opensource_license_urls.json (known opensource licenses)
Outputs: 08_opensource_licenses.json + 08_custom_licenses.json
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple
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

def load_standardized_license_data() -> List[Dict[str, Any]]:
    """Load standardized license data from Stage-G"""
    input_file = get_input_file_path('07_standardized_licenses.json')
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(data, list):
            license_data = data
        elif isinstance(data, dict) and 'models' in data:
            license_data = data['models']
        else:
            raise ValueError("Unexpected data format in input file")
        print(f"✓ Loaded {len(license_data)} models with standardized licenses from: {input_file}")
        return license_data
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load standardized license data from {input_file}: {error}")
        return []

def load_opensource_license_reference() -> Set[str]:
    """Load opensource license names from reference file"""
    reference_file = CONFIG_DIR / "opensource_license_urls.json"

    try:
        with open(reference_file, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)

        # Extract license names from the opensource_licenses array
        opensource_licenses = set()
        for license_entry in reference_data.get('opensource_licenses', []):
            license_name = license_entry.get('license_name', '').strip()
            if license_name:
                opensource_licenses.add(license_name)

        print(f"✓ Loaded {len(opensource_licenses)} opensource license names from: {reference_file}")
        return opensource_licenses

    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load opensource license reference from {reference_file}: {error}")
        return set()

def categorize_model_license(standardized_license: str, opensource_licenses: Set[str]) -> Tuple[str, str]:
    """Categorize a model's license as opensource or custom
    
    Returns:
        Tuple[str, str]: (category, matched_reference_license)
    """
    if not standardized_license or standardized_license.strip() == '':
        return 'custom', 'Unknown'
    
    license_clean = standardized_license.strip()
    
    # Exact match (case-sensitive first)
    if license_clean in opensource_licenses:
        return 'opensource', license_clean
    
    # Case-insensitive match
    for opensource_license in opensource_licenses:
        if license_clean.lower() == opensource_license.lower():
            return 'opensource', opensource_license
    
    # No match found - categorize as custom
    return 'custom', license_clean

def bucketize_licenses(license_data: List[Dict[str, Any]], 
                      opensource_licenses: Set[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Bucketize models into opensource and custom license categories"""
    opensource_models = []
    custom_models = []
    
    print(f"Bucketizing {len(license_data)} models into opensource vs custom licenses...")
    print(f"Using {len(opensource_licenses)} known opensource licenses as reference")
    
    for i, model in enumerate(license_data, 1):
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        standardized_license = model.get('standardized_license_name', '') # Practical for license categorization
        
        # Categorize license
        category, matched_reference = categorize_model_license(standardized_license, opensource_licenses)
        
        # Create simplified model record with only required fields
        enriched_model = {
            'id': model.get('id', ''),
            'canonical_slug': primary_key,             # Primary identifier
            'name': model.get('name', ''),              # Needed for clean model name extraction
            'hugging_face_id': model.get('hugging_face_id', ''),
            'license_name': standardized_license
        }
        
        # Add to appropriate bucket
        if category == 'opensource':
            opensource_models.append(enriched_model)
        else:
            custom_models.append(enriched_model)
        
        # Progress indicator
        if i % 50 == 0 or i == len(license_data):
            print(f"  Processed {i}/{len(license_data)} models...")
    
    print(f"✓ Bucketization complete: {len(opensource_models)} opensource, {len(custom_models)} custom")
    return opensource_models, custom_models

def save_opensource_bucket(opensource_models: List[Dict[str, Any]]) -> str:
    """Save opensource models to JSON file"""
    output_file = get_output_file_path('08_opensource_licenses.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(opensource_models),
                "pipeline_stage": "H_bucketize_other_license_names"
            },
            "models": opensource_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved {len(opensource_models)} opensource models to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save opensource bucket to {output_file}: {error}")
        return ""

def save_custom_bucket(custom_models: List[Dict[str, Any]]) -> str:
    """Save custom licensed models to JSON file"""
    output_file = get_output_file_path('08_custom_licenses.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(custom_models),
                "pipeline_stage": "H_bucketize_other_license_names"
            },
            "models": custom_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved {len(custom_models)} custom licensed models to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save custom bucket to {output_file}: {error}")
        return ""

def generate_opensource_report(opensource_models: List[Dict[str, Any]]) -> str:
    """Generate opensource models report"""
    report_file = get_output_file_path('08_opensource_licenses_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("OPENSOURCE LICENSE MODELS REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(opensource_models)}\n")
            f.write(f"  Input        : 07_standardized_licenses.json\n")
            f.write(f"  Reference    : opensource_license_urls.json\n")
            f.write(f"  Processor    : step_08_bucketize_licenses.py\n")
            f.write(f"  Output       : 08_opensource_licenses.json\n\n")
            
            # License distribution
            license_distribution = {}
            for model in opensource_models:
                license_name = model.get('license_name', 'Unknown')
                license_distribution[license_name] = license_distribution.get(license_name, 0) + 1
            
            f.write(f"OPENSOURCE LICENSE DISTRIBUTION:\n")
            for license_name in sorted(license_distribution.keys()):
                count = license_distribution[license_name]
                f.write(f"  {license_name}: {count} models\n")
            f.write(f"\nTotal license types: {len(license_distribution)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED OPENSOURCE MODEL LISTINGS:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by license then canonical slug
            sorted_models = sorted(
                opensource_models, 
                key=lambda x: (x.get('license_name', ''), x.get('canonical_slug', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Key fields
                f.write(f"  ID              : {model.get('id', 'Unknown')}\n")
                f.write(f"  Canonical Slug  : {model.get('canonical_slug', 'Unknown')}\n")
                f.write(f"  HuggingFace ID  : {model.get('hugging_face_id', 'Unknown')}\n")
                f.write(f"  License Name    : {model.get('license_name', 'Unknown')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Opensource report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save opensource report to {report_file}: {error}")
        return ""

def generate_custom_report(custom_models: List[Dict[str, Any]]) -> str:
    """Generate custom licensed models report"""
    report_file = get_output_file_path('08_custom_licenses_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("CUSTOM LICENSE MODELS REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(custom_models)}\n")
            f.write(f"  Input        : 07_standardized_licenses.json\n")
            f.write(f"  Reference    : opensource_license_urls.json\n")
            f.write(f"  Processor    : step_08_bucketize_licenses.py\n")
            f.write(f"  Output       : 08_custom_licenses.json\n\n")
            
            # License distribution
            license_distribution = {}
            for model in custom_models:
                license_name = model.get('license_name', 'Unknown')
                license_distribution[license_name] = license_distribution.get(license_name, 0) + 1
            
            f.write(f"CUSTOM LICENSE DISTRIBUTION:\n")
            for license_name in sorted(license_distribution.keys()):
                count = license_distribution[license_name]
                f.write(f"  {license_name}: {count} models\n")
            f.write(f"\nTotal license types: {len(license_distribution)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED CUSTOM LICENSE MODEL LISTINGS:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by license then canonical slug
            sorted_models = sorted(
                custom_models, 
                key=lambda x: (x.get('license_name', ''), x.get('canonical_slug', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Key fields
                f.write(f"  ID              : {model.get('id', 'Unknown')}\n")
                f.write(f"  Canonical Slug  : {model.get('canonical_slug', 'Unknown')}\n")
                f.write(f"  HuggingFace ID  : {model.get('hugging_face_id', 'Unknown')}\n")
                f.write(f"  License Name    : {model.get('license_name', 'Unknown')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Custom license report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save custom report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Other License Names Bucketizer")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load standardized license data from Stage-6
    license_data = load_standardized_license_data()
    if not license_data:
        print("No standardized license data loaded")
        return False
    
    # Load opensource license reference
    opensource_licenses = load_opensource_license_reference()
    if not opensource_licenses:
        print("No opensource license reference loaded")
        return False
    
    # Bucketize licenses
    opensource_models, custom_models = bucketize_licenses(license_data, opensource_licenses)
    
    # Validation check
    total_input = len(license_data)
    total_output = len(opensource_models) + len(custom_models)
    if total_input != total_output:
        print(f"WARNING: Input/Output mismatch - Input: {total_input}, Output: {total_output}")
    
    # Save JSON outputs
    opensource_json_success = save_opensource_bucket(opensource_models)
    custom_json_success = save_custom_bucket(custom_models)
    
    # Generate reports
    opensource_report_success = generate_opensource_report(opensource_models)
    custom_report_success = generate_custom_report(custom_models)
    
    if all([opensource_json_success, custom_json_success, opensource_report_success, custom_report_success]):
        print("="*60)
        print("BUCKETIZATION COMPLETE")
        print(f"Total input models: {len(license_data)}")
        print(f"Opensource models: {len(opensource_models)}")
        print(f"Custom licensed models: {len(custom_models)}")
        print(f"Opensource outputs: {opensource_json_success}, {opensource_report_success}")
        print(f"Custom outputs: {custom_json_success}, {custom_report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("BUCKETIZATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)