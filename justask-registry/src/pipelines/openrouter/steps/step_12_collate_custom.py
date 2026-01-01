#!/usr/bin/env python3
"""
Custom License Information Collator
Brings together custom license information from pipeline stages
Sources:
- 10_custom_license_urls.json (custom license URLs from HF)
Output: 12_collated_custom_licenses.json + comprehensive report
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path for imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    get_ist_timestamp,
    ensure_output_dir_exists,
    set_current_pipeline,
    get_project_root,
)
set_current_pipeline('openrouter')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "openrouter"

def load_special_mappings() -> Dict[str, str]:
    """Load GPT OSS special mappings from config file"""
    config_path = CONFIG_DIR / "provider_enrichment.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('special_mappings', {}).get('oss_models', {})
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load special mappings from {config_path}: {error}")
        return {}

def extract_model_name(full_name: str) -> str:
    """Extract clean model name from full name"""
    # Remove provider prefix like "Google:", "Meta:", etc.
    if ':' in full_name:
        model_part = full_name.split(':', 1)[1].strip()
    else:
        model_part = full_name.strip()
    
    # Remove (free) suffix if present
    if model_part.endswith(' (free)'):
        model_part = model_part[:-7].strip()
    
    return model_part

def load_json_file(filename: str, description: str) -> List[Dict[str, Any]]:
    """Load JSON file with error handling"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(data, list):
            models = data
        elif isinstance(data, dict) and 'models' in data:
            models = data['models']
        else:
            raise ValueError("Unexpected data format in input file")
        print(f"✓ Loaded {len(models)} items from {description}: {filename}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load {description} from {filename}: {error}")
        return []

