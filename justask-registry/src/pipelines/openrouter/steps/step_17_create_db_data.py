#!/usr/bin/env python3
"""
Final Database Schema Creation
Merges provider, modality, and license data into final database schema

Input Files:
- 16_provider_enriched.json (primary data source)
- 15_standardized_modalities.json (modality data)
- 13_final_licenses.json (license data)
- api_configuration.json (API metadata)
- 10_timestamp_patterns.json (timestamp formatting)

Output: 17_normalized_models.json + CSV + human readable report
"""

import json
import sys
import csv
from datetime import datetime
from typing import Any, Dict, List

# Add project root to path for imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    get_ist_timestamp,
    ensure_output_dir_exists,
    set_current_pipeline,
    get_project_root,
)
set_current_pipeline('openrouter')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "openrouter"

def load_provider_data() -> List[Dict[str, Any]]:
    """Load provider enriched data from Stage-P"""
    input_file = get_input_file_path('16_provider_enriched.json')
    
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
        print(f"ERROR: Failed to load provider data from {input_file}: {error}")
        return []

def load_modality_data() -> Dict[str, Dict[str, Any]]:
    """Load standardized modality data from Stage-O"""
    input_file = get_input_file_path('15_standardized_modalities.json')
    
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

        # Create lookup index by canonical_slug
        modality_index = {}
        for model in models:
            canonical_slug = model.get('canonical_slug', '')
            if canonical_slug:
                modality_index[canonical_slug] = model
        
        print(f"✓ Loaded {len(modality_index)} models with modalities from: {input_file}")
        return modality_index
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load modality data from {input_file}: {error}")
        return {}

def load_license_data() -> Dict[str, Dict[str, Any]]:
    """Load license data from Stage-M"""
    input_file = get_input_file_path('13_final_licenses.json')
    
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

        # Create lookup index by canonical_slug
        license_index = {}
        for model in models:
            canonical_slug = model.get('canonical_slug', '')
            if canonical_slug:
                license_index[canonical_slug] = model
        
        print(f"✓ Loaded {len(license_index)} models with licenses from: {input_file}")
        return license_index
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load license data from {input_file}: {error}")
        return {}

def load_api_configuration() -> Dict[str, Any]:
    """Load API configuration"""
    config_file = CONFIG_DIR / "api_configuration.json"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded API configuration from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load API configuration from {config_file}: {error}")
        return {}

def load_database_schema() -> Dict[str, Any]:
    """Load database schema definition"""
    schema_file = CONFIG_DIR / "database_schema.json"
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        print(f"✓ Loaded database schema from: {schema_file}")
        return schema
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load database schema from {schema_file}: {error}")
        return {}

def load_field_mapping() -> Dict[str, Any]:
    """Load field mapping configuration"""
    mapping_file = CONFIG_DIR / "field_mapping.json"

    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        print(f"✓ Loaded field mapping from: {mapping_file}")
        return mapping
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load field mapping from {mapping_file}: {error}")
        return {}

def generate_iso_timestamp() -> str:
    """Generate ISO timestamp in the format specified by 10_timestamp_patterns.json"""
    return datetime.now().isoformat() + '+00:00'

