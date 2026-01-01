#!/usr/bin/env python3
"""
Provider Information Enrichment
Takes standardized modalities and enriches with provider information

Input: 15_standardized_modalities.json (standardized modality data)
Config: provider_enrichment.json (provider mappings and static fields)
Output: 16_provider_enriched.json + human readable report

Adds fields:
- inference_provider (static: "OpenRouter")
- model_provider (extracted from canonical_slug and mapped)
- model_provider_country (from provider mappings)
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

def load_standardized_modalities() -> List[Dict[str, Any]]:
    """Load standardized modalities from Stage-O"""
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
        print(f"✓ Loaded {len(models)} models with standardized modalities from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load standardized modalities from {input_file}: {error}")
        return []

def load_provider_enrichment_config() -> Dict[str, Any]:
    """Load provider enrichment configuration"""
    config_file = CONFIG_DIR / "provider_enrichment.json"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded provider enrichment config from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load provider config from {config_file}: {error}")
        return {}

def extract_provider_slug(canonical_slug: str) -> str:
    """Extract provider slug from canonical_slug (part before first slash)"""
    if '/' in canonical_slug:
        return canonical_slug.split('/', 1)[0].lower()
    return canonical_slug.lower()

def extract_model_family(canonical_slug: str, config: Dict[str, Any]) -> str:
    """Extract model family from canonical_slug - family patterns only for Google models, model name for others"""
    if '/' not in canonical_slug:
        return "Unknown"
    
    provider_slug = canonical_slug.split('/', 1)[0].lower()
    model_part = canonical_slug.split('/', 1)[1].lower()
    
    # For Google models, use family pattern matching
    if provider_slug == 'google':
        family_patterns = config.get('model_family_patterns', {})
        
        # Check each family pattern
        for family, patterns in family_patterns.items():
            for pattern in patterns:
                if model_part.startswith(pattern.lower()):
                    return family
        
        # If no pattern matches, try to extract the first part before any delimiter
        for delimiter in ['-', '_', '.']:
            if delimiter in model_part:
                first_part = model_part.split(delimiter, 1)[0]
                # Check if this first part matches any family
                for family, patterns in family_patterns.items():
                    if first_part in [p.lower() for p in patterns]:
                        return family
                break
        
        return "Unknown"
    
    # For non-Google models, return normalized provider name for URL mapping
    provider_mappings = config.get('provider_mappings', {})
    if provider_slug in provider_mappings:
        provider_name = provider_mappings[provider_slug][0]  # Get provider name from [name, country] tuple
        # Normalize provider names to match URL keys
        normalized_name = provider_name.lower()
        return normalized_name
    return provider_slug.lower()

def get_official_url(model_family: str, config: Dict[str, Any]) -> str:
    """Get official URL for model family"""
    family_urls = config.get('family_official_urls', {})
    # Model family should already be normalized (lowercase), so direct lookup
    return family_urls.get(model_family, "Unknown")

def enrich_provider_info(models: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Enrich models with provider information"""
    enriched_models = []
    
    static_fields = config.get('static_fields', {})
    provider_mappings = config.get('provider_mappings', {})
    
    print(f"Enriching {len(models)} models with provider information...")
    
    unmapped_providers = set()
    unmapped_families = set()
    mapped_count = 0
    unmapped_count = 0
    family_mapped_count = 0
    family_unmapped_count = 0
    
    for model in models:
        canonical_slug = model.get('canonical_slug', '')
        provider_slug = extract_provider_slug(canonical_slug)
        
        # Get provider mapping
        if provider_slug in provider_mappings:
            provider_name, provider_country = provider_mappings[provider_slug]
            mapped_count += 1
        else:
            provider_name = "Unknown"
            provider_country = "Unknown"
            unmapped_providers.add(provider_slug)
            unmapped_count += 1
        
        # Get model family and official URL
        model_family = extract_model_family(canonical_slug, config)
        official_url = get_official_url(model_family, config)
        
        if model_family != "Unknown":
            family_mapped_count += 1
        else:
            family_unmapped_count += 1
            unmapped_families.add(canonical_slug)
        
        # Create enriched model record
        # Extract provider_slug: everything after the provider prefix (e.g., "x-ai/grok-4.1-fast" -> "grok-4.1-fast")
        provider_slug_value = canonical_slug.split('/', 1)[1] if '/' in canonical_slug else canonical_slug

        enriched_model = {
            'id': model.get('id', ''),
            'canonical_slug': canonical_slug,
            'provider_slug': provider_slug_value,
            'original_name': model.get('original_name', ''),
            'hugging_face_id': model.get('hugging_face_id', ''),
            'clean_model_name': model.get('clean_model_name', ''),
            'raw_input_modalities': model.get('raw_input_modalities', ''),
            'raw_output_modalities': model.get('raw_output_modalities', ''),
            'enhanced_input_modalities': model.get('enhanced_input_modalities', ''),
            'enhanced_output_modalities': model.get('enhanced_output_modalities', ''),
            'standardized_input_modalities': model.get('standardized_input_modalities', ''),
            'standardized_output_modalities': model.get('standardized_output_modalities', ''),
            'google_enhancement_status': model.get('google_enhancement_status', ''),
            'inference_provider': static_fields.get('inference_provider', 'OpenRouter'),
            'model_provider': provider_name,
            'model_provider_country': provider_country,
            'model_family': model_family,
            'official_url': official_url
        }
        
        enriched_models.append(enriched_model)
    
    print(f"✓ Provider enrichment complete for {len(enriched_models)} models")
    print(f"  Mapped providers: {mapped_count} models")
    print(f"  Mapped families: {family_mapped_count} models")
    if unmapped_count > 0:
        print(f"  Unmapped providers: {unmapped_count} models")
        print(f"  Unmapped provider slugs: {sorted(unmapped_providers)}")
    if family_unmapped_count > 0:
        print(f"  Unmapped families: {family_unmapped_count} models")
        print(f"  Sample unmapped family slugs: {sorted(list(unmapped_families))[:5]}")
    
    return enriched_models

