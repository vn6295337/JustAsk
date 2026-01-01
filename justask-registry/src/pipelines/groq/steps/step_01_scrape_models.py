#!/usr/bin/env python3
"""
step_01_scrape_models.py
============================

Standalone production models scraper for Groq pipeline.
Extracts models from both production-models and production-systems sections.

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
    print("GROQ PRODUCTION MODELS SCRAPER")
    print("=" * 80)

    try:
        scraper = GroqWebScraper()

        # Scrape production models
        production_models = scraper.scrape_production_models()

        if not production_models:
            print("❌ No production models extracted")
            return False
    except Exception as e:
        print(f"❌ FATAL ERROR during scraping: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Save the results
    filename = get_output_file_path('01_scraped_models.json')

    # Count models by source section
    production_models_count = sum(1 for m in production_models if m.get('source_section') == 'production-models')
    production_systems_count = sum(1 for m in production_models if m.get('source_section') == 'production-systems')

    data = {
        'metadata': {
            'extraction_timestamp': datetime.now().isoformat(),
            'source_urls': [
                'https://console.groq.com/docs/models#production-models',
                'https://console.groq.com/docs/models#production-systems'
            ],
            'total_models': len(production_models),
            'models_by_source': {
                'production-models': production_models_count,
                'production-systems': production_systems_count
            }
        },
        'production_models': production_models
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    # Create TXT report
    txt_filename = str(filename).replace('.json', '-report.txt')
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write("GROQ PRODUCTION MODELS EXTRACTION REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {data['metadata']['extraction_timestamp']}\n")
        f.write(f"Total Models: {data['metadata']['total_models']}\n\n")

        f.write("MODELS BY SOURCE:\n")
        f.write("-" * 40 + "\n")
        for source, count in data['metadata']['models_by_source'].items():
            f.write(f"{source}: {count} models\n")

    print(f"✅ Saved {len(production_models)} production models to: {filename}")
    print(f"✅ Saved production models report to: {txt_filename}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
