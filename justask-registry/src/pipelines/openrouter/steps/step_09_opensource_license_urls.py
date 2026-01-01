#!/usr/bin/env python3
"""
Opensource License URLs Enricher
Enriches opensource licensed models with official license URLs from reference
Source: 08_opensource_licenses.json (opensource models with license names)
Reference: opensource_license_urls.json (official license URLs)
Outputs: 09_opensource_license_urls.json + report with URL mappings
"""

import json
import os
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

def load_opensource_models() -> List[Dict[str, Any]]:
    """Load opensource models from Stage-H"""
    input_file = get_input_file_path('08_opensource_licenses.json')
    
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
        print(f"✓ Loaded {len(models)} opensource models from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load opensource models from {input_file}: {error}")
        return []

def load_license_url_reference() -> Dict[str, str]:
    """Load license name to URL mappings from reference file"""
    reference_file = CONFIG_DIR / "opensource_license_urls.json"

    try:
        with open(reference_file, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)

        # Create mapping from license name to license URL
        license_url_map = {}
        for license_entry in reference_data.get('opensource_licenses', []):
            license_name = license_entry.get('license_name', '').strip()
            license_url = license_entry.get('license_url', '').strip()
            if license_name and license_url:
                license_url_map[license_name] = license_url

        print(f"✓ Loaded {len(license_url_map)} license URL mappings from: {reference_file}")
        return license_url_map

    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load license URL reference from {reference_file}: {error}")
        return {}

def get_official_license_url(license_name: str, license_url_map: Dict[str, str]) -> str:
    """Get official license URL for a given license name"""
    if not license_name or license_name.strip() == '':
        return 'Unknown'
    
    license_clean = license_name.strip()
    
    # Exact match (case-sensitive first)
    if license_clean in license_url_map:
        return license_url_map[license_clean]
    
    # Case-insensitive match
    for ref_license_name, ref_license_url in license_url_map.items():
        if license_clean.lower() == ref_license_name.lower():
            return ref_license_url
    
    # No match found
    return f"Unknown (no URL for '{license_name}')"

