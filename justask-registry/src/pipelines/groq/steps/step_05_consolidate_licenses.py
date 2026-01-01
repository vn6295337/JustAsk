#!/usr/bin/env python3
"""
Consolidate All License Information for Groq Pipeline

This script consolidates license information from all extraction sources:
1. step_03_extract_meta_licenses.py output (03_meta_licenses.json)
2. step_04_extract_opensource_licenses.py output (04_opensource_licenses.json)

Combines all results into the final 05_consolidated_licenses.json file
used by subsequent pipeline steps.

Input Files:
- 03_meta_licenses.json
- 04_opensource_licenses.json

Output:
- 05_consolidated_licenses.json (final consolidated results)
"""

import json
import sys
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    set_current_pipeline,
    get_project_root,
)
set_current_pipeline('groq')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "groq"


def load_meta_licenses() -> List[Dict[str, Any]]:
    """Load Meta/Llama license information"""
    try:
        input_file = get_input_file_path('03_meta_licenses.json')
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('models', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load Meta licenses: {e}")
        return []


def load_hf_scraped_licenses() -> List[Dict[str, Any]]:
    """Load HuggingFace-scraped and Google license information"""
    try:
        input_file = get_input_file_path('04_opensource_licenses.json')
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('models', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load HF-scraped licenses: {e}")
        return []


def build_provider_mappings(all_models: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Build provider license mappings structure for the Groq pipeline.

    Structure:
    {
        "provider_license_mappings": {
            "ProviderName": {
                "model_name": {
                    "license_info_text": "",
                    "license_info_url": "",
                    "license_name": "",
                    "license_url": ""
                }
            }
        }
    }
    """
    provider_mappings = {}

    for model in all_models:
        model_id = model.get('model_id', '')
        provider = model.get('model_provider', '')

        if not model_id or not provider:
            continue

        # Initialize provider if not exists
        if provider not in provider_mappings:
            provider_mappings[provider] = {}

        # Use model_id as key (remove provider prefix if exists)
        model_key = model_id.split('/')[-1] if '/' in model_id else model_id

        # Build license info
        license_info = {
            'license_info_text': model.get('license_info_text', ''),
            'license_info_url': model.get('license_info_url', ''),
            'license_name': model.get('license_name', ''),
            'license_url': model.get('license_url', '')
        }

        provider_mappings[provider][model_key] = license_info

    return provider_mappings


def collect_license_urls(all_models: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Collect all unique license names and their official URLs

    Returns:
    {
        "license_name": "official_license_url"
    }
    """
    license_urls = {}

    for model in all_models:
        license_name = model.get('license_name', '')
        license_url = model.get('license_url', '')

        # Only add if we have both name and URL, and URL is not a HuggingFace URL
        if (license_name and license_url and
            not license_url.startswith('https://huggingface.co')):
            license_urls[license_name] = license_url

    return license_urls


def generate_consolidation_statistics(meta_models: List[Dict[str, Any]],
                                    hf_scraped_models: List[Dict[str, Any]],
                                    all_models: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive statistics about the consolidation"""

    # Source statistics
    source_stats = {
        'meta_models': len(meta_models),
        'hf_scraped_models': len(hf_scraped_models),
        'total_consolidated': len(all_models)
    }

    # Provider breakdown
    provider_stats = {}
    for model in all_models:
        provider = model.get('model_provider', 'Unknown')
        provider_stats[provider] = provider_stats.get(provider, 0) + 1

    # License breakdown
    license_stats = {}
    for model in all_models:
        license_name = model.get('license_name', 'Unknown')
        license_stats[license_name] = license_stats.get(license_name, 0) + 1

    # Category breakdown (if available)
    category_stats = {}
    for model in all_models:
        category = model.get('category', 'meta' if 'llama' in model.get('model_id', '').lower() else 'unknown')
        category_stats[category] = category_stats.get(category, 0) + 1

    return {
        'sources': source_stats,
        'providers': provider_stats,
        'licenses': license_stats,
        'categories': category_stats
    }


def save_consolidated_results(provider_mappings: Dict[str, Dict[str, Dict[str, str]]],
                            license_urls: Dict[str, str],
                            statistics: Dict[str, Any],
                            all_models: List[Dict[str, Any]]) -> str:
    """Save consolidated results to 05_consolidated_licenses.json"""

    output_file = get_output_file_path('05_consolidated_licenses.json')

    # Build final structure for the Groq pipeline
    consolidated_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat() + '+00:00',
            'consolidation_processor': 'step_05_consolidate_licenses.py',
            'source_files': [
                '03_meta_licenses.json',
                '04_opensource_licenses.json'
            ],
            'total_models': len(all_models),
            'description': 'Consolidated license information from all Groq model sources',
            'statistics': statistics
        },
        'license_urls': license_urls,
        'provider_license_mappings': provider_mappings
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, indent=2, ensure_ascii=False)

    print(f"Saved consolidated license information to: {output_file}")
    return str(output_file)


def main():
    """Main consolidation function"""
    print("=" * 80)
    print("CONSOLIDATE ALL GROQ MODEL LICENSE INFORMATION")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    try:
        # Step 1: Load all license sources
        print("STEP 1: Loading license information from all sources...")
        meta_models = load_meta_licenses()
        hf_scraped_models = load_hf_scraped_licenses()

        print(f"  Meta/Llama models: {len(meta_models)}")
        print(f"  HF-scraped + Google models: {len(hf_scraped_models)}")
        print()

        # Combine all models
        all_models = meta_models + hf_scraped_models

        if not all_models:
            print("ERROR: No models found to consolidate")
            return False

        print(f"Total models to consolidate: {len(all_models)}")
        print()

        # Step 2: Build provider mappings structure
        print("STEP 2: Building provider license mappings...")
        provider_mappings = build_provider_mappings(all_models)
        print(f"  Providers processed: {len(provider_mappings)}")

        for provider, models in provider_mappings.items():
            print(f"    {provider}: {len(models)} models")
        print()

        # Step 3: Collect license URLs
        print("STEP 3: Collecting license URLs...")
        license_urls = collect_license_urls(all_models)
        print(f"  Unique license URLs collected: {len(license_urls)}")

        for license_name, license_url in sorted(license_urls.items()):
            print(f"    {license_name}: {license_url}")
        print()

        # Step 4: Generate statistics
        print("STEP 4: Generating consolidation statistics...")
        statistics = generate_consolidation_statistics(meta_models, hf_scraped_models, all_models)
        print()

        # Step 5: Save consolidated results
        print("STEP 5: Saving consolidated results...")
        output_file = save_consolidated_results(provider_mappings, license_urls, statistics, all_models)
        print()

        # Final Summary
        print("=" * 80)
        print("CONSOLIDATION SUMMARY")
        print("=" * 80)
        print(f"Input Sources:")
        print(f"  Meta/Llama models: {len(meta_models)}")
        print(f"  HF-scraped + Google models: {len(hf_scraped_models)}")
        print(f"Total Consolidated: {len(all_models)}")
        print(f"Output File: {output_file}")

        print(f"\nProvider Distribution:")
        for provider, count in sorted(statistics['providers'].items()):
            print(f"  {provider}: {count} models")

        print(f"\nLicense Distribution:")
        for license_name, count in sorted(statistics['licenses'].items()):
            official_url = "✓" if license_name in license_urls else "✗"
            print(f"  {license_name}: {count} models (Official URL: {official_url})")

        if 'categories' in statistics and statistics['categories']:
            print(f"\nCategory Distribution:")
            for category, count in sorted(statistics['categories'].items()):
                print(f"  {category.title()}: {count} models")

        print(f"\nCompleted at: {datetime.now().isoformat()}")
        print("SUCCESS: All license information consolidated successfully!")
        return True

    except Exception as e:
        print(f"ERROR: Consolidation failed: {e}")
        print("Please check that both source files exist and are valid JSON")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
