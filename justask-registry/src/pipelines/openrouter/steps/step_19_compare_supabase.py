#!/usr/bin/env python3
"""
Pipeline vs Supabase Field Comparison
Compares field values between 18_validated_models.json and Supabase working_version table
"""

import json
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

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

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    get_ist_timestamp,
    ensure_output_dir_exists,
    set_current_pipeline,
    get_project_root,
    get_pipeline_db_connection,
)
set_current_pipeline('openrouter')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "openrouter"

# Configuration
PIPELINE_DATA_FILE = get_input_file_path("18_validated_models.json")
REPORT_FILE = get_output_file_path("19_supabase_comparison.txt")
TABLE_NAME = "working_version"
INFERENCE_PROVIDER = "OpenRouter"

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

    if get_pipeline_db_connection is None:
        print("db_utils module not available - cannot connect to Supabase")
        return None

    conn = get_pipeline_db_connection()
    if not conn:
        print("Failed to connect to Supabase using configured credentials")
    else:
        print("[DEBUG] Successfully connected to Supabase")
    return conn

def load_pipeline_data() -> List[Dict[str, Any]]:
    """Load pipeline data from 18_validated_models.json"""
    try:
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
    """Load OpenRouter data from Supabase working_version table"""
    try:
        print(f"Querying Supabase table '{TABLE_NAME}' for inference_provider='{INFERENCE_PROVIDER}'")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {TABLE_NAME} WHERE inference_provider = %s",
                (INFERENCE_PROVIDER,)
            )
            data = [dict(row) for row in cur.fetchall()]

        print(f"Loaded {len(data)} models from Supabase")

        # Debug: Check if table exists but has no OpenRouter data
        if len(data) == 0:
            print("No OpenRouter data found. Checking total table count...")
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