def enrich_models_with_license_urls(models: List[Dict[str, Any]], 
                                   license_url_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """Enrich models with official license URLs"""
    enriched_models = []
    
    print(f"Enriching {len(models)} models with official license URLs...")
    print(f"Using {len(license_url_map)} license URL mappings")
    
    for i, model in enumerate(models, 1):
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        license_name = model.get('license_name', '') # Practical for URL mapping
        
        # Get official license URL
        official_license_url = get_official_license_url(license_name, license_url_map)
        
        # Create enriched model record
        enriched_model = {
            'id': model.get('id', ''),
            'canonical_slug': primary_key,             # Primary identifier
            'name': model.get('name', ''),              # Needed for clean model name extraction
            'hugging_face_id': model.get('hugging_face_id', ''),
            'license_name': license_name,
            'official_license_url': official_license_url
        }
        
        enriched_models.append(enriched_model)
        
        # Progress indicator
        if i % 50 == 0 or i == len(models):
            print(f"  Processed {i}/{len(models)} models...")
    
    return enriched_models

def save_enriched_models_json(enriched_models: List[Dict[str, Any]]) -> str:
    """Save enriched models to JSON file"""
    output_file = get_output_file_path('09_opensource_license_urls.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(enriched_models),
                "pipeline_stage": "I_opensource_license_urls"
            },
            "models": enriched_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved {len(enriched_models)} enriched models to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_license_urls_report(enriched_models: List[Dict[str, Any]], 
                                license_url_map: Dict[str, str]) -> str:
    """Generate comprehensive report"""
    report_file = get_output_file_path('09_opensource_license_urls_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("OPENSOURCE LICENSE URLS ENRICHMENT REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(enriched_models)}\n")
            f.write(f"  Input        : 08_opensource_licenses.json\n")
            f.write(f"  Reference    : opensource_license_urls.json\n")
            f.write(f"  Processor    : step_09_opensource_license_urls.py\n")
            f.write(f"  Output       : 09_opensource_license_urls.json\n\n")
            
            # URL mapping statistics
            successful_mappings = 0
            failed_mappings = 0
            url_stats = {}
            
            for model in enriched_models:
                official_url = model.get('official_license_url', '')
                license_name = model.get('license_name', '')
                
                if official_url.startswith('Unknown'):
                    failed_mappings += 1
                    category = 'Failed mapping'
                else:
                    successful_mappings += 1
                    category = f'{license_name} → Official URL'
                
                url_stats[category] = url_stats.get(category, 0) + 1
            
            f.write(f"URL MAPPING STATISTICS:\n")
            f.write(f"  Successful URL mappings: {successful_mappings}\n")
            f.write(f"  Failed URL mappings: {failed_mappings}\n")
            if enriched_models:
                f.write(f"  Success rate: {(successful_mappings/len(enriched_models)*100):.1f}%\n\n")
            else:
                f.write(f"  Success rate: 0.0%\n\n")
            
            # License URL distribution
            license_url_distribution = {}
            for model in enriched_models:
                license_name = model.get('license_name', 'Unknown')
                official_url = model.get('official_license_url', 'Unknown')
                key = f"{license_name} → {official_url}"
                license_url_distribution[key] = license_url_distribution.get(key, 0) + 1
            
            f.write(f"LICENSE URL DISTRIBUTION:\n")
            for mapping in sorted(license_url_distribution.keys()):
                count = license_url_distribution[mapping]
                f.write(f"  {mapping}: {count} models\n")
            f.write(f"\nTotal mapping types: {len(license_url_distribution)}\n\n")
            
            # Failed mappings analysis
            failed_licenses = set()
            for model in enriched_models:
                official_url = model.get('official_license_url', '')
                if official_url.startswith('Unknown'):
                    license_name = model.get('license_name', 'Unknown')
                    failed_licenses.add(license_name)
            
            if failed_licenses:
                f.write(f"LICENSES WITHOUT URL MAPPINGS:\n")
                for license_name in sorted(failed_licenses):
                    f.write(f"  {license_name}\n")
                f.write(f"\nTotal unmapped licenses: {len(failed_licenses)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED MODEL LICENSE URL MAPPINGS:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by license name then canonical slug
            sorted_models = sorted(
                enriched_models, 
                key=lambda x: (x.get('license_name', ''), x.get('canonical_slug', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Key fields
                f.write(f"  ID                     : {model.get('id', 'Unknown')}\n")
                f.write(f"  Canonical Slug         : {model.get('canonical_slug', 'Unknown')}\n")
                f.write(f"  HuggingFace ID         : {model.get('hugging_face_id', 'Unknown')}\n")
                f.write(f"  License Name           : {model.get('license_name', 'Unknown')}\n")
                f.write(f"  Official License URL   : {model.get('official_license_url', 'Unknown')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ License URLs report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Opensource License URLs Enricher")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load opensource models from Stage-H
    models = load_opensource_models()
    if not models:
        print("No opensource models loaded")
        return False
    
    # Load license URL reference
    license_url_map = load_license_url_reference()
    if not license_url_map:
        print("No license URL reference loaded")
        return False
    
    # Enrich models with license URLs
    enriched_models = enrich_models_with_license_urls(models, license_url_map)
    
    if not enriched_models:
        print("No models enriched")
        return False
    
    # Save JSON output
    json_success = save_enriched_models_json(enriched_models)
    
    # Generate report
    report_success = generate_license_urls_report(enriched_models, license_url_map)
    
    if json_success and report_success:
        print("="*60)
        print("LICENSE URL ENRICHMENT COMPLETE")
        print(f"Total models enriched: {len(enriched_models)}")
        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("LICENSE URL ENRICHMENT FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)