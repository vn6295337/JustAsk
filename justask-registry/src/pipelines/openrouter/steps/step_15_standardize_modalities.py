#!/usr/bin/env python3
"""
Raw Modality Standardization with Google Enhancement
Takes raw modalities and standardizes them using configuration mappings
Enhanced with accurate Google model modalities from Google pipeline

Sources: 
- 14_raw_modalities.json (raw modality data)
- modality_standardization.json (standardization mappings)
- google_models_modalities.json (Google modality data from Google pipeline)

Note: google_models_modalities.json is stage-4-enriched-modalities.json from Google pipeline.
Run the Google pipeline step_04 for latest Google model modalities.

Strategy:
- Gemma 2 and older: Use OpenRouter data
- Gemma 3/3n, Gemini: Use Google data first, OpenRouter fallback
- Fallback: "No match in Google data - run Google pipeline step_04"

Output: 15_standardized_modalities.json + human readable report
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

def load_raw_modalities() -> List[Dict[str, Any]]:
    """Load raw modalities from Stage-N"""
    input_file = get_input_file_path('14_raw_modalities.json')
    
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
        print(f"✓ Loaded {len(models)} models with raw modalities from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load raw modalities from {input_file}: {error}")
        return []

def load_modality_config() -> Dict[str, Any]:
    """Load modality standardization configuration"""
    config_file = CONFIG_DIR / "modality_standardization.json"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded modality standardization config from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load modality config from {config_file}: {error}")
        return {}

def load_google_modalities() -> Dict[str, Dict[str, Any]]:
    """Load Google model modalities from Google pipeline data"""
    google_file = CONFIG_DIR / "google_models_modalities.json"
    
    try:
        with open(google_file, 'r', encoding='utf-8') as f:
            google_data = json.load(f)
        
        # Extract models array from nested structure
        google_models = google_data.get('google_models_modalities', [])
        
        # Create lookup index by model name
        google_index = {}
        for model in google_models:
            name = model.get('name', '')
            if name:
                google_index[name] = model
        
        print(f"✓ Loaded {len(google_index)} Google model modalities from: {google_file}")
        return google_index
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load Google modalities from {google_file}: {error}")
        print("         Using OpenRouter data only - run Google pipeline step_04 for Google data")
        return {}

def map_openrouter_to_google_name(canonical_slug: str) -> str:
    """Map OpenRouter canonical slug to Google model name"""
    if canonical_slug.startswith('google/'):
        return f"models/{canonical_slug[7:]}"  # google/gemma-3-4b-it → models/gemma-3-4b-it
    return None

def standardize_modalities(modalities_str: str, config: Dict[str, Any]) -> str:
    """Standardize modalities string using configuration mappings"""
    if not modalities_str or modalities_str.strip() == '':
        return ''

    mappings = config.get('modality_mappings', {})
    ordering = config.get('ordering_priority', {})

    # Split by comma and normalize each modality
    modalities = [m.strip().lower() for m in str(modalities_str).split(',')]
    standardized = []

    for modality in modalities:
        if modality in mappings:
            standardized.append(mappings[modality])
        elif modality:  # Non-empty, keep as-is but capitalize
            standardized.append(modality.capitalize())

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for item in standardized:
        if item not in seen:
            seen.add(item)
            result.append(item)

    # Sort by ordering priority
    result.sort(key=lambda x: ordering.get(x, 5))

    return ', '.join(result) if result else ''

def get_enhanced_google_modalities(canonical_slug: str, raw_input: str, raw_output: str, google_index: Dict[str, Dict[str, Any]]) -> tuple[str, str, str]:
    """Get enhanced modalities for Google models with fallback"""
    google_name = map_openrouter_to_google_name(canonical_slug)
    enhancement_status = "no_google_model"
    
    if google_name and google_name in google_index:
        google_data = google_index[google_name]
        enhanced_input = google_data.get('input_modalities', raw_input)
        enhanced_output = google_data.get('output_modalities', raw_output)
        enhancement_status = "google_enhanced"
        return enhanced_input, enhanced_output, enhancement_status
    elif google_name:
        enhancement_status = "no_match_in_google_data"
        
    return raw_input, raw_output, enhancement_status

def process_standardized_modalities(models: List[Dict[str, Any]], config: Dict[str, Any], google_index: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process raw modalities to create standardized versions with Google enhancement"""
    processed_models = []
    
    print(f"Processing {len(models)} models to standardize modalities...")
    
    google_enhanced = 0
    no_match_warnings = 0
    
    for model in models:
        canonical_slug = model.get('canonical_slug', '')
        raw_input = model.get('raw_input_modalities', '')
        raw_output = model.get('raw_output_modalities', '')
        
        # Get enhanced modalities for Google models
        enhanced_input, enhanced_output, enhancement_status = get_enhanced_google_modalities(
            canonical_slug, raw_input, raw_output, google_index
        )
        
        # Track statistics
        if enhancement_status == "google_enhanced":
            google_enhanced += 1
        elif enhancement_status == "no_match_in_google_data":
            no_match_warnings += 1
        
        # Standardize modalities
        standardized_input = standardize_modalities(enhanced_input, config)
        standardized_output = standardize_modalities(enhanced_output, config)
        
        # Create model record with standardized modalities
        standardized_model = {
            'id': model.get('id', ''),
            'canonical_slug': canonical_slug,
            'original_name': model.get('original_name', ''),
            'hugging_face_id': model.get('hugging_face_id', ''),
            'clean_model_name': model.get('clean_model_name', ''),
            'raw_input_modalities': raw_input,
            'raw_output_modalities': raw_output,
            'enhanced_input_modalities': enhanced_input,
            'enhanced_output_modalities': enhanced_output,
            'standardized_input_modalities': standardized_input,
            'standardized_output_modalities': standardized_output,
            'google_enhancement_status': enhancement_status
        }
        
        processed_models.append(standardized_model)
    
    print(f"✓ Standardized modalities for {len(processed_models)} models")
    print(f"  Google enhanced: {google_enhanced} models")
    if no_match_warnings > 0:
        print(f"  No match in Google data: {no_match_warnings} models - run Google pipeline step_04")
    
    return processed_models

