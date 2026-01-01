#!/usr/bin/env python3
"""
Other License Info URLs Fetcher from HuggingFace
Fetches license info URLs from HuggingFace repositories for other models
Source: 02_filtered_models.json
Outputs: 05_hf_license_urls.json + report
"""

import json
import os
import time
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import requests

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


def check_url_accessible(url: str, max_retries: int = 2) -> bool:
    """Check if a URL is accessible with a HEAD request, with retry logic for rate limiting"""
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.head(url, timeout=5, allow_redirects=True, headers=headers)

            if response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3  # 3, 6 seconds
                    time.sleep(wait_time)
                    continue
                return False

            return response.status_code == 200
        except (requests.RequestException, requests.Timeout):
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return False
    return False


# =============================================================================
# HUGGINGFACE MODELS SECTION
# =============================================================================

def get_huggingface_license_info(hf_id: str) -> str:
    """Get license info URL for HuggingFace models with 3-tier priority system"""
    
    # HUGGINGFACE MODELS - Priority-Based LICENSE Detection
    if not hf_id or not hf_id.strip():
        return "Unknown"
    
    base_url = f"https://huggingface.co/{hf_id}"
    
    # Priority 1: Try LICENSE first
    license_url = f"{base_url}/blob/main/LICENSE"
    if check_url_accessible(license_url):
        return license_url
    
    # Priority 2: If LICENSE not accessible, try README.md
    readme_url = f"{base_url}/blob/main/README.md"
    if check_url_accessible(readme_url):
        return readme_url
    
    # Priority 3: If README.md not accessible, try base repo page
    if check_url_accessible(base_url):
        return base_url
    
    # Fallback: Return Unknown if no valid repository page
    return "Unknown"



def load_models_data() -> List[Dict[str, Any]]:
    """Load models data from 02_filtered_models.json"""
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
        print(f"✓ Loaded {len(models)} models from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load models from {input_file}: {error}")
        return []

def should_skip_model(name: str) -> bool:
    """Check if model should be skipped (Google, Meta)"""
    name_lower = name.lower()
    skip_providers = ['google:', 'meta:']
    
    for provider in skip_providers:
        if name_lower.startswith(provider):
            return True
    return False


def process_models_for_license_info(models: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Process models to extract license info URLs (excluding Google/Meta)"""
    processed_models = []
    
    print(f"Processing {len(models)} models for license info URLs...")
    
    for i, model in enumerate(models, 1):
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        name = model.get('name', '')                   # Practical for skip detection
        hf_id = model.get('hugging_face_id', '')       # Practical for HF API calls
        
        # Skip Google and Meta models (they have dedicated handlers)
        if should_skip_model(name):
            continue
        
        # Skip models without HuggingFace IDs
        if not hf_id:
            continue
        
        # Get license info URL using 3-tier priority system
        license_info_url = get_huggingface_license_info(hf_id)
        
        processed_model = {
            'id': model.get('id', ''),
            'canonical_slug': primary_key,             # Primary identifier
            'name': name,
            'hugging_face_id': hf_id,
            'license_info_url': license_info_url
        }
        
        processed_models.append(processed_model)
    
    print(f"✓ Processed {len(processed_models)} models (excluding Google/Meta)")
    return processed_models

def save_license_info_json(processed_models: List[Dict[str, str]]) -> str:
    """Save processed models to JSON file"""
    output_file = get_output_file_path('05_hf_license_urls.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(processed_models),
                "pipeline_stage": "E_fetch_other_license_info_urls_from_hf"
            },
            "models": processed_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved license info to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_license_info_report(processed_models: List[Dict[str, str]]) -> str:
    """Generate human-readable report"""
    report_file = get_output_file_path('05_hf_license_urls_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("OTHER LICENSE INFO URLS REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(processed_models)}\n")
            f.write(f"  Input        : 02_filtered_models.json\n")
            f.write(f"  Processor    : step_05_fetch_hf_license_urls.py\n")
            f.write(f"  Output       : 05_hf_license_urls.json\n\n")
            
            # URL Status Statistics
            url_stats = {}
            for model in processed_models:
                url = model.get('license_info_url', 'Unknown')
                if url.startswith('https://huggingface.co/') and '/blob/main/LICENSE' in url:
                    category = 'LICENSE file'
                elif url.startswith('https://huggingface.co/') and '/blob/main/README.md' in url:
                    category = 'README.md file'
                elif url.startswith('https://huggingface.co/') and url.count('/') == 3:
                    category = 'Base repository'
                elif url == 'Unknown':
                    category = 'Unknown/Inaccessible'
                else:
                    category = 'Other'
                
                url_stats[category] = url_stats.get(category, 0) + 1
            
            f.write(f"LICENSE INFO URL BREAKDOWN:\n")
            # Sort by count descending, then by category name
            sorted_categories = sorted(url_stats.items(), key=lambda x: (-x[1], x[0]))
            for category, count in sorted_categories:
                f.write(f"  {count:2d} models: {category}\n")
            f.write(f"\nTotal categories: {len(url_stats)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED MODEL LICENSE INFO URLS:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by license info URL category then model name
            def get_sort_key(model):
                url = model.get('license_info_url', 'Unknown')
                if 'LICENSE' in url:
                    priority = 1
                elif 'README.md' in url:
                    priority = 2
                elif url != 'Unknown' and url.startswith('https://huggingface.co/'):
                    priority = 3
                else:
                    priority = 4
                return (priority, model.get('name', ''))
            
            sorted_models = sorted(processed_models, key=get_sort_key)
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Key fields
                f.write(f"  ID              : {model.get('id', 'Unknown')}\n")
                f.write(f"  Canonical Slug  : {model.get('canonical_slug', 'Unknown')}\n")
                f.write(f"  HuggingFace ID  : {model.get('hugging_face_id', 'Unknown')}\n")
                f.write(f"  License Info URL: {model.get('license_info_url', 'Unknown')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ License info report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    print("Other License Info URLs Fetcher from HuggingFace")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    # Ensure output directory exists
    ensure_output_dir_exists()

    # Load models data
    models = load_models_data()
    if not models:
        print("No models loaded from input file")
        return False
    
    # Process models for license info URLs
    processed_models = process_models_for_license_info(models)
    
    if not processed_models:
        print("No models processed")
        return False
    
    # Save JSON output
    json_success = save_license_info_json(processed_models)
    
    # Generate report
    report_success = generate_license_info_report(processed_models)
    
    if json_success and report_success:
        print("="*60)
        print("PROCESSING COMPLETE")
        print(f"Total models: {len(processed_models)}")
        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("PROCESSING FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)