def save_provider_enriched_json(enriched_models: List[Dict[str, Any]]) -> str:
    """Save provider enriched models to JSON file"""
    output_file = get_output_file_path('16_provider_enriched.json')
    
    try:
        # Create output data with metadata
        output_data = {
            "metadata": {
                "generated_at": get_ist_timestamp(),
                "total_models": len(enriched_models),
                "pipeline_stage": "P_enrich_provider_info"
            },
            "models": enriched_models
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved provider enriched models to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_provider_enriched_report(enriched_models: List[Dict[str, Any]]) -> str:
    """Generate human readable report"""
    report_file = get_output_file_path('16_provider_enriched_report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("PROVIDER ENRICHED MODELS REPORT\n")
            f.write(f"Generated: {get_ist_timestamp()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models      : {len(enriched_models)}\n")
            f.write(f"  Input             : 15_standardized_modalities.json\n")
            f.write(f"  Config            : provider_enrichment.json\n")
            f.write(f"  Processor         : step_16_enrich_provider.py\n")
            f.write(f"  Output            : 16_provider_enriched.json\n\n")
            
            # Unknown mappings section for action items
            unknown_providers = set()
            unknown_families = set()
            unknown_urls = set()
            
            for model in enriched_models:
                if model.get('model_provider') == 'Unknown':
                    unknown_providers.add(model.get('canonical_slug', ''))
                if model.get('model_family') == 'Unknown':
                    unknown_families.add(model.get('canonical_slug', ''))
                if model.get('official_url') == 'Unknown':
                    unknown_urls.add(f"{model.get('model_family', '')} ({model.get('canonical_slug', '')})")
            
            if unknown_providers or unknown_families or unknown_urls:
                f.write(f"ACTION ITEMS - UNKNOWN MAPPINGS:\n")
                f.write("=" * 50 + "\n")
                
                if unknown_providers:
                    f.write(f"UNKNOWN PROVIDERS ({len(unknown_providers)} models):\n")
                    f.write("  Add these provider mappings to provider_enrichment.json:\n")
                    for slug in sorted(unknown_providers)[:10]:  # Show first 10
                        provider_slug = slug.split('/', 1)[0] if '/' in slug else slug
                        f.write(f"    \"{provider_slug}\": [\"Provider Name\", \"Country\"],\n")
                    if len(unknown_providers) > 10:
                        f.write(f"    ... and {len(unknown_providers) - 10} more\n")
                    f.write("\n")
                
                if unknown_families:
                    f.write(f"UNKNOWN FAMILIES ({len(unknown_families)} models):\n")
                    f.write("  Google models missing family patterns:\n")
                    google_unknowns = [slug for slug in unknown_families if slug.startswith('google/')]
                    for slug in sorted(google_unknowns)[:5]:
                        model_part = slug.split('/', 1)[1] if '/' in slug else slug
                        f.write(f"    {slug} -> add pattern for '{model_part}'\n")
                    f.write("\n")
                
                if unknown_urls:
                    f.write(f"UNKNOWN OFFICIAL URLS ({len(unknown_urls)} unique families):\n")
                    f.write("  Add these URL mappings to family_official_urls:\n")
                    unique_families = set()
                    for entry in sorted(unknown_urls)[:10]:
                        family = entry.split(' (')[0]
                        if family not in unique_families and family != 'Unknown':
                            unique_families.add(family)
                            f.write(f"    \"{family.lower()}\": \"https://official-url-here\",\n")
                    f.write("\n")
                
                f.write("=" * 50 + "\n\n")
            else:
                f.write(f"✓ ALL PROVIDERS AND FAMILIES MAPPED SUCCESSFULLY\n\n")
            
            # Provider distribution analysis
            provider_counts = {}
            country_counts = {}
            family_counts = {}
            
            for model in enriched_models:
                model_provider = model.get('model_provider', '')
                country = model.get('model_provider_country', '')
                model_family = model.get('model_family', '')
                
                provider_counts[model_provider] = provider_counts.get(model_provider, 0) + 1
                country_counts[country] = country_counts.get(country, 0) + 1
                family_counts[model_family] = family_counts.get(model_family, 0) + 1
            
            # Model provider distribution
            f.write(f"MODEL PROVIDER DISTRIBUTION:\n")
            sorted_providers = sorted(provider_counts.items(), key=lambda x: (-x[1], x[0]))
            for provider, count in sorted_providers:
                f.write(f"  {count:2d} models: {provider}\n")
            f.write(f"\nTotal unique model providers: {len(provider_counts)}\n\n")
            
            # Country distribution
            f.write(f"MODEL PROVIDER COUNTRY DISTRIBUTION:\n")
            sorted_countries = sorted(country_counts.items(), key=lambda x: (-x[1], x[0]))
            for country, count in sorted_countries:
                f.write(f"  {count:2d} models: {country}\n")
            f.write(f"\nTotal unique countries: {len(country_counts)}\n\n")
            
            
            # Model family distribution
            f.write(f"MODEL FAMILY DISTRIBUTION:\n")
            sorted_families = sorted(family_counts.items(), key=lambda x: (-x[1], x[0]))
            for family, count in sorted_families:
                f.write(f"  {count:2d} models: {family}\n")
            f.write(f"\nTotal unique model families: {len(family_counts)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED PROVIDER ENRICHED MODEL INFORMATION:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by model family, then provider, then name
            sorted_models = sorted(
                enriched_models,
                key=lambda x: (x.get('model_family', ''),
                              x.get('model_provider', ''),
                              x.get('clean_model_name', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Standardized field ordering: identifiers → names → providers
                f.write(f"  ID: {model.get('id', '')}\n")
                f.write(f"  Original Name: {model.get('original_name', '')}\n")
                f.write(f"  HuggingFace ID: {model.get('hugging_face_id', '')}\n")
                f.write(f"  Canonical Slug: {model.get('canonical_slug', '')}\n")
                f.write(f"  Clean Model Name: {model.get('clean_model_name', '')}\n")
                f.write(f"  Model Provider: {model.get('model_provider', '')}\n")
                f.write(f"  Model Provider Country: {model.get('model_provider_country', '')}\n")
                f.write(f"  Model Family: {model.get('model_family', '')}\n")
                f.write(f"  Official URL: {model.get('official_url', '')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Provider enriched report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Provider Information Enrichment")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load standardized modalities from Stage-O
    models = load_standardized_modalities()
    if not models:
        print("No standardized modalities loaded")
        return False
    
    # Load provider enrichment configuration
    config = load_provider_enrichment_config()
    if not config:
        print("No provider enrichment configuration loaded")
        return False
    
    # Enrich models with provider information
    enriched_models = enrich_provider_info(models, config)
    
    if not enriched_models:
        print("No models enriched")
        return False
    
    # Save JSON output
    json_success = save_provider_enriched_json(enriched_models)
    
    # Generate report
    report_success = generate_provider_enriched_report(enriched_models)
    
    if json_success and report_success:
        print("="*60)
        print("PROVIDER INFORMATION ENRICHMENT COMPLETE")
        print(f"Total models processed: {len(enriched_models)}")
        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("PROVIDER INFORMATION ENRICHMENT FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)