def detect_duplicates(data: List[Dict[str, Any]], source_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """Detect duplicate human_readable_name values in data"""
    name_groups = {}
    for model in data:
        name = model.get('human_readable_name', '')
        if name:  # Skip empty names
            if name not in name_groups:
                name_groups[name] = []
            name_groups[name].append(model)

    # Return only groups with duplicates
    duplicates = {name: models for name, models in name_groups.items() if len(models) > 1}

    if duplicates:
        print(f"⚠ WARNING: Found {len(duplicates)} duplicate name(s) in {source_name}:")
        for name, models in duplicates.items():
            print(f"  - '{name}': {len(models)} occurrences")

    return duplicates

def create_comparison_report(pipeline_data: List[Dict[str, Any]], supabase_data: List[Dict[str, Any]]):
    """Generate field comparison report"""

    # Detect duplicates BEFORE creating lookups
    pipeline_duplicates = detect_duplicates(pipeline_data, "pipeline")
    supabase_duplicates = detect_duplicates(supabase_data, "Supabase")

    # Create lookup dictionaries by human_readable_name
    # Note: This will overwrite duplicates - only last occurrence will be kept
    pipeline_lookup = {model.get('human_readable_name', ''): model for model in pipeline_data}
    supabase_lookup = {model.get('human_readable_name', ''): model for model in supabase_data}

    # Get all unique model names
    all_model_names = set(pipeline_lookup.keys()) | set(supabase_lookup.keys())
    all_model_names.discard('')  # Remove empty names

    # Fields to compare (excluding auto-managed fields)
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
        'provider_api_access'
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
        f.write("FIELD COMPARISON REPORT: PIPELINE vs SUPABASE\n")
        f.write(f"Generated: {get_ist_timestamp()}\n")
        f.write("=" * 80 + "\n\n")

        # Duplicate Detection Results
        if pipeline_duplicates or supabase_duplicates:
            f.write("⚠ DUPLICATE DETECTION ALERTS\n")
            f.write("-" * 80 + "\n\n")

            if pipeline_duplicates:
                f.write(f"PIPELINE DUPLICATES: Found {len(pipeline_duplicates)} duplicate name(s)\n")
                for name, models in sorted(pipeline_duplicates.items()):
                    f.write(f"  • '{name}': {len(models)} occurrences\n")
                    for i, model in enumerate(models, 1):
                        provider_id = model.get('provider_id', 'N/A')
                        license_name = model.get('license_name', 'N/A')
                        f.write(f"    [{i}] provider_id: {provider_id}, license: {license_name}\n")
                f.write("\n")

            if supabase_duplicates:
                f.write(f"SUPABASE DUPLICATES: Found {len(supabase_duplicates)} duplicate name(s)\n")
                for name, models in sorted(supabase_duplicates.items()):
                    f.write(f"  • '{name}': {len(models)} occurrences\n")
                    for i, model in enumerate(models, 1):
                        provider_id = model.get('provider_id', 'N/A')
                        license_name = model.get('license_name', 'N/A')
                        db_id = model.get('id', 'N/A')
                        f.write(f"    [{i}] id: {db_id}, provider_id: {provider_id}, license: {license_name}\n")
                f.write("\n")

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

        # Overall Statistics
        f.write("1. OVERALL STATISTICS:\n")
        f.write(f"   • Total unique model names: {len(all_model_names)}\n")
        f.write(f"   • Total records in pipeline: {len(pipeline_data)}\n")
        f.write(f"   • Total records in Supabase: {len(supabase_data)}\n")

        if pipeline_duplicates or supabase_duplicates:
            dup_count_pipeline = sum(len(models) - 1 for models in pipeline_duplicates.values())
            dup_count_supabase = sum(len(models) - 1 for models in supabase_duplicates.values())
            f.write(f"   • Duplicate records in pipeline: {dup_count_pipeline}\n")
            f.write(f"   • Duplicate records in Supabase: {dup_count_supabase}\n")

        f.write(f"   • Models in both systems: {len(models_in_both)}\n")
        if models_in_both:
            f.write(f"   • Models with differences: {models_with_differences_count}\n")
        f.write(f"   • Models in pipeline only (not in Supabase): {len(models_pipeline_only)}\n")
        f.write(f"   • Models in Supabase only (not in pipeline): {len(models_supabase_only)}\n\n")

        # Field-by-Field Analysis (only if there are models in both systems)
        if models_in_both:
            f.write("2. FIELD-BY-FIELD ANALYSIS (for models in both systems):\n")
            for field in fields_to_compare:
                stats = field_stats[field]
                f.write(f"   • {field}:\n")
                f.write(f"     - Exact matches: {stats['exact_matches']}\n")
                f.write(f"     - Differences: {stats['differences']}\n")
                if stats['pipeline_missing'] > 0:
                    f.write(f"     - Missing in pipeline: {stats['pipeline_missing']}\n")
                if stats['supabase_missing'] > 0:
                    f.write(f"     - Missing in Supabase: {stats['supabase_missing']}\n")

                # Show detailed differences for each field
                if stats['difference_details']:
                    f.write(f"     - Specific differences:\n")
                    for diff in stats['difference_details']:  # Show all differences
                        model_name = diff['model'][:30] + "..." if len(diff['model']) > 30 else diff['model']
                        pipeline_val = diff['pipeline_value'][:20] + "..." if len(diff['pipeline_value']) > 20 else diff['pipeline_value']
                        supabase_val = diff['supabase_value'][:20] + "..." if len(diff['supabase_value']) > 20 else diff['supabase_value']
                        f.write(f"       * {model_name}: Pipeline='{pipeline_val}' vs Supabase='{supabase_val}'\n")
            f.write("\n")

        # Categorized Breakdown
        f.write("3. CATEGORIZED BREAKDOWN:\n")

        if models_pipeline_only:
            f.write(f"   • New models (pipeline only): {len(models_pipeline_only)}\n")
            f.write("     Models: " + ", ".join(sorted(models_pipeline_only)) + "\n")

        if models_in_both:
            # Count models with differences
            models_with_differences = []
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
                    models_with_differences.append(model_name)

            f.write(f"   • Existing models with differences: {len(models_with_differences)}\n")
            if models_with_differences:
                f.write("     Models: " + ", ".join(sorted(models_with_differences)) + "\n")

        if models_supabase_only:
            f.write(f"   • Deprecated models (Supabase only): {len(models_supabase_only)}\n")
            f.write("     Models: " + ", ".join(sorted(models_supabase_only)) + "\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("DETAILED COMPARISON BY MODEL\n")
        f.write("=" * 80 + "\n\n")

        for model_name in sorted(all_model_names):
            pipeline_model = pipeline_lookup.get(model_name, {})
            supabase_model = supabase_lookup.get(model_name, {})

            f.write(f"MODEL: {model_name}\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Field Name':<25} | {'Pipeline Value':<25} | {'Supabase Value':<25}\n")
            f.write("-" * 80 + "\n")

            for field in fields_to_compare:
                pipeline_value = str(pipeline_model.get(field, '')).strip()
                supabase_value = str(supabase_model.get(field, '')).strip()

                # Truncate long values for display
                pipeline_display = pipeline_value[:23] + ".." if len(pipeline_value) > 25 else pipeline_value
                supabase_display = supabase_value[:23] + ".." if len(supabase_value) > 25 else supabase_value

                f.write(f"{field:<25} | {pipeline_display:<25} | {supabase_display:<25}\n")

            f.write("\n" + "=" * 80 + "\n\n")

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Starting field comparison...")

    try:
        # Load pipeline data
        pipeline_data = load_pipeline_data()
        if not pipeline_data:
            print("No pipeline data loaded")
            return False

        # Connect to Supabase and load data
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to Supabase - creating report with pipeline data only")
            # Create report with pipeline data only
            create_comparison_report(pipeline_data, [])
            print(f"Comparison report (pipeline-only) saved to: {REPORT_FILE}")
            return True

        try:
            supabase_data = load_supabase_data(conn)
        finally:
            conn.close()

        # Generate comparison report
        create_comparison_report(pipeline_data, supabase_data)

        print(f"Comparison report saved to: {REPORT_FILE}")
        return True

    except Exception as e:
        print(f"Error in main execution: {e}")
        # Try to create a basic report even if there's an error
        try:
            with open(REPORT_FILE, 'w', encoding='utf-8') as f:
                f.write("FIELD COMPARISON REPORT: PIPELINE vs SUPABASE\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"ERROR: Script failed with error: {e}\n")
                f.write(f"Generated at: {get_ist_timestamp()}\n")
            print(f"Error report saved to: {REPORT_FILE}")
        except Exception as write_error:
            print(f"Failed to write error report: {write_error}")
        return False

if __name__ == "__main__":
    main()