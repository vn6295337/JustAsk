#!/usr/bin/env python3
"""
Raw Modality Extraction
Extracts raw input/output modalities from filtered models without standardization
Source: 02_filtered_models.json (filtered models data)
Output: 14_raw_modalities.json + human readable report
"""

import json
import sys
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

def load_special_mappings() -> Dict[str, str]:
    """Load GPT OSS special mappings from config file"""
    config_path = CONFIG_DIR / "provider_enrichment.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('special_mappings', {}).get('oss_models', {})
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load special mappings from {config_path}: {error}")
        return {}

def load_filtered_models() -> List[Dict[str, Any]]:
    """Load filtered models from Stage-B"""
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
        print(f"✓ Loaded {len(models)} filtered models from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load filtered models from {input_file}: {error}")
        return []

def extract_model_name(full_name: str, canonical_slug: str = '') -> str:
    """Extract clean model name from full name with enhanced Google Gemma support and GPT OSS mappings"""
    # Check if this is a Google model - handle specially for Gemma canonical slug processing
    if ':' in full_name:
        provider_part, model_part = full_name.split(':', 1)
        provider = provider_part.strip()
        model_part = model_part.strip()

        # Special handling for Google Gemma models using canonical slug
        if provider.lower() == 'google' and canonical_slug and 'gemma' in canonical_slug.lower():
            return extract_gemma_clean_name(canonical_slug)
    else:
        model_part = full_name.strip()

    # Remove (free) suffix if present
    if model_part.endswith(' (free)'):
        model_part = model_part[:-7].strip()

    # Load special mappings for GPT OSS models
    special_mappings = load_special_mappings()

    # Check if this model has a special mapping
    if model_part.lower() in special_mappings:
        return special_mappings[model_part.lower()]

    return model_part

def extract_gemma_clean_name(canonical_slug: str) -> str:
    """Extract clean Gemma model name from canonical slug with proper capitalization"""
    # Expected format: "google/gemma-3n-e2b-it" -> "Gemma 3n E2B IT"
    if '/' not in canonical_slug:
        return canonical_slug

    # Extract model part after "google/"
    model_slug = canonical_slug.split('/', 1)[1]

    # Handle Gemma-specific transformations
    if model_slug.startswith('gemma-'):
        # Remove "gemma-" prefix
        parts = model_slug[6:]  # Skip "gemma-"

        # Split by hyphens and process each part
        components = parts.split('-')
        clean_parts = []

        for component in components:
            if component == 'it':
                clean_parts.append('IT')
            elif component in ['e2b', 'e4b']:
                clean_parts.append(component.upper())
            elif component.endswith('b') and component[:-1].isdigit():
                # Handle size components like "2b", "27b" -> "2B", "27B"
                clean_parts.append(component.upper())
            elif component == '3n':
                # Special case: preserve lowercase 'n' in "3n"
                clean_parts.append('3n')
            elif component.isdigit():
                # Version numbers remain as-is
                clean_parts.append(component)
            else:
                # Default: capitalize first letter
                clean_parts.append(component.capitalize())

        # Reconstruct with "Gemma" prefix
        if clean_parts:
            return 'Gemma ' + ' '.join(clean_parts)

    # Fallback: basic capitalization
    return canonical_slug.replace('-', ' ').title()

