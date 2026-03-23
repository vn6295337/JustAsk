#!/usr/bin/env python3
"""
Groq Pipeline vs Supabase Field Comparison
Compares field values between stage-5-data-normalization.json and Supabase working_version table
"""

import csv
import os
import json
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    get_ist_timestamp,
    set_current_pipeline,
    get_project_root,
    get_pipeline_db_connection,
)
set_current_pipeline('groq')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "groq"

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    print("Warning: psycopg2 package not found. Running in pipeline-only mode.")
    PSYCOPG2_AVAILABLE = False

try:
    from dotenv import load_dotenv
    # Check for .env in multiple possible locations
    env_paths = [
        Path(__file__).parent.parent.parent / ".env.local",
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

# Configuration
PIPELINE_DATA_FILE = get_input_file_path('06_normalized_models.json')
REPORT_FILE = get_output_file_path('07_supabase_comparison.txt')
TABLE_NAME = "working_version"
INFERENCE_PROVIDER = "Groq"

def get_db_connection():
    """Initialize PostgreSQL connection using pipeline_writer role"""
    # Diagnostic: Check if environment variable is set
    pipeline_url = os.getenv("PIPELINE_SUPABASE_URL")
    print(f"[DEBUG] PIPELINE_SUPABASE_URL environment variable: {'SET' if pipeline_url else 'NOT SET'}")
    if pipeline_url:
        print(f"[DEBUG] URL length: {len(pipeline_url)} characters")
        print(f"[DEBUG] URL starts with: {pipeline_url[:20]}...")

    if not PSYCOPG2_AVAILABLE:
        print("psycopg2 not available - running in pipeline-only mode")
        return None

    conn = get_pipeline_db_connection()
    if not conn:
        print("Failed to connect to Supabase using configured credentials")
    else:
        print("[DEBUG] Successfully connected to Supabase")
    return conn

def load_pipeline_data() -> List[Dict[str, Any]]:
    """Load pipeline data from stage-5-data-normalization.json"""
    try:
        if not os.path.exists(PIPELINE_DATA_FILE):
            print(f"❌ ERROR: {PIPELINE_DATA_FILE} not found")
            print("Please run the Groq pipeline first to generate the normalized data")
            return []

        with open(PIPELINE_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(data, list):
            models = data
        elif isinstance(data, dict) and 'models' in data:
            models = data['models']
        else:
            raise ValueError("Unexpected data format in input file")

        print(f"Loaded {len(models)} models from pipeline data")
        return models
    except Exception as e:
        print(f"Failed to load pipeline data: {e}")
        return []

def load_supabase_data(conn) -> List[Dict[str, Any]]:
    """Load Groq data from Supabase working_version table"""
    try:
        print(f"Querying Supabase table '{TABLE_NAME}' for inference_provider='{INFERENCE_PROVIDER}'")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {TABLE_NAME} WHERE inference_provider = %s",
                (INFERENCE_PROVIDER,)
            )
            data = [dict(row) for row in cur.fetchall()]

        print(f"Loaded {len(data)} models from Supabase")

        # Debug: Check if table exists but has no Groq data
        if len(data) == 0:
            print("No Groq data found. Checking total table count...")
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 5")
                total_data = [dict(row) for row in cur.fetchall()]
            print(f"Total rows in table (first 5): {len(total_data)}")
            if total_data:
                print(f"Sample inference_provider values: {[row.get('inference_provider', 'None') for row in total_data]}")

        return data
    except Exception as e:
        print(f"Failed to load Supabase data: {e}")
        return []

def create_comparison_report(pipeline_data: List[Dict[str, Any]], supabase_data: List[Dict[str, Any]]):
    """Generate field comparison report"""

    # Create lookup dictionaries by human_readable_name
    pipeline_lookup = {model.get('human_readable_name', ''): model for model in pipeline_data}
    supabase_lookup = {model.get('human_readable_name', ''): model for model in supabase_data}

    # Get all unique model names
    all_model_names = set(pipeline_lookup.keys()) | set(supabase_lookup.keys())
    all_model_names.discard('')  # Remove empty names

    # Fields to compare (based on Groq pipeline schema)
    fields_to_compare = [
        'inference_provider',
        'model_provider',
        'human_readable_name',
        'model_provider_country',
        'official_url',
        'input_modalities',
        'output_modalities',
        'license_info_text',
        'license_info_url',
        'license_name',
        'license_url',
        'rate_limits',
        'provider_api_access',
        'context_window',
        'max_completion_tokens'
    ]

    # Calculate statistics
    models_in_both = []
    models_pipeline_only = []
    models_supabase_only = []
    field_stats = {field: {'exact_matches': 0, 'differences': 0, 'pipeline_missing': 0, 'supabase_missing': 0, 'difference_details': []} for field in fields_to_compare}

    for model_name in all_model_names:
        pipeline_model = pipeline_lookup.get(model_name, {})
        supabase_model = supabase_lookup.get(model_name, {})

        if pipeline_model and supabase_model:
            models_in_both.append(model_name)
            # Compare fields for models in both systems
            for field in fields_to_compare:
                pipeline_value = str(pipeline_model.get(field, '')).strip()
                # Handle Supabase NULL values properly - convert None to empty string
                supabase_raw = supabase_model.get(field, '')
                supabase_value = '' if supabase_raw is None else str(supabase_raw).strip()

                if pipeline_value == supabase_value:
                    field_stats[field]['exact_matches'] += 1
                else:
                    field_stats[field]['differences'] += 1
                    # Store detailed difference information
                    diff_detail = {
                        'model': model_name,
                        'pipeline_value': pipeline_value,
                        'supabase_value': supabase_value
                    }
                    field_stats[field]['difference_details'].append(diff_detail)

                    if not pipeline_value:
                        field_stats[field]['pipeline_missing'] += 1
                    if not supabase_value:
                        field_stats[field]['supabase_missing'] += 1
        elif pipeline_model:
            models_pipeline_only.append(model_name)
        elif supabase_model:
            models_supabase_only.append(model_name)

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("GROQ FIELD COMPARISON REPORT: PIPELINE vs SUPABASE\n")
        f.write(f"Generated: {get_ist_timestamp()}\n")
        f.write("=" * 80 + "\n\n")

        # Summary Statistics
        f.write("SUMMARY STATISTICS\n")
        f.write("-" * 80 + "\n\n")

        # Calculate models with differences for overall statistics
        models_with_differences_count = 0
        if models_in_both:
            for model_name in models_in_both:
                pipeline_model = pipeline_lookup[model_name]
                supabase_model = supabase_lookup[model_name]
                has_differences = False
                for field in fields_to_compare:
                    pipeline_value = str(pipeline_model.get(field, '')).strip()
                    # Handle Supabase NULL values properly
                    supabase_raw = supabase_model.get(field, '')
                    supabase_value = '' if supabase_raw is None else str(supabase_raw).strip()
                    if pipeline_value != supabase_value:
                        has_differences = True
                        break
                if has_differences:
                    models_with_differences_count += 1

        # Overall statistics
        f.write(f"Pipeline Models: {len(pipeline_data)}\n")
        f.write(f"Supabase Models: {len(supabase_data)}\n")
        f.write(f"Models in Both Systems: {len(models_in_both)}\n")
        f.write(f"Models with Field Differences: {models_with_differences_count}\n")
        f.write(f"Models Only in Pipeline: {len(models_pipeline_only)}\n")
        f.write(f"Models Only in Supabase: {len(models_supabase_only)}\n\n")

        # Field-by-field statistics
        f.write("FIELD-BY-FIELD COMPARISON\n")
        f.write("-" * 80 + "\n\n")

        for field in fields_to_compare:
            stats = field_stats[field]
            total_comparisons = stats['exact_matches'] + stats['differences']

            if total_comparisons > 0:
                match_percentage = (stats['exact_matches'] / total_comparisons) * 100
                f.write(f"Field: {field}\n")
                f.write(f"  Exact Matches: {stats['exact_matches']} ({match_percentage:.1f}%)\n")
                f.write(f"  Differences: {stats['differences']}\n")
                f.write(f"  Pipeline Missing: {stats['pipeline_missing']}\n")
                f.write(f"  Supabase Missing: {stats['supabase_missing']}\n")
                f.write("\n")

        # Detailed differences for models in both systems
        if models_in_both and any(field_stats[field]['differences'] > 0 for field in fields_to_compare):
            f.write("DETAILED FIELD DIFFERENCES\n")
            f.write("-" * 80 + "\n\n")

            # Show up to 5 examples for each field with differences
            for field in fields_to_compare:
                if field_stats[field]['difference_details']:
                    f.write(f"Field: {field}\n")
                    f.write("-" * 40 + "\n")

                    # Show first 5 differences
                    for i, diff in enumerate(field_stats[field]['difference_details'][:5]):
                        f.write(f"Model: {diff['model']}\n")
                        f.write(f"  Pipeline Value: '{diff['pipeline_value']}'\n")
                        f.write(f"  Supabase Value: '{diff['supabase_value']}'\n")
                        f.write("\n")

                    if len(field_stats[field]['difference_details']) > 5:
                        f.write(f"... and {len(field_stats[field]['difference_details']) - 5} more differences\n")
                    f.write("\n")

        # Models only in pipeline
        if models_pipeline_only:
            f.write("MODELS ONLY IN PIPELINE\n")
            f.write("-" * 80 + "\n\n")
            f.write(f"Count: {len(models_pipeline_only)}\n")
            f.write("     Models: " + ", ".join(sorted(models_pipeline_only)[:10]))
            if len(models_pipeline_only) > 10:
                f.write(f" ... and {len(models_pipeline_only) - 10} more")
            f.write("\n\n")

        # Models only in Supabase
        if models_supabase_only:
            f.write("MODELS ONLY IN SUPABASE\n")
            f.write("-" * 80 + "\n\n")
            f.write(f"Count: {len(models_supabase_only)}\n")
            f.write("     Models: " + ", ".join(sorted(models_supabase_only)[:10]))
            if len(models_supabase_only) > 10:
                f.write(f" ... and {len(models_supabase_only) - 10} more")
            f.write("\n\n")

        # Detailed comparison for ALL models
        f.write("=" * 80 + "\n")
        f.write("DETAILED COMPARISON BY MODEL\n")
        f.write("=" * 80 + "\n\n")

        # Show ALL models (both pipeline-only and those in both systems)
        all_models_to_display = sorted(set(list(pipeline_lookup.keys()) + list(supabase_lookup.keys())))
        all_models_to_display = [m for m in all_models_to_display if m]  # Remove empty names

        for model_name in all_models_to_display:
            pipeline_model = pipeline_lookup.get(model_name, {})
            supabase_model = supabase_lookup.get(model_name, {})

            f.write(f"MODEL: {model_name}\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Field Name':<25} | {'Pipeline Value':<25} | {'Supabase Value':<25}\n")
            f.write("-" * 80 + "\n")

            for field in fields_to_compare:
                pipeline_value = str(pipeline_model.get(field, '')).strip()
                supabase_raw = supabase_model.get(field, '')
                supabase_value = '' if supabase_raw is None else str(supabase_raw).strip()

                # Truncate long values for display
                pipeline_display = pipeline_value[:23] + ".." if len(pipeline_value) > 25 else pipeline_value
                supabase_display = supabase_value[:23] + ".." if len(supabase_value) > 25 else supabase_value

                f.write(f"{field:<25} | {pipeline_display:<25} | {supabase_display:<25}\n")

            f.write("\n" + "=" * 80 + "\n\n")

    print(f"✅ Comparison report saved to: {REPORT_FILE}")

def main():
    """Main execution function"""
    print("=" * 80)
    print("🔍 GROQ PIPELINE vs SUPABASE COMPARISON")
    print("=" * 80)
    print(f"🕒 Started at: {get_ist_timestamp()}")

    # Load pipeline data
    print("\n📊 Loading Groq pipeline data...")
    pipeline_data = load_pipeline_data()

    if not pipeline_data:
        print("❌ No pipeline data available. Exiting.")
        return

    # Initialize database connection
    print("\n🔗 Connecting to Supabase...")
    conn = get_db_connection()

    if not conn:
        print("❌ Database not available. Creating pipeline-only report...")
        supabase_data = []
    else:
        # Load Supabase data
        print("\n📊 Loading Supabase data...")
        try:
            supabase_data = load_supabase_data(conn)
        finally:
            conn.close()

    # Generate comparison report
    print("\n📋 Generating comparison report...")
    create_comparison_report(pipeline_data, supabase_data)

    print(f"\n✅ Comparison completed at: {get_ist_timestamp()}")
    print(f"📄 Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    main()
