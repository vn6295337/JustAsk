#!/usr/bin/env python3
"""
Custom License URLs Enricher
Enriches custom licensed models with HuggingFace license URLs using prioritization
Source: 08_custom_licenses.json (custom models with license names)
Priority: LICENSE → README.md → Base repository URLs
Outputs: 10_custom_license_urls.json + report with URL mappings
"""

import json
import os
import time
import requests
from datetime import datetime
from typing import Any, Dict, List, Tuple
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

def load_license_url_overrides() -> Dict[str, str]:
    """Load custom license URL overrides for non-Meta models"""
    config_file = CONFIG_DIR / "custom_license_url_overrides.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        overrides = config.get('license_url_overrides', {})
        print(f"✓ Loaded {len(overrides)} license URL overrides from: {config_file}")
        return overrides

    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load license URL overrides from {config_file}: {error}")
        return {}

def get_override_license_url(license_name: str, overrides: Dict[str, str]) -> str:
    """Get override license URL if available for this license type"""
    if not license_name or not overrides:
        return ''

    license_clean = license_name.strip()

    # Exact match (case-sensitive first)
    if license_clean in overrides:
        return overrides[license_clean]

    # Case-insensitive match
    for override_license, override_url in overrides.items():
        if license_clean.lower() == override_license.lower():
            return override_url

    return ''

def load_custom_models() -> List[Dict[str, Any]]:
    """Load custom models from Stage-H"""
    input_file = get_input_file_path('08_custom_licenses.json')
    
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
        print(f"✓ Loaded {len(models)} custom models from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load custom models from {input_file}: {error}")
        return []

