#!/usr/bin/env python3
"""
Database Data Finalizer
Removes models specified in removal configuration file from database-ready data
Input: 17_normalized_models.json (database-ready models)
Config: remove_models.json (models to remove with reasons)
Output: 18_validated_models.json + removal report
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

def load_database_data() -> List[Dict[str, Any]]:
    """Load database-ready data from Stage-Q"""
    input_file = get_input_file_path('17_normalized_models.json')
    
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
        print(f"✓ Loaded {len(models)} database-ready models from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load database data from {input_file}: {error}")
        return []

def load_provider_enriched_data() -> List[Dict[str, Any]]:
    """Load provider-enriched data from Stage-P to get canonical slug mappings"""
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
        print(f"✓ Loaded {len(models)} provider-enriched models from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load provider data from {input_file}: {error}")
        return []

def load_provider_enrichment_config() -> Dict[str, Any]:
    """Load provider enrichment configuration for model family patterns"""
    config_file = CONFIG_DIR / "provider_enrichment.json"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded provider enrichment config from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load provider enrichment config from {config_file}: {error}")
        return {}

def determine_model_family(clean_model_name: str, enrichment_config: Dict[str, Any]) -> str:
    """Determine model family based on clean model name using enrichment patterns"""
    if not clean_model_name or not enrichment_config:
        return "Unknown"
    
    family_patterns = enrichment_config.get('model_family_patterns', {})
    clean_name_lower = clean_model_name.lower()
    
    for family, patterns in family_patterns.items():
        for pattern in patterns:
            if pattern.lower() in clean_name_lower:
                return family
    
    return "Unknown"

def load_removal_config() -> Dict[str, Any]:
    """Load removal configuration"""
    config_file = CONFIG_DIR / "remove_models.json"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded removal config from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load removal config from {config_file}: {error}")
        return {}

def create_slug_to_clean_name_mapping(provider_models: List[Dict[str, Any]]) -> Dict[str, str]:
    """Create mapping from canonical_slug to clean_model_name"""
    slug_mapping = {}
    
    for model in provider_models:
        canonical_slug = model.get('canonical_slug', '')
        clean_model_name = model.get('clean_model_name', '')
        
        if canonical_slug and clean_model_name:
            slug_mapping[canonical_slug] = clean_model_name
    
    print(f"✓ Created slug-to-name mapping for {len(slug_mapping)} models")
    return slug_mapping

def create_removal_index(removal_config: Dict[str, Any], slug_mapping: Dict[str, str]) -> Dict[str, str]:
    """Create index of clean model names to remove with their reasons"""
    removal_index = {}
    
    models_to_remove = removal_config.get('models_to_remove', [])
    not_found_slugs = []
    
    for entry in models_to_remove:
        canonical_slug = entry.get('canonical_slug', '')
        reason = entry.get('reason', 'No reason specified')
        
        if canonical_slug:
            # Map canonical slug to clean model name
            clean_model_name = slug_mapping.get(canonical_slug)
            if clean_model_name:
                removal_index[clean_model_name] = reason
            else:
                not_found_slugs.append(canonical_slug)
    
    if not_found_slugs:
        print(f"WARNING: {len(not_found_slugs)} canonical slugs not found in provider data:")
        for slug in not_found_slugs[:5]:  # Show first 5
            print(f"  - {slug}")
        if len(not_found_slugs) > 5:
            print(f"  ... and {len(not_found_slugs) - 5} more")
    
    print(f"✓ Created removal index for {len(removal_index)} clean model names")
    return removal_index

def finalize_database_data(models: List[Dict[str, Any]], removal_index: Dict[str, str], provider_models: List[Dict[str, Any]], enrichment_config: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Remove specified models from database data based on human_readable_name matching clean_model_name"""
    finalized_models = []
    removed_models = []
    
    # Create lookup for provider data by clean_model_name
    provider_lookup = {}
    for pmodel in provider_models:
        clean_name = pmodel.get('clean_model_name', '')
        if clean_name:
            provider_lookup[clean_name] = pmodel
    
    print(f"Filtering {len(models)} models against {len(removal_index)} removal entries...")
    
    for model in models:
        # Q schema uses human_readable_name, which matches clean_model_name from P schema
        human_readable_name = model.get('human_readable_name', '')
        
        if human_readable_name in removal_index:
            # Model should be removed
            removal_reason = removal_index[human_readable_name]
            removed_model = model.copy()
            removed_model['removal_reason'] = removal_reason
            
            # Enrich with provider data for better reporting
            provider_data = provider_lookup.get(human_readable_name, {})
            removed_model['canonical_slug'] = provider_data.get('canonical_slug', '')
            removed_model['clean_model_name'] = provider_data.get('clean_model_name', '')
            removed_model['provider_id'] = provider_data.get('id', '')
            
            # Determine model family using enrichment patterns
            clean_model_name = provider_data.get('clean_model_name', '')
            model_family = determine_model_family(clean_model_name, enrichment_config)
            removed_model['model_family'] = model_family
            
            removed_models.append(removed_model)
        else:
            # Model should be kept
            finalized_models.append(model)
    
    print(f"✓ Filtered models: {len(finalized_models)} kept, {len(removed_models)} removed")
    return finalized_models, removed_models

