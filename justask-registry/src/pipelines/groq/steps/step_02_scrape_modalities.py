#!/usr/bin/env python3
"""
step_02_scrape_modalities.py
=====================

Standalone modalities scraper for Groq pipeline.
Extracts input/output modalities for each model.

Author: AI Models Discovery Pipeline
Version: 1.0
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    set_current_pipeline,
    get_project_root,
    GroqWebScraper,
)
set_current_pipeline('groq')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "groq"

def main():
    """Main execution function"""
    print("=" * 80)
    print("GROQ MODALITIES SCRAPER")
    print("=" * 80)

    # Load production models from stage 1
    try:
        input_file = get_input_file_path('01_scraped_models.json')
        with open(input_file, 'r', encoding='utf-8') as f:
            stage1_data = json.load(f)
            production_models = stage1_data['production_models']
    except FileNotFoundError:
        print("❌ Error: 01_scraped_models.json not found")
        print("   Please run step_01_scrape_models.py first")
        return False
    except Exception as e:
        print(f"❌ Error loading production models: {e}")
        return False

    scraper = GroqWebScraper()

    # Scrape modalities
    modalities_data = scraper.scrape_model_modalities(production_models)

    if not modalities_data:
        print("⚠️ No modalities extracted")
        # Continue - modalities are not critical

    # Transform data to include model_id field for each model
    transformed_modalities = {}
    for model_key, modality_info in modalities_data.items():
        transformed_modalities[model_key] = {
            'model_id': model_key,
            'input_modalities': modality_info['input_modalities'],
            'output_modalities': modality_info['output_modalities']
        }

    # Save the results
    filename = get_output_file_path('02_scraped_modalities.json')

    data = {
        'metadata': {
            'extraction_timestamp': datetime.now().isoformat(),
            'source_base_url': 'https://console.groq.com/docs/model/',
            'total_models': len(transformed_modalities)
        },
        'modalities': transformed_modalities
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved modalities for {len(modalities_data)} models to: {filename}")

    # Show summary
    for model_id, modalities in modalities_data.items():
        input_mod = ', '.join(modalities['input_modalities'])
        output_mod = ', '.join(modalities['output_modalities'])
        print(f"   📋 {model_id}: {input_mod} → {output_mod}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