def check_url_accessible(url: str) -> bool:
    """Check if a URL is accessible with a HEAD request"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(url, timeout=10, allow_redirects=True, headers=headers)
        return response.status_code == 200
    except (requests.RequestException, requests.Timeout):
        return False

def get_license_url_with_priority(hf_id: str) -> Tuple[str, str]:
    """Get license URL for HuggingFace models with 3-tier priority system
    
    Returns:
        Tuple[str, str]: (license_url, url_type)
    """
    if not hf_id or not hf_id.strip():
        return 'Unknown', 'No HF ID'
    
    base_url = f"https://huggingface.co/{hf_id}"
    
    # Priority 1: Try LICENSE file first
    license_url = f"{base_url}/blob/main/LICENSE"
    if check_url_accessible(license_url):
        return license_url, 'LICENSE file'
    
    # Priority 2: If LICENSE not accessible, try README.md
    readme_url = f"{base_url}/blob/main/README.md"
    if check_url_accessible(readme_url):
        return readme_url, 'README.md file'
    
    # Priority 3: If README.md not accessible, try base repo page
    if check_url_accessible(base_url):
        return base_url, 'Base repository'
    
    # Fallback: Return Unknown if no valid repository page
    return 'Unknown', 'Inaccessible'

def enrich_models_with_license_urls(models: List[Dict[str, Any]], overrides: Dict[str, str]) -> List[Dict[str, Any]]:
    """Enrich models with license URLs, using official overrides or HuggingFace URLs"""
    enriched_models = []

    print(f"Enriching {len(models)} custom models with license URLs...")
    if overrides:
        print(f"Using {len(overrides)} license URL overrides for known license types")
    print("Fallback priority for non-override models: LICENSE → README.md → Base repository")

    for i, model in enumerate(models, 1):
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        hf_id = model.get('hugging_face_id', '')       # Practical for URL generation
        license_name = model.get('license_name', '')   # Practical for override checking

        # Check for license URL override first
        override_url = get_override_license_url(license_name, overrides)

        if override_url:
            # Use official license URL override
            license_url = override_url
            url_type = 'Official override'
        else:
            # Get license URL using HuggingFace priority system
            license_url, url_type = get_license_url_with_priority(hf_id)

        # Create enriched model record
        enriched_model = {
            'id': model.get('id', ''),
            'canonical_slug': primary_key,             # Primary identifier
            'name': model.get('name', ''),              # Needed for clean model name extraction
            'hugging_face_id': hf_id,
            'license_name': license_name,
            'license_url': license_url,
            'license_url_type': url_type
        }

        enriched_models.append(enriched_model)

        # Progress indicator with URL type
        print(f"  {i}/{len(models)}: {model.get('name', 'Unknown')[:50]}... → {url_type}")

        # Small delay to be respectful to HuggingFace (only if fetching HF URLs)
        if url_type != 'Official override' and i % 10 == 0:
            time.sleep(1)

    return enriched_models

def save_enriched_models_json(enriched_models: List[Dict[str, Any]]) -> str:
    """Save enriched models to JSON file"""
    output_file = get_output_file_path('10_custom_license_urls.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(enriched_models),
                "pipeline_stage": "J_custom_license_urls"
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

def generate_license_urls_report(enriched_models: List[Dict[str, Any]]) -> str:
    """Generate comprehensive report"""
    report_file = get_output_file_path('10_custom_license_urls_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("CUSTOM LICENSE URLS ENRICHMENT REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(enriched_models)}\n")
            f.write(f"  Input        : 08_custom_licenses.json\n")
            f.write(f"  Priority     : LICENSE → README.md → Base repository\n")
            f.write(f"  Processor    : step_10_custom_license_urls.py\n")
            f.write(f"  Output       : 10_custom_license_urls.json\n\n")
            
            # URL type statistics
            url_type_stats = {}
            for model in enriched_models:
                url_type = model.get('license_url_type', 'Unknown')
                url_type_stats[url_type] = url_type_stats.get(url_type, 0) + 1
            
            f.write(f"LICENSE URL TYPE DISTRIBUTION:\n")
            for url_type in ['Official override', 'LICENSE file', 'README.md file', 'Base repository', 'Inaccessible', 'No HF ID']:
                count = url_type_stats.get(url_type, 0)
                if count > 0:
                    f.write(f"  {url_type}: {count} models\n")
            f.write(f"\nTotal URL types: {len(url_type_stats)}\n\n")
            
            # Success rate analysis
            successful_urls = sum(1 for model in enriched_models 
                                if model.get('license_url', 'Unknown') != 'Unknown')
            if enriched_models:
                success_rate = (successful_urls / len(enriched_models)) * 100
                f.write(f"URL RESOLUTION STATISTICS:\n")
                f.write(f"  Successful URL resolutions: {successful_urls}\n")
                f.write(f"  Failed URL resolutions: {len(enriched_models) - successful_urls}\n")
                f.write(f"  Success rate: {success_rate:.1f}%\n\n")
            
            # License name distribution
            license_distribution = {}
            for model in enriched_models:
                license_name = model.get('license_name', 'Unknown')
                license_distribution[license_name] = license_distribution.get(license_name, 0) + 1
            
            f.write(f"CUSTOM LICENSE DISTRIBUTION:\n")
            for license_name in sorted(license_distribution.keys()):
                count = license_distribution[license_name]
                f.write(f"  {license_name}: {count} models\n")
            f.write(f"\nTotal license types: {len(license_distribution)}\n\n")
            
            # Failed URL resolution analysis
            failed_models = [model for model in enriched_models 
                           if model.get('license_url', 'Unknown') == 'Unknown']
            
            if failed_models:
                f.write(f"MODELS WITH FAILED URL RESOLUTION ({len(failed_models)} models):\n")
                for model in failed_models:
                    model_name = model.get('name', 'Unknown')
                    hf_id = model.get('hugging_face_id', 'Unknown')
                    url_type = model.get('license_url_type', 'Unknown')
                    f.write(f"  {model_name}\n")
                    f.write(f"    HF ID: {hf_id}\n")
                    f.write(f"    Reason: {url_type}\n")
                f.write(f"\n")
            
            # Detailed model listings
            f.write("DETAILED MODEL LICENSE URL MAPPINGS:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by URL type priority then model name
            def get_sort_priority(model):
                url_type = model.get('license_url_type', 'Unknown')
                priority_map = {
                    'LICENSE file': 1,
                    'README.md file': 2,
                    'Base repository': 3,
                    'Inaccessible': 4,
                    'No HF ID': 5
                }
                priority = priority_map.get(url_type, 6)
                return (priority, model.get('canonical_slug', ''))
            
            sorted_models = sorted(enriched_models, key=get_sort_priority)
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Key fields
                f.write(f"  ID                     : {model.get('id', 'Unknown')}\n")
                f.write(f"  Canonical Slug         : {model.get('canonical_slug', 'Unknown')}\n")
                f.write(f"  HuggingFace ID         : {model.get('hugging_face_id', 'Unknown')}\n")
                f.write(f"  License Name           : {model.get('license_name', 'Unknown')}\n")
                f.write(f"  License URL            : {model.get('license_url', 'Unknown')}\n")
                f.write(f"  License URL Type       : {model.get('license_url_type', 'Unknown')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Custom license URLs report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""

    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Custom License URLs Enricher")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    # Load license URL overrides for non-Meta models with known license types
    overrides = load_license_url_overrides()
    print()

    # Load custom models from Stage-H
    models = load_custom_models()
    if not models:
        print("No custom models loaded")
        return False

    # Enrich models with license URLs
    enriched_models = enrich_models_with_license_urls(models, overrides)

    if not enriched_models:
        print("No models enriched")
        return False

    # Save JSON output
    json_success = save_enriched_models_json(enriched_models)

    # Generate report
    report_success = generate_license_urls_report(enriched_models)

    if json_success and report_success:
        print("="*60)
        print("CUSTOM LICENSE URL ENRICHMENT COMPLETE")
        print(f"Total models enriched: {len(enriched_models)}")

        # Summary statistics
        url_type_counts = {}
        for model in enriched_models:
            url_type = model.get('license_url_type', 'Unknown')
            url_type_counts[url_type] = url_type_counts.get(url_type, 0) + 1

        print("URL Type Distribution:")
        for url_type, count in sorted(url_type_counts.items()):
            print(f"  {url_type}: {count} models")

        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("CUSTOM LICENSE URL ENRICHMENT FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)