def save_finalized_data(finalized_models: List[Dict[str, Any]]) -> str:
    """Save finalized database data to JSON file"""
    output_file = get_output_file_path('18_validated_models.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(finalized_models),
                "pipeline_stage": "18_filter_db_data"
            },
            "models": finalized_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved {len(finalized_models)} finalized models to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_removal_report(finalized_models: List[Dict[str, Any]], removed_models: List[Dict[str, Any]], removal_config: Dict[str, Any]) -> str:
    """Generate comprehensive removal report"""
    report_file = get_output_file_path('18_validated_models_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("DATABASE DATA FINALIZATION REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Input models         : {len(finalized_models) + len(removed_models)}\n")
            f.write(f"  Models kept          : {len(finalized_models)}\n")
            f.write(f"  Models removed       : {len(removed_models)}\n")
            f.write(f"  Input                : 17_normalized_models.json\n")
            f.write(f"  Config               : remove_models.json\n")
            f.write(f"  Processor            : step_18_filter_db_data.py\n")
            f.write(f"  Output               : 18_validated_models.json\n\n")
            
            # Removal reasons distribution
            if removed_models:
                reason_counts = {}
                for model in removed_models:
                    reason = model.get('removal_reason', 'Unknown')
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                
                f.write(f"REMOVAL REASONS DISTRIBUTION:\n")
                sorted_reasons = sorted(reason_counts.items(), key=lambda x: (-x[1], x[0]))
                for reason, count in sorted_reasons:
                    f.write(f"  {count:2d} models: {reason}\n")
                f.write(f"\nTotal removal reasons: {len(reason_counts)}\n\n")
            else:
                f.write(f"NO MODELS REMOVED\n\n")
            
            # Configuration validation
            config_models = removal_config.get('models_to_remove', [])
            config_slugs = {entry.get('canonical_slug', '') for entry in config_models}
            removed_clean_names = {model.get('clean_model_name', '') for model in removed_models}
            
            # Count how many config entries were successfully processed
            successfully_removed = len([entry for entry in config_models 
                                      if entry.get('canonical_slug', '') and 
                                      any(model.get('clean_model_name', '') for model in removed_models)])
            
            f.write(f"REMOVAL PROCESSING SUMMARY:\n")
            f.write(f"  Configured for removal: {len(config_models)} models\n")
            f.write(f"  Successfully removed: {len(removed_models)} models\n")
            if len(removed_models) == len(config_models):
                f.write(f"  ✓ ALL CONFIGURED MODELS FOUND AND REMOVED\n\n")
            else:
                f.write(f"  ⚠ {len(config_models) - len(removed_models)} models not found (check canonical slugs)\n\n")
            
            # Removed models details
            if removed_models:
                f.write("DETAILED REMOVED MODEL INFORMATION:\n")
                f.write("=" * 80 + "\n\n")
                
                # Sort removed models by removal reason then clean model name
                sorted_removed = sorted(
                    removed_models,
                    key=lambda x: (x.get('removal_reason', ''), x.get('clean_model_name', ''))
                )
                
                for i, model in enumerate(sorted_removed, 1):
                    canonical_slug = model.get('canonical_slug', 'Unknown')
                    f.write(f"REMOVED MODEL {i}: {canonical_slug}\n")
                    f.write("-" * 50 + "\n")
                    
                    # Key identification fields
                    f.write(f"  Provider ID: {model.get('provider_id', '')}\n")
                    f.write(f"  Clean Model Name: {model.get('clean_model_name', '')}\n")
                    f.write(f"  Canonical Slug: {canonical_slug}\n")
                    f.write(f"  Model Provider: {model.get('model_provider', '')}\n")
                    f.write(f"  Model Family: {model.get('model_family', '')}\n")
                    f.write(f"  Removal Reason: {model.get('removal_reason', '')}\n")
                    
                    # Add separator between models
                    if i < len(sorted_removed):
                        f.write("\n" + "=" * 80 + "\n\n")
                    else:
                        f.write("\n")
            
            # Finalized models summary
            f.write("FINALIZED DATABASE DATA SUMMARY:\n")
            f.write("=" * 80 + "\n\n")
            
            if finalized_models:
                # Provider distribution
                provider_counts = {}
                family_counts = {}
                
                for model in finalized_models:
                    provider = model.get('model_provider', 'Unknown')
                    family = model.get('model_family', 'Unknown')
                    
                    provider_counts[provider] = provider_counts.get(provider, 0) + 1
                    family_counts[family] = family_counts.get(family, 0) + 1
                
                f.write(f"PROVIDER DISTRIBUTION (FINALIZED DATA):\n")
                sorted_providers = sorted(provider_counts.items(), key=lambda x: (-x[1], x[0]))
                for provider, count in sorted_providers:
                    f.write(f"  {count:2d} models: {provider}\n")
                f.write(f"\nTotal providers: {len(provider_counts)}\n\n")
                
                f.write(f"FAMILY DISTRIBUTION (FINALIZED DATA):\n")
                sorted_families = sorted(family_counts.items(), key=lambda x: (-x[1], x[0]))
                for family, count in sorted_families[:10]:  # Show top 10 families
                    f.write(f"  {count:2d} models: {family}\n")
                if len(family_counts) > 10:
                    f.write(f"  ... and {len(family_counts) - 10} more families\n")
                f.write(f"\nTotal families: {len(family_counts)}\n")
            else:
                f.write(f"NO MODELS IN FINALIZED DATA\n")
        
        print(f"✓ Removal report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Database Data Finalizer")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load database-ready data from Stage-Q
    models = load_database_data()
    if not models:
        print("No database data loaded")
        return False
    
    # Load provider-enriched data from Stage-P for canonical slug mappings
    provider_models = load_provider_enriched_data()
    if not provider_models:
        print("No provider data loaded")
        return False
    
    # Load provider enrichment configuration for model family patterns
    enrichment_config = load_provider_enrichment_config()
    
    # Load removal configuration
    removal_config = load_removal_config()
    if not removal_config:
        print("No removal configuration loaded")
        return False
    
    # Create canonical slug to clean model name mapping
    slug_mapping = create_slug_to_clean_name_mapping(provider_models)
    
    # Create removal index using slug mapping
    removal_index = create_removal_index(removal_config, slug_mapping)
    
    # Filter models
    finalized_models, removed_models = finalize_database_data(models, removal_index, provider_models, enrichment_config)
    
    # Save finalized data
    json_success = save_finalized_data(finalized_models)
    
    # Generate comprehensive report
    report_success = generate_removal_report(finalized_models, removed_models, removal_config)
    
    if json_success and report_success:
        print("="*60)
        print("DATABASE DATA FINALIZATION COMPLETE")
        print(f"Total input models: {len(models)}")
        print(f"Models kept: {len(finalized_models)}")
        print(f"Models removed: {len(removed_models)}")
        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("DATABASE DATA FINALIZATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)