def save_standardized_modalities_json(processed_models: List[Dict[str, Any]]) -> str:
    """Save standardized modalities to JSON file using standardized flat array structure"""
    output_file = get_output_file_path('15_standardized_modalities.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(processed_models),
                "pipeline_stage": "O_standardize_raw_modalities"
            },
            "models": processed_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved standardized modalities to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_standardized_modalities_report(processed_models: List[Dict[str, Any]]) -> str:
    """Generate human readable report"""
    report_file = get_output_file_path('15_standardized_modalities_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("STANDARDIZED MODALITIES REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(processed_models)}\n")
            f.write(f"  Input        : 14_raw_modalities.json\n")
            f.write(f"  Config       : modality_standardization.json\n")
            f.write(f"  Processor    : step_15_standardize_modalities.py\n")
            f.write(f"  Output       : 15_standardized_modalities.json\n\n")
            
            # Standardized modality combinations analysis
            input_combinations = {}
            output_combinations = {}
            combo_pairs = {}
            
            for model in processed_models:
                input_mod = model.get('standardized_input_modalities', '')
                output_mod = model.get('standardized_output_modalities', '')
                
                # Count input modality types
                input_combinations[input_mod] = input_combinations.get(input_mod, 0) + 1
                
                # Count output modality types
                output_combinations[output_mod] = output_combinations.get(output_mod, 0) + 1
                
                # Count input/output pairs
                pair = f"{input_mod} → {output_mod}"
                combo_pairs[pair] = combo_pairs.get(pair, 0) + 1
            
            # Input modalities distribution
            f.write(f"STANDARDIZED INPUT MODALITIES DISTRIBUTION:\n")
            sorted_inputs = sorted(input_combinations.items(), key=lambda x: (-x[1], x[0]))
            for modality, count in sorted_inputs:
                display_mod = modality if modality else "(empty)"
                f.write(f"  {count:2d} models: {display_mod}\n")
            f.write(f"\nTotal unique input types: {len(input_combinations)}\n\n")
            
            # Output modalities distribution
            f.write(f"STANDARDIZED OUTPUT MODALITIES DISTRIBUTION:\n")
            sorted_outputs = sorted(output_combinations.items(), key=lambda x: (-x[1], x[0]))
            for modality, count in sorted_outputs:
                display_mod = modality if modality else "(empty)"
                f.write(f"  {count:2d} models: {display_mod}\n")
            f.write(f"\nTotal unique output types: {len(output_combinations)}\n\n")
            
            # Input/Output combinations
            f.write(f"STANDARDIZED MODALITY COMBINATIONS (INPUT → OUTPUT):\n")
            sorted_pairs = sorted(combo_pairs.items(), key=lambda x: (-x[1], x[0]))
            for pair, count in sorted_pairs:
                f.write(f"  {count:2d} models: {pair}\n")
            f.write(f"\nTotal unique combinations: {len(combo_pairs)}\n\n")
            
            # Before/After comparison section
            f.write(f"STANDARDIZATION IMPACT ANALYSIS:\n")
            # Count models where standardization changed the modalities
            input_changes = 0
            output_changes = 0
            
            for model in processed_models:
                raw_input = model.get('raw_input_modalities', '')
                raw_output = model.get('raw_output_modalities', '')
                std_input = model.get('standardized_input_modalities', '')
                std_output = model.get('standardized_output_modalities', '')
                
                if raw_input != std_input:
                    input_changes += 1
                if raw_output != std_output:
                    output_changes += 1
            
            f.write(f"  Input modalities changed: {input_changes} models\n")
            f.write(f"  Output modalities changed: {output_changes} models\n")
            f.write(f"  Input modalities unchanged: {len(processed_models) - input_changes} models\n")
            f.write(f"  Output modalities unchanged: {len(processed_models) - output_changes} models\n\n")
            
            # Detailed model listings
            f.write("DETAILED STANDARDIZED MODALITY MODEL INFORMATION:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by standardized input modality, then output modality, then name
            sorted_models = sorted(
                processed_models,
                key=lambda x: (x.get('standardized_input_modalities', ''),
                              x.get('standardized_output_modalities', ''), 
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
                f.write(f"  Standardized Input Modalities: {model.get('standardized_input_modalities', '')}\n")
                f.write(f"  Standardized Output Modalities: {model.get('standardized_output_modalities', '')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Standardized modalities report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Raw Modality Standardization")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load raw modalities from Stage-N
    models = load_raw_modalities()
    if not models:
        print("No raw modalities loaded")
        return False
    
    # Load modality standardization configuration
    config = load_modality_config()
    if not config:
        print("No modality configuration loaded")
        return False
    
    # Load Google modality enhancements
    google_index = load_google_modalities()
    
    # Process standardized modalities with Google enhancement
    processed_models = process_standardized_modalities(models, config, google_index)
    
    if not processed_models:
        print("No models processed")
        return False
    
    # Save JSON output
    json_success = save_standardized_modalities_json(processed_models)
    
    # Generate report
    report_success = generate_standardized_modalities_report(processed_models)
    
    if json_success and report_success:
        print("="*60)
        print("RAW MODALITY STANDARDIZATION COMPLETE")
        print(f"Total models processed: {len(processed_models)}")
        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("RAW MODALITY STANDARDIZATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)