def create_canonical_slug_index(models: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Create index by canonical_slug for fast lookups"""
    index = {}
    for model in models:
        canonical_slug = model.get('canonical_slug', '')
        if canonical_slug:
            index[canonical_slug] = model
    return index

def collate_custom_license_information() -> List[Dict[str, Any]]:
    """Collate custom license information from Step 10 and Step 05"""
    
    # Load source files
    print("Loading source files...")
    
    # Step 10: Custom license URLs from HF
    custom_models = load_json_file(
        get_input_file_path('10_custom_license_urls.json'),
        'custom license URLs'
    )
    
    # Step 05: Original names for all models
    stage_e_models = load_json_file(
        get_input_file_path('05_hf_license_urls.json'),
        'license info URLs (for original names)'
    )
    
    # Create index for Stage-E data
    stage_e_index = create_canonical_slug_index(stage_e_models)
    
    print(f"Found {len(custom_models)} custom license models")
    
    # Collate information for each model
    collated_models = []
    
    for model in custom_models:
        canonical_slug = model.get('canonical_slug', '')
        stage_e_data = stage_e_index.get(canonical_slug, {})
        
        # Get the original name (prioritize Stage-E which has full names)
        original_name = (stage_e_data.get('name') or
                        model.get('name') or
                        'Unknown')
        
        # Extract clean model name
        clean_model_name = extract_model_name(original_name) if original_name != 'Unknown' else 'Unknown'
        
        # Create simplified model record with only required fields
        collated_model = {
            # Primary identification
            'id': model.get('id', 'Unknown'),
            'canonical_slug': model.get('canonical_slug', 'Unknown'),
            'original_name': original_name,
            'hugging_face_id': model.get('hugging_face_id', ''),
            'clean_model_name': clean_model_name,

            # License information
            'license_info_text': '',  # Always blank for custom licenses
            'license_info_url': '',   # Always blank for custom licenses
            'license_name': model.get('license_name', 'Unknown'),
            'license_url': model.get('license_url', '')
        }
        
        collated_models.append(collated_model)
    
    print(f"✓ Collated license information for {len(collated_models)} custom license models")
    return collated_models

def save_collated_data(collated_models: List[Dict[str, Any]]) -> str:
    """Save collated data to JSON file"""
    output_file = get_output_file_path('12_collated_custom_licenses.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(collated_models),
                "pipeline_stage": "L_collate_custom_licenses"
            },
            "models": collated_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved {len(collated_models)} collated models to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_collation_report(collated_models: List[Dict[str, Any]]) -> str:
    """Generate comprehensive collation report"""
    report_file = get_output_file_path('12_collated_custom_licenses_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("COLLATED CUSTOM LICENSE INFORMATION REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models        : {len(collated_models)}\n")
            f.write(f"  Input sources       : 10_custom_license_urls.json + 05_hf_license_urls.json\n")
            f.write(f"  Processor           : step_12_collate_custom.py\n")
            f.write(f"  Output              : 12_collated_custom_licenses.json\n\n")
            
            # License name distribution
            license_distribution = {}
            for model in collated_models:
                license_name = model.get('license_name', 'Unknown')
                license_distribution[license_name] = license_distribution.get(license_name, 0) + 1
            
            f.write(f"CUSTOM LICENSE DISTRIBUTION:\n")
            # Sort by count descending, then by name
            sorted_licenses = sorted(license_distribution.items(), key=lambda x: (-x[1], x[0]))
            for license_name, count in sorted_licenses:
                f.write(f"  {count:2d} models: {license_name}\n")
            f.write(f"\nTotal unique license types: {len(license_distribution)}\n\n")
            
            # License URL type distribution
            url_type_distribution = {}
            for model in collated_models:
                # Get URL type from original model data
                url_type = 'Unknown'
                if model.get('license_url', ''):
                    if '/blob/main/LICENSE' in model['license_url']:
                        url_type = 'LICENSE file'
                    elif '/blob/main/README.md' in model['license_url']:
                        url_type = 'README.md file'
                    elif model['license_url'].count('/') == 3:
                        url_type = 'Base repository'
                    else:
                        url_type = 'Other'
                else:
                    url_type = 'No URL'
                url_type_distribution[url_type] = url_type_distribution.get(url_type, 0) + 1
            
            f.write(f"LICENSE URL TYPE DISTRIBUTION:\n")
            # Sort by priority order
            priority_order = ['LICENSE file', 'README.md file', 'Base repository', 'Other', 'No URL', 'Unknown']
            for url_type in priority_order:
                count = url_type_distribution.get(url_type, 0)
                if count > 0:
                    f.write(f"  {count:2d} models: {url_type}\n")
            f.write(f"\nTotal URL types: {len(url_type_distribution)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED CUSTOM MODEL INFORMATION:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by license name, then canonical slug
            sorted_models = sorted(
                collated_models,
                key=lambda x: (x.get('license_name', ''), 
                              x.get('canonical_slug', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Standardized field ordering: identifiers → names → licenses
                f.write(f"  ID: {model.get('id', '')}\n")
                f.write(f"  Original Name: {model.get('original_name', '')}\n")
                f.write(f"  HuggingFace ID: {model.get('hugging_face_id', '')}\n")
                f.write(f"  Canonical Slug: {model.get('canonical_slug', '')}\n")
                f.write(f"  Clean Model Name: {model.get('clean_model_name', '')}\n")
                f.write(f"  License Info Text: {model.get('license_info_text', '')}\n")
                f.write(f"  License Info URL: {model.get('license_info_url', '')}\n")
                f.write(f"  License Name: {model.get('license_name', '')}\n")
                f.write(f"  License URL: {model.get('license_url', '')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Collation report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Custom License Information Collator")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Collate custom license information from Step 10
    collated_models = collate_custom_license_information()
    
    if not collated_models:
        print("No models to collate")
        return False
    
    # Save JSON output
    json_success = save_collated_data(collated_models)
    
    # Generate comprehensive report
    report_success = generate_collation_report(collated_models)
    
    if json_success and report_success:
        print(f"SUCCESS: Collated {len(collated_models)} custom license models - JSON: {json_success} | Report: {report_success}")
        return True
    else:
        print("CUSTOM LICENSE INFORMATION COLLATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)