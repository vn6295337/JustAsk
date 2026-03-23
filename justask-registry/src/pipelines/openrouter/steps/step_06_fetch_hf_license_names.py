#!/usr/bin/env python3
"""
Extract license names from HuggingFace pages for filtered models with HF IDs
Source: 05_hf_license_urls.json
Outputs: 06_hf_license_names.json + report
Excludes Google and Meta models (they have dedicated handlers)
"""

import json
import os
import time
import re
import requests
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from huggingface_hub import HfApi

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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Check multiple .env locations
    env_paths = [
        Path("/home/vn6295337/.env"),
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent / ".env"
    ]

    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
    # No warning - env vars may come from GitHub Actions
except ImportError:
    pass


def extract_license_from_url(url: str, source_label: str = "URL", max_retries: int = 3) -> str:
    """Extract license from a given URL with web scraping"""
    if not url:
        return "Unknown"

    for attempt in range(max_retries):
        try:
            # Add headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                    print(f"    Rate limited for {source_label}, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    return f"HTTP 429 (Rate Limited after {max_retries} attempts)"

            if response.status_code != 200:
                return f"HTTP {response.status_code}"

            content = response.text

            # Look for license information in the specific HuggingFace HTML structure
            # IMPORTANT: HuggingFace uses "license":"other" + "license_name":"actual-license"
            # so we must check license_name FIRST before falling back to license
            # NOTE: HuggingFace embeds JSON with HTML entities (&quot; instead of ")
            patterns = [
                r'<span class="-mr-1 text-gray-400">License:</span>\s*<span>([^<]+)</span>',  # HF license structure
                r'<span[^>]*>License:</span>[^<]*<span[^>]*>([^<]+)</span>',  # General license span structure
                r'license_name&quot;:&quot;([^&]+)&quot;',  # HTML-escaped JSON license_name (HF primary format)
                r'"license_name"\s*:\s*"([^"]+)"',  # JSON license_name field (non-escaped)
                r'license&quot;:&quot;([^&]+)&quot;',  # HTML-escaped JSON license (fallback)
                r'"license"\s*:\s*"([^"]+)"',  # JSON license field (fallback)
                r'<dt[^>]*>License</dt>\s*<dd[^>]*>([^<]+)</dd>',  # Definition list structure
                r'License:\s*([A-Za-z0-9\-\.\s]+)',  # Plain text license
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    license_name = match.group(1).strip()
                    # Skip 'other' if found - it means HF has a custom license in license_name field
                    if license_name.lower() == 'other':
                        continue
                    return license_name

            return "Unknown"

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"    Request failed for {source_label}, retrying in 3s (attempt {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(3)
                continue
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Parse Error: {str(e)}"

    return "Unknown"


def extract_license_from_hf_page(hf_id: str, max_retries: int = 3) -> str:
    """Extract license from HuggingFace base repo page with web scraping (fallback for 'other' licenses)"""
    if not hf_id:
        return "Unknown"

    url = f"https://huggingface.co/{hf_id}"
    return extract_license_from_url(url, f"base repo page ({hf_id})", max_retries)


def extract_license_from_hf_api(hf_id: str, license_info_url: str = None) -> str:
    """Extract license from HuggingFace using official Hub API, with web scraping fallback for 'other' licenses"""
    if not hf_id:
        return "Unknown"

    try:
        api = HfApi(token=os.getenv('HUGGINGFACE_API_KEY'))
        repo_info = api.repo_info(hf_id)

        if repo_info.cardData:
            license_value = repo_info.cardData.license or 'Unknown'

            # If license is 'other', use web scraping to get the actual license name
            if license_value.lower() == 'other':
                print(f"  License is 'other', attempting web scraping for {hf_id}")

                # Try license file URL first (from script E's output)
                if license_info_url:
                    print(f"    Trying license file URL: {license_info_url}")
                    scraped_license = extract_license_from_url(license_info_url, f"license file ({hf_id})")
                    if scraped_license not in ["Unknown", "HTTP 404", "HTTP 429 (Rate Limited after 3 attempts)"]:
                        print(f"    Successfully extracted from license file: {scraped_license}")
                        return scraped_license
                    else:
                        print(f"    License file scraping failed ({scraped_license}), falling back to base repo page")

                # Fallback to base repo page
                print(f"    Trying base repo page scraping")
                scraped_license = extract_license_from_hf_page(hf_id)
                return scraped_license if scraped_license != "Unknown" else license_value

            return license_value
        return 'Unknown'
    except Exception as e:
        print(f"API error for {hf_id}: {str(e)}")
        return 'Unknown'


def should_skip_model(name: str) -> bool:
    """Check if model should be skipped (Google, Meta)"""
    name_lower = name.lower()
    skip_providers = ['google:', 'meta:']
    
    for provider in skip_providers:
        if name_lower.startswith(provider):
            return True
    return False


def main():
    """Extract licenses from HuggingFace pages for non-Google/Meta models"""

    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Loading stage-E license info data...")
    
    # Load the JSON data
    with open(get_input_file_path('05_hf_license_urls.json'), 'r') as f:
        data = json.load(f)

    # Handle both old format (list) and new format (dict with metadata)
    if isinstance(data, list):
        models = data
    elif isinstance(data, dict) and 'models' in data:
        models = data['models']
    else:
        raise ValueError("Unexpected data format in input file")

    # Filter models with HuggingFace IDs, excluding Google/Meta
    # Also create a mapping of hf_id to license_info_url
    target_models = []
    hf_id_to_license_url = {}

    for model in models:
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        name = model.get('name', '')                   # Practical for skip detection
        hf_id = model.get('hugging_face_id', '')       # Practical for HF API calls
        license_info_url = model.get('license_info_url', '')  # License file URL from script E

        if hf_id and not should_skip_model(name):
            target_models.append({
                'id': model.get('id', ''),
                'canonical_slug': primary_key,
                'name': name,
                'hugging_face_id': hf_id
            })
            # Store mapping for license URL lookup
            if license_info_url:
                hf_id_to_license_url[hf_id] = license_info_url

    print(f"Found {len(target_models)} models to process (excluding Google/Meta)")
    print(f"Found {len(hf_id_to_license_url)} license file URLs from script E")

    # Extract licenses
    results = []

    for i, model in enumerate(target_models, 1):
        print(f"Processing {i}/{len(target_models)}: {model['name'][:60]}...")

        # Get license_info_url from mapping if available
        hf_id = model['hugging_face_id']
        license_info_url = hf_id_to_license_url.get(hf_id)

        license_info = extract_license_from_hf_api(hf_id, license_info_url)

        results.append({
            'id': model['id'],
            'canonical_slug': model['canonical_slug'],     # Primary identifier
            'name': model['name'],
            'hugging_face_id': model['hugging_face_id'],
            'extracted_license': license_info
        })

        # Small delay to be respectful to the API
        time.sleep(0.1)  # 100ms delay between API calls
    
    # Write results to JSON file
    json_output_file = get_output_file_path('06_hf_license_names.json')

    # Create output data with metadata
    output_data = {
        "metadata": {
            "generated_at": get_ist_timestamp(),
            "total_models": len(results),
            "pipeline_stage": "F_fetch_other_license_names_from_hf"
        },
        "models": results
    }

    with open(json_output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Write human-readable report
    report_output_file = get_output_file_path('06_hf_license_names_report.txt')
    
    with open(report_output_file, 'w') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("OTHER MODEL LICENSE NAME EXTRACTIONS REPORT\n")
        f.write(f"Generated: {get_ist_timestamp()}\n")
        f.write("=" * 80 + "\n\n")
        
        # Summary
        f.write(f"SUMMARY:\n")
        f.write(f"  Total models : {len(results)}\n")
        f.write(f"  Input        : 05_hf_license_urls.json\n")
        f.write(f"  Processor    : step_06_fetch_hf_license_names.py\n")
        f.write(f"  Output       : 06_hf_license_names.json\n\n")
        
        # License distribution
        license_counts = {}
        for model in results:
            license = model['extracted_license']
            license_counts[license] = license_counts.get(license, 0) + 1
        
        f.write("LICENSE DISTRIBUTION:\n")
        for license, count in sorted(license_counts.items()):
            f.write(f"  {license}: {count}\n")
        f.write(f"\nTotal license types: {len(license_counts)}\n\n")
        
        # Detailed results
        f.write("DETAILED MODEL EXTRACTION RESULTS:\n")
        f.write("=" * 80 + "\n\n")
        
        for i, model in enumerate(results, 1):
            f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
            f.write("-" * 50 + "\n")
            f.write(f"  ID               : {model.get('id', 'Unknown')}\n")
            f.write(f"  Canonical Slug   : {model.get('canonical_slug', 'Unknown')}\n")
            f.write(f"  HuggingFace ID   : {model.get('hugging_face_id', 'Unknown')}\n")
            f.write(f"  Extracted License: {model.get('extracted_license', 'Unknown')}\n")
            
            if i < len(results):
                f.write("\n" + "=" * 80 + "\n\n")
            else:
                f.write("\n")
    
    print(f"JSON results written to: {json_output_file}")
    print(f"Report written to: {report_output_file}")
    print(f"Processed {len(results)} models")


if __name__ == "__main__":
    main()