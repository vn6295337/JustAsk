#!/usr/bin/env python3
"""
Meta/Llama Models License Extraction for Groq Pipeline

This script processes Groq's 01_scraped_models.json file to:
1. Identify Meta/Llama models using provider and model_id patterns
2. Extract licensing information using regex-based version detection
3. Generate JSON output with official Llama license URLs

Features:
- Regex-based Llama version extraction (e.g., "llama-3.1" → "Llama-3.1")
- Llama Guard detection (e.g., "llama-guard-4" → "Llama-4")
- Official Llama license URL construction
- Works with Groq's data structure

Source Data: 01_scraped_models.json
Output: 03_meta_licenses.json
"""

import json
import sys
import re
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


def load_groq_models() -> List[Dict[str, Any]]:
    """Load Groq production models from stage-1 data"""
    try:
        input_file = get_input_file_path('01_scraped_models.json')
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('production_models', [])
    except FileNotFoundError:
        print(f"ERROR: {input_file} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in stage-1 file: {e}")
        return []


def extract_llama_license_info(model_id: str) -> Dict[str, str]:
    """
    Extract Llama license information based on version patterns.

    Extracts Llama license information using regex-based version detection
    for standalone use in the pipeline.

    Args:
        model_id: Groq model ID (e.g., "llama-3.1-8b-instant", "meta-llama/llama-guard-4-12b")

    Returns:
        Dict with license_info_text="", license_info_url="",
        license_name="Llama-{version}", license_url=official Llama URL
    """
    model_lower = model_id.lower()

    # Llama Guard patterns
    guard_match = re.search(r'llama[_/-]?guard[_/-]?(\d+)', model_lower)
    if guard_match:
        guard_version = guard_match.group(1)
        return {
            'license_info_text': '',
            'license_info_url': '',
            'license_name': f'LLAMA-{guard_version}',
            'license_url': f'https://www.llama.com/llama{guard_version}/license/'
        }

    # Regular Llama version patterns
    version_patterns = [
        r'llama[_/-]?(\d+\.\d+)',  # Match llama-3.1, llama-3.3, meta-llama/llama-3.1, etc.
        r'llama[_/-]?(\d+)',       # Match llama-4, meta-llama/llama-4, etc.
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

    # Fallback for unrecognized Llama patterns
    return {
        'license_info_text': '',
        'license_info_url': '',
        'license_name': 'LLAMA-UNKNOWN',
        'license_url': 'https://llama.meta.com/llama-downloads/'
    }


def is_meta_model(model_id: str, provider: str) -> bool:
    """Check if model is from Meta/Llama"""
    return provider.lower() == 'meta' or 'llama' in model_id.lower()


def extract_meta_licenses(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract Meta/Llama license information from Groq models"""
    meta_models = []

    print(f"Processing {len(models)} Groq models for Meta/Llama licensing...")

    for model in models:
        model_id = model.get('model_id', '')
        provider = model.get('model_provider', '')

        # Check if this is a Meta/Llama model
        if not is_meta_model(model_id, provider):
            continue

        print(f"Processing Meta model: {model_id} ({provider})")

        # Extract license information using regex patterns
        license_info = extract_llama_license_info(model_id)

        # Create model record
        meta_model = {
            'model_id': model_id,
            'model_provider': provider,
            'license_info_text': license_info.get('license_info_text', ''),
            'license_info_url': license_info.get('license_info_url', ''),
            'license_name': license_info.get('license_name', ''),
            'license_url': license_info.get('license_url', '')
        }

        meta_models.append(meta_model)
        print(f"  License Name: {license_info.get('license_name', 'UNKNOWN')}")
        print(f"  License URL: {license_info.get('license_url', 'NONE')}")

    print(f"Found {len(meta_models)} Meta/Llama models")
    return meta_models


def save_meta_results(meta_models: List[Dict[str, Any]]) -> str:
    """Save Meta license results to JSON file"""
    output_file = get_output_file_path('03_meta_licenses.json')

    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat() + '+00:00',
            'source_file': '01_scraped_models.json',
            'processor': 'step_03_extract_meta_licenses.py',
            'total_models': len(meta_models),
            'description': 'Meta/Llama models with official license information'
        },
        'models': meta_models
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(meta_models)} Meta license models to: {output_file}")
    return str(output_file)


def main():
    """Main execution function"""
    print("=" * 80)
    print("META/LLAMA LICENSE EXTRACTION FOR GROQ MODELS")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    try:
        # Load Groq models
        models = load_groq_models()
        if not models:
            print("No models found to process")
            return False

        # Extract Meta licenses
        meta_models = extract_meta_licenses(models)

        if not meta_models:
            print("No Meta/Llama models found")
            return True

        # Save results
        output_file = save_meta_results(meta_models)

        # Summary
        print("\n" + "=" * 80)
        print("META LICENSE EXTRACTION SUMMARY")
        print("=" * 80)
        print(f"Total Groq models: {len(models)}")
        print(f"Meta/Llama models: {len(meta_models)}")
        print(f"Output file: {output_file}")

        # License breakdown
        license_counts = {}
        for model in meta_models:
            license_name = model.get('license_name', 'Unknown')
            license_counts[license_name] = license_counts.get(license_name, 0) + 1

        print("\nLicense Distribution:")
        for license_name, count in sorted(license_counts.items()):
            print(f"  {license_name}: {count} models")

        print(f"\nCompleted at: {datetime.now().isoformat()}")
        return True

    except Exception as e:
        print(f"ERROR: Meta license extraction failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