def process_raw_modalities(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process filtered models to extract raw modality information"""
    processed_models = []
    
    print(f"Processing {len(models)} models to extract raw modalities...")
    
    for model in models:
        # Extract clean model name with canonical slug for Google Gemma models
        original_name = model.get('name', '')
        canonical_slug = model.get('canonical_slug', '')
        clean_model_name = extract_model_name(original_name, canonical_slug)
        
        # Extract modalities from nested architecture object
        architecture = model.get('architecture', {})
        input_modalities = architecture.get('input_modalities', [])
        output_modalities = architecture.get('output_modalities', [])
        
        # Convert arrays to comma-separated strings
        raw_input = ', '.join(input_modalities) if input_modalities else ''
        raw_output = ', '.join(output_modalities) if output_modalities else ''
        
        # Create model record with raw modality data
        modality_model = {
            'id': model.get('id', ''),
            'canonical_slug': model.get('canonical_slug', ''),
            'original_name': original_name,
            'hugging_face_id': model.get('hugging_face_id', ''),
            'clean_model_name': clean_model_name,
            'raw_input_modalities': raw_input,
            'raw_output_modalities': raw_output
        }
        
        processed_models.append(modality_model)
    
    print(f"✓ Processed raw modalities for {len(processed_models)} models")
    return processed_models

def save_raw_modalities_json(processed_models: List[Dict[str, Any]]) -> str:
    """Save raw modalities to JSON file using standardized flat array structure"""
    output_file = get_output_file_path('14_raw_modalities.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(processed_models),
                "pipeline_stage": "N_extract_raw_modalities"
            },
            "models": processed_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved raw modalities to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_raw_modalities_report(processed_models: List[Dict[str, Any]]) -> str:
    """Generate human readable report"""
    report_file = get_output_file_path('14_raw_modalities_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("RAW MODALITIES EXTRACTION REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(processed_models)}\n")
            f.write(f"  Input        : 02_filtered_models.json\n")
            f.write(f"  Processor    : step_14_extract_modalities.py\n")
            f.write(f"  Output       : 14_raw_modalities.json\n\n")
            
            # Raw modality combinations analysis
            input_combinations = {}
            output_combinations = {}
            combo_pairs = {}
            
            for model in processed_models:
                input_mod = model.get('raw_input_modalities', '')
                output_mod = model.get('raw_output_modalities', '')
                
                # Count input modality types
                input_combinations[input_mod] = input_combinations.get(input_mod, 0) + 1
                
                # Count output modality types
                output_combinations[output_mod] = output_combinations.get(output_mod, 0) + 1
                
                # Count input/output pairs
                pair = f"{input_mod} → {output_mod}"
                combo_pairs[pair] = combo_pairs.get(pair, 0) + 1
            
            # Input modalities distribution
            f.write(f"RAW INPUT MODALITIES DISTRIBUTION:\n")
            sorted_inputs = sorted(input_combinations.items(), key=lambda x: (-x[1], x[0]))
            for modality, count in sorted_inputs:
                display_mod = modality if modality else "(empty)"
                f.write(f"  {count:2d} models: {display_mod}\n")
            f.write(f"\nTotal unique input types: {len(input_combinations)}\n\n")
            
            # Output modalities distribution
            f.write(f"RAW OUTPUT MODALITIES DISTRIBUTION:\n")
            sorted_outputs = sorted(output_combinations.items(), key=lambda x: (-x[1], x[0]))
            for modality, count in sorted_outputs:
                display_mod = modality if modality else "(empty)"
                f.write(f"  {count:2d} models: {display_mod}\n")
            f.write(f"\nTotal unique output types: {len(output_combinations)}\n\n")
            
            # Input/Output combinations
            f.write(f"RAW MODALITY COMBINATIONS (INPUT → OUTPUT):\n")
            sorted_pairs = sorted(combo_pairs.items(), key=lambda x: (-x[1], x[0]))
            for pair, count in sorted_pairs:
                f.write(f"  {count:2d} models: {pair}\n")
            f.write(f"\nTotal unique combinations: {len(combo_pairs)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED RAW MODALITY MODEL INFORMATION:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by input modality, then output modality, then name
            sorted_models = sorted(
                processed_models,
                key=lambda x: (x.get('raw_input_modalities', ''),
                              x.get('raw_output_modalities', ''), 
                              x.get('clean_model_name', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Standardized field ordering: identifiers → names → modalities
                f.write(f"  ID: {model.get('id', '')}\n")
                f.write(f"  Original Name: {model.get('original_name', '')}\n")
                f.write(f"  HuggingFace ID: {model.get('hugging_face_id', '')}\n")
                f.write(f"  Canonical Slug: {model.get('canonical_slug', '')}\n")
                f.write(f"  Clean Model Name: {model.get('clean_model_name', '')}\n")
                f.write(f"  Raw Input Modalities: {model.get('raw_input_modalities', '')}\n")
                f.write(f"  Raw Output Modalities: {model.get('raw_output_modalities', '')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Raw modalities report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Raw Modalities Extraction")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load filtered models from Stage-B
    models = load_filtered_models()
    if not models:
        print("No filtered models loaded")
        return False
    
    # Process raw modalities
    processed_models = process_raw_modalities(models)
    
    if not processed_models:
        print("No models processed")
        return False
    
    # Save JSON output
    json_success = save_raw_modalities_json(processed_models)
    
    # Generate report
    report_success = generate_raw_modalities_report(processed_models)
    
    if json_success and report_success:
        print("="*60)
        print("RAW MODALITIES EXTRACTION COMPLETE")
        print(f"Total models processed: {len(processed_models)}")
        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("RAW MODALITIES EXTRACTION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)