def create_database_record(provider_model: Dict[str, Any],
                          modality_data: Dict[str, Any],
                          license_data: Dict[str, Any],
                          api_config: Dict[str, Any],
                          field_mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Create a single database record from merged data sources"""
    
    # Get timestamp
    current_timestamp = generate_iso_timestamp()
    
    # Create database record according to schema
    db_record = {
        # Database managed field
        'id': '',  # Database will auto-generate

        # Provider information (from Step 16)
        'inference_provider': provider_model.get('inference_provider', ''),
        'model_provider': provider_model.get('model_provider', ''),
        'human_readable_name': provider_model.get('clean_model_name', ''),
        'provider_slug': provider_model.get('provider_slug', ''),
        'model_provider_country': provider_model.get('model_provider_country', ''),
        'official_url': provider_model.get('official_url', ''),
        
        # Modality information (from Step 15)
        'input_modalities': modality_data.get('standardized_input_modalities', ''),
        'output_modalities': modality_data.get('standardized_output_modalities', ''),
        
        # License information (from Step 13)
        'license_info_text': license_data.get('license_info_text', ''),
        'license_info_url': license_data.get('license_info_url', ''),
        'license_name': license_data.get('license_name', ''),
        'license_url': license_data.get('license_url', ''),
        
        # API configuration (from api_configuration.json)
        'rate_limits': api_config.get('rate_limits', {}).get('openrouter_default', ''),
        'provider_api_access': api_config.get('api_access_urls', {}).get('openrouter', ''),
        
        # Timestamps
        'created_at': current_timestamp,
        'updated_at': current_timestamp
    }
    
    return db_record

def create_final_database_data(provider_models: List[Dict[str, Any]], 
                               modality_index: Dict[str, Dict[str, Any]],
                               license_index: Dict[str, Dict[str, Any]],
                               api_config: Dict[str, Any],
                               field_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create final database data by merging all data sources using field mapping"""
    
    database_records = []
    
    print(f"Creating database records for {len(provider_models)} models...")
    
    # Statistics tracking
    modality_matched = 0
    license_matched = 0
    modality_missing = []
    license_missing = []
    
    for provider_model in provider_models:
        canonical_slug = provider_model.get('canonical_slug', '')

        # Get modality data
        modality_data = modality_index.get(canonical_slug, {})
        if modality_data:
            modality_matched += 1
        else:
            modality_missing.append(canonical_slug)

        # Get license data
        license_data = license_index.get(canonical_slug, {})
        if license_data:
            license_matched += 1
        else:
            license_missing.append(canonical_slug)
        
        # Create database record using field mapping
        db_record = create_database_record(provider_model, modality_data, license_data, api_config, field_mapping)
        database_records.append(db_record)
    
    print(f"✓ Database record creation complete")
    print(f"  Total records: {len(database_records)}")
    print(f"  Modality matches: {modality_matched}/{len(provider_models)}")
    print(f"  License matches: {license_matched}/{len(provider_models)}")
    
    if modality_missing:
        print(f"  Modality misses: {len(modality_missing)} models")
        print(f"  Sample missing: {modality_missing[:5]}")
    
    if license_missing:
        print(f"  License misses: {len(license_missing)} models")
        print(f"  Sample missing: {license_missing[:5]}")
    
    return database_records

def save_database_json(database_records: List[Dict[str, Any]]) -> str:
    """Save database records to JSON file"""
    output_file = get_output_file_path('17_normalized_models.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(database_records),
                "pipeline_stage": "Q_create_db_data"
            },
            "models": database_records
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved database records to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def save_database_csv(database_records: List[Dict[str, Any]], db_schema: Dict[str, Any]) -> str:
    """Save database records to CSV file using schema field order"""
    output_file = '17_normalized_models.csv'
    
    try:
        schema_fields = db_schema.get('schema_fields', [])
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=schema_fields)
            writer.writeheader()
            
            for record in database_records:
                # Ensure all schema fields are present in the correct order
                ordered_record = {}
                for field in schema_fields:
                    ordered_record[field] = record.get(field, '')
                writer.writerow(ordered_record)
        
        print(f"✓ Saved database CSV to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save CSV to {output_file}: {error}")
        return ""

def save_database_txt(database_records: List[Dict[str, Any]]) -> str:
    """Save database records to human-readable TXT file with data quality analysis"""
    output_file = get_output_file_path('17_normalized_models_report.txt')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("CREATED DATABASE SCHEMA - DATA QUALITY REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Data Quality Analysis
            missing_data = {
                'model_provider': [],
                'human_readable_name': [],
                'model_provider_country': [],
                'official_url': [],
                'input_modalities': [],
                'output_modalities': [],
                'license_info_text': [],
                'license_info_url': [],
                'license_name': [],
                'license_url': [],
                'rate_limits': [],
                'provider_api_access': []
            }
            
            unknown_values = {
                'model_provider': [],
                'license_name': []
            }
            
            # Analyze data quality
            for record in database_records:
                model_name = record.get('human_readable_name', 'Unknown')
                
                # Check for missing/empty values
                for field in missing_data.keys():
                    value = record.get(field, '').strip()
                    if not value:
                        missing_data[field].append(model_name)
                
                # Check for "Unknown" values
                if record.get('model_provider', '').strip().lower() in ['unknown', 'not found']:
                    unknown_values['model_provider'].append(model_name)
                
                if record.get('license_name', '').strip().lower() in ['unknown', 'not found']:
                    unknown_values['license_name'].append(model_name)
            
            # DATA QUALITY ISSUES SECTION
            f.write("DATA QUALITY ISSUES:\n")
            f.write("=" * 50 + "\n\n")
            
            # Missing/Empty Values Report
            f.write("MISSING OR EMPTY VALUES:\n")
            f.write("-" * 30 + "\n")
            has_missing = False
            for field, models in missing_data.items():
                if models:
                    has_missing = True
                    f.write(f"\n{field.upper().replace('_', ' ')} ({len(models)} models):\n")
                    for model in sorted(models):
                        f.write(f"  - {model}\n")
            
            if not has_missing:
                f.write("✓ No missing or empty values found\n")
            f.write("\n")
            
            # Unknown Values Report
            f.write("UNKNOWN OR 'NOT FOUND' VALUES:\n")
            f.write("-" * 30 + "\n")
            has_unknown = False
            for field, models in unknown_values.items():
                if models:
                    has_unknown = True
                    f.write(f"\n{field.upper().replace('_', ' ')} ({len(models)} models):\n")
                    for model in sorted(models):
                        f.write(f"  - {model}\n")
            
            if not has_unknown:
                f.write("✓ No unknown values found\n")
            f.write("\n")
            
            # Summary Statistics
            total_models = len(database_records)
            f.write("DATA QUALITY SUMMARY:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total models: {total_models}\n")
            
            for field, models in missing_data.items():
                if models:
                    percentage = (len(models) / total_models) * 100
                    f.write(f"Missing {field.replace('_', ' ')}: {len(models)} ({percentage:.1f}%)\n")
            
            for field, models in unknown_values.items():
                if models:
                    percentage = (len(models) / total_models) * 100
                    f.write(f"Unknown {field.replace('_', ' ')}: {len(models)} ({percentage:.1f}%)\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
            
            # COMPLETE MODEL RECORDS SECTION
            f.write("COMPLETE MODEL RECORDS:\n")
            f.write("=" * 50 + "\n\n")
            
            # Sort models by provider, then name for organized output
            sorted_models = sorted(
                database_records,
                key=lambda x: (x.get('model_provider', ''),
                              x.get('human_readable_name', ''))
            )
            
            for i, record in enumerate(sorted_models, 1):
                f.write(f"{i:3d}. {record.get('human_readable_name', 'Unknown')}\n")
                f.write(f"     Provider           : {record.get('model_provider', '')} ({record.get('model_provider_country', '')})\n")
                f.write(f"     Modalities         : {record.get('input_modalities', '')} → {record.get('output_modalities', '')}\n")
                f.write(f"     License            : {record.get('license_name', '')}\n")
                f.write(f"     License Info       : {record.get('license_info_text', '')}\n")
                f.write(f"     License URL        : {record.get('license_url', '')}\n")
                f.write(f"     Official URL       : {record.get('official_url', '')}\n")
                f.write(f"     Rate Limits        : {record.get('rate_limits', '')}\n")
                f.write(f"     Provider API Access: {record.get('provider_api_access', '')}\n")
                
                if i < len(sorted_models):
                    f.write("\n")
        
        print(f"✓ Saved data quality report to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save TXT to {output_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Final Database Schema Creation")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load all data sources
    provider_models = load_provider_data()
    if not provider_models:
        print("No provider data loaded")
        return False
    
    modality_index = load_modality_data()
    license_index = load_license_data()
    api_config = load_api_configuration()
    db_schema = load_database_schema()
    field_mapping = load_field_mapping()
    
    if not db_schema:
        print("No database schema loaded")
        return False
    
    if not field_mapping:
        print("No field mapping loaded")
        return False
    
    # Create database records using field mapping
    database_records = create_final_database_data(
        provider_models, modality_index, license_index, api_config, field_mapping
    )
    
    if not database_records:
        print("No database records created")
        return False
    
    # Save outputs
    json_success = save_database_json(database_records)
    txt_success = save_database_txt(database_records)
    # Database schema report generation removed

    if json_success and txt_success:
        print("="*60)
        print("FINAL DATABASE SCHEMA CREATION COMPLETE")
        print(f"Total records created: {len(database_records)}")
        print(f"JSON output: {json_success}")
        print(f"TXT output: {txt_success}")
        # Database schema report generation removed
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("FINAL DATABASE SCHEMA CREATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)