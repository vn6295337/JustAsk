#!/usr/bin/env python3
"""
Google Models Data Normalization - Stage 5

This script handles Stage 5: Database Schema Normalization from ../02_outputs/04_enriched_modalities.json.
It normalizes enriched model data and outputs ../02_outputs/05_normalized_models.json and
../02_outputs/05_normalized_models_report.txt for final database insertion.
"""

import json
import csv
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    get_ist_timestamp,
    set_current_pipeline,
    get_project_root,
)
set_current_pipeline('google')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "google"


# =============================================================================
# CONFIGURATION LOADING FUNCTIONS
# =============================================================================

def load_filtering_configuration() -> Dict[str, Any]:
    """Load model filtering configuration from JSON file"""
    try:
        with open(CONFIG_DIR / 'filtering_rules.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ filtering_rules.json not found, returning Unknown")
        return "Unknown"

def load_modality_standardization() -> Dict[str, Any]:
    """Load modality standardization configuration from JSON file"""
    try:
        with open(CONFIG_DIR / 'modality_standardization.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ modality_standardization.json not found, returning Unknown")
        return "Unknown"

def load_license_configuration() -> Dict[str, Any]:
    """Load license configuration from 01_google_models_licenses.json"""
    try:
        with open(CONFIG_DIR / 'licenses.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ licenses.json not found, returning Unknown")
        return "Unknown"

def load_name_standardization_rules() -> Dict[str, Any]:
    """Load name standardization rules from 07_name_standardization_rules.json"""
    try:
        with open(CONFIG_DIR / 'name_standardization.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ name_standardization.json not found, returning Unknown")
        return "Unknown"


# =============================================================================
# PIPELINE CONFIGURATION
# =============================================================================

PIPELINE_CONFIG = {
    # OFFICIAL URLS: Model-family-specific documentation assignment
    'official_urls': {
        'Gemini': 'https://deepmind.google/models/gemini/',
        'Gemma': 'https://deepmind.google/models/gemma/', 
        'Embedding': 'https://ai.google.dev/gemini-api/docs/embeddings',
        'Imagen': 'https://deepmind.google/models/imagen/',
        'Veo': 'https://deepmind.google/models/veo/',
        'AQA': 'https://deepmind.google/models/gemini/'  # AQA uses Gemini URL per user instruction
    },
    
    # RATE LIMITS: Populated from official Google documentation
    'rate_limits_official': {
        # Gemini 2.5 models (latest)
        'gemini-2.5-pro': '5 requests/min, 250K tokens/min, 100 requests/day',
        'gemini-2.5-flash': '10 requests/min, 250K tokens/min, 250 requests/day',
        'gemini-2.5-flash-lite': '15 requests/min, 250K tokens/min, 1,000 requests/day',
        
        # Gemini 2.0 models
        'gemini-2.0-flash': '15 requests/min, 1M tokens/min, 200 requests/day',
        'gemini-2.0-flash-lite': '30 requests/min, 1M tokens/min, 200 requests/day',
        'gemini-2.0-flash-live': '15 requests/min, 1M tokens/min, 200 requests/day',
        
        # Gemini 1.5 models - Updated per user correction
        'gemini-1.5-pro': '15 requests/min, 250K tokens/min, 50 requests/day',
        'gemini-1.5-pro-002': '15 requests/min, 250K tokens/min, 50 requests/day',
        'gemini-1.5-flash': '15 requests/min, 250K tokens/min, 50 requests/day',
        'gemini-1.5-flash-8b': '15 requests/min, 250K tokens/min, 50 requests/day',
        
        # Gemma models (Open Source)
        'gemma': '30 requests/min, 15K tokens/min, 14,400 requests/day',
        
        # Embedding models
        'embedding': '100 requests/min, 30K tokens/min, 1,000 requests/day',
        
        # Image generation models  
        'imagen': 'Input: 480 tokens, Output: up to 4 images',
        
        # Video generation models
        'veo': 'Image input: up to 20MB, Output video: up to 2 minutes'
    }
}


# =============================================================================
# MODEL NAME NORMALIZATION
# =============================================================================

def apply_special_name_rules(name: str) -> str:
    """Apply special name standardization rules from configuration"""
    name_rules = load_name_standardization_rules()
    if name_rules == "Unknown":
        return name
    
    # Apply case corrections
    case_corrections = name_rules.get('case_corrections', {})
    for rule_name, rule_config in case_corrections.items():
        patterns = rule_config.get('patterns', [])
        replacement = rule_config.get('replacement', '')
        
        for pattern in patterns:
            if pattern in name:
                name = name.replace(pattern, replacement)
                break
    
    return name

def clean_model_name(name: str) -> str:
    """
    Clean and standardize model names per user requirements:
    - Remove hyphens except for flash-lite
    - Use title case
    - Use capitals for abbreviations like B in 27B and IT in -it
    - Apply special rules from 07_name_standardization_rules.json
    """
    # Remove common prefixes
    clean_name = re.sub(r'^models/', '', name)
    
    # User instruction: "rename Model that performs Attributed Question Answering as AQA"
    if 'aqa' in clean_name.lower() or 'attributed question answering' in clean_name.lower():
        return 'AQA'
    
    # Lowercase everything first
    clean_name = clean_name.lower()
    
    # Replace hyphens with spaces (including flash-lite)
    clean_name = clean_name.replace('-', ' ')
    
    # Clean up spacing before title case
    clean_name = re.sub(r'\s+', ' ', clean_name)
    
    # Apply title case
    clean_name = clean_name.title()
    
    # Force "B" capitalization for model sizes (numbers or alphanum like E4B)
    clean_name = re.sub(r'(\d+)([Bb])', r'\1B', clean_name)     # 27b → 27B
    clean_name = re.sub(r'([A-Za-z]\d+)([Bb])', r'\1B', clean_name)  # E4b → E4B
    
    # Handle all IT variations explicitly for maximum reliability
    clean_name = re.sub(r'\bIt\b', 'IT', clean_name)    # It → IT
    clean_name = re.sub(r'\bit\b', 'IT', clean_name)    # it → IT  
    clean_name = re.sub(r'\biT\b', 'IT', clean_name)    # iT → IT
    clean_name = re.sub(r'\bIT\b', 'IT', clean_name)    # IT → IT (already correct)
    
    # Restore flash-lite hyphen (final step after all other processing)
    clean_name = re.sub(r'\bFlash Lite\b', 'Flash-Lite', clean_name)
    
    # Fix version numbers and model identifiers
    clean_name = re.sub(r'\b001\b', '001', clean_name)
    clean_name = re.sub(r'\b002\b', '002', clean_name)
    clean_name = re.sub(r'\b004\b', '004', clean_name)
    
    # Apply special name rules (e.g., Gemma 3N → Gemma 3n)
    clean_name = apply_special_name_rules(clean_name)
    
    return clean_name


# =============================================================================
# MODALITY STANDARDIZATION
# =============================================================================

def standardize_modalities(modalities_str: str) -> str:
    """
    Standardize modality ordering using 02_modality_standardization.json
    Order is dynamically loaded from configuration file
    """
    if not modalities_str or modalities_str.strip() == '':
        return ''
    
    # Load standardization configuration
    config = load_modality_standardization()
    if config == "Unknown":
        # Handle special case for Text Embeddings even without config
        if 'embedding' in modalities_str.lower() and 'text' in modalities_str.lower():
            return 'Text Embeddings'
        return modalities_str  # Return as-is if no config available
    
    modality_mappings = config['modality_mappings']
    ordering_priority = config['ordering_priority']
    
    # Split and clean modalities
    modalities = [m.strip() for m in modalities_str.split(',') if m.strip()]
    
    # Normalize variations using configuration
    normalized = []
    for modality in modalities:
        modality_lower = modality.lower()
        
        # Handle "Text Embeddings" as special case first
        if 'embedding' in modality_lower and 'text' in modality_lower:
            normalized.append('Text Embeddings')
        else:
            # Check against modality mappings
            mapped = False
            for key, value in modality_mappings.items():
                if key in modality_lower:
                    normalized.append(value)
                    mapped = True
                    break
            
            if not mapped:
                normalized.append(modality)  # Keep original if unknown
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for modality in normalized:
        if modality not in seen:
            result.append(modality)
            seen.add(modality)
    
    # Sort by priority from 02_modality_standardization.json configuration
    # Text Embeddings gets same priority as Text
    result.sort(key=lambda x: ordering_priority.get(x, ordering_priority.get('Text', 1)) if 'Embeddings' in x else ordering_priority.get(x, 99))
    
    return ', '.join(result) if result else ''


# =============================================================================
# URL AND METADATA ASSIGNMENT
# =============================================================================

def get_official_url_google(model_name: str) -> str:
    """Get official URL based on model type"""
    name_lower = model_name.lower()
    
    if 'gemini' in name_lower:
        return PIPELINE_CONFIG['official_urls']['Gemini']
    elif 'gemma' in name_lower:
        return PIPELINE_CONFIG['official_urls']['Gemma']
    elif 'embedding' in name_lower:
        return PIPELINE_CONFIG['official_urls']['Embedding']
    elif 'imagen' in name_lower:
        return PIPELINE_CONFIG['official_urls']['Imagen']
    elif 'veo' in name_lower:
        return PIPELINE_CONFIG['official_urls']['Veo']
    else:
        return PIPELINE_CONFIG['official_urls']['Gemini']

def get_rate_limits_google(model_name: str) -> str:
    """
    Get rate limits based on official Google documentation
    Source: https://ai.google.dev/gemini-api/docs/rate-limits
    """
    name_lower = model_name.lower()
    rate_limits_map = PIPELINE_CONFIG['rate_limits_official']
    
    # Direct model pattern matching from official documentation
    for pattern, limits in rate_limits_map.items():
        if pattern.replace('-', '').replace(' ', '') in name_lower.replace('-', '').replace(' ', ''):
            return limits
    
    # Model family fallback based on official documentation categories
    if 'embedding' in name_lower:
        return rate_limits_map['embedding']
    elif 'imagen' in name_lower:
        return rate_limits_map['imagen']
    elif 'veo' in name_lower:
        return rate_limits_map['veo']
    elif 'gemma' in name_lower:
        return rate_limits_map['gemma']
    elif any(version in name_lower for version in ['2.5-pro', '2.5pro']):
        return rate_limits_map['gemini-2.5-pro']
    elif any(version in name_lower for version in ['2.5-flash', '2.5flash']):
        return rate_limits_map['gemini-2.5-flash']
    elif any(version in name_lower for version in ['2.0-flash', '2.0flash']):
        return rate_limits_map['gemini-2.0-flash']
    elif any(version in name_lower for version in ['1.5-flash', '1.5flash']):
        return rate_limits_map['gemini-1.5-flash']
    else:
        # Default for unmatched Gemini models
        return rate_limits_map['gemini-2.0-flash']

def get_license_info_google(model_name: str) -> Dict[str, str]:
    """
    Get license information from 01_google_models_licenses.json configuration file
    """
    name_lower = model_name.lower()
    license_config = load_license_configuration()
    if license_config == "Unknown":
        return {
            "license_info_text": "Unknown",
            "license_info_url": "Unknown",
            "license_name": "Unknown",
            "license_url": "Unknown"
        }
    
    google_models = license_config['google_models']
    
    if 'gemma' in name_lower:
        return google_models['gemma']
    elif any(family in name_lower for family in ['gemini', 'embedding', 'imagen', 'veo', 'aqa']):
        return google_models['gemini']
    else:
        # For all other models, use Gemini license details as default
        return google_models['gemini']


# =============================================================================
# GEMMA-SPECIFIC MODALITY HANDLING
# =============================================================================

def get_gemma_modalities(model_name: str) -> Dict[str, str]:
    """
    Get Gemma model specific modalities based on https://ai.google.dev/gemma/docs
    Returns dict with input_modalities and output_modalities
    """
    name_lower = model_name.lower()
    
    # Default Gemma models (text-only)
    default_modalities = {'input_modalities': 'Text', 'output_modalities': 'Text'}
    
    # Gemma 3 variants support text and image input
    if 'gemma 3' in name_lower and 'n' not in name_lower:  # Gemma 3 but not 3N
        return {'input_modalities': 'Image, Text', 'output_modalities': 'Text'}
    
    # Gemma 3N variants support audio input  
    elif 'gemma 3n' in name_lower:
        return {'input_modalities': 'Audio, Text', 'output_modalities': 'Text'}
    
    # PaliGemma for visual data processing
    elif 'pali' in name_lower:
        return {'input_modalities': 'Image, Text', 'output_modalities': 'Text'}
    
    # CodeGemma for programming tasks
    elif 'code' in name_lower:
        return {'input_modalities': 'Text', 'output_modalities': 'Text'}
    
    # ShieldGemma for safety evaluation
    elif 'shield' in name_lower:
        return {'input_modalities': 'Text', 'output_modalities': 'Text'}
    
    # Default for other Gemma variants
    return default_modalities


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_documentation_compliance(model_name: str, modalities: Dict[str, str]) -> bool:
    """
    Validate model data against official documentation standards using configuration
    """
    config = load_filtering_configuration()
    if config == "Unknown":
        return True
        
    validation_rules = config.get('validation_rules', {})
    
    # Check embedding output modality rule
    embedding_rule = validation_rules.get('embedding_output_modality', {})
    if embedding_rule and 'embedding' in model_name.lower():
        expected_output = embedding_rule.get('required_output', 'Text Embeddings')
        actual_output = modalities.get('output_modalities', '')
        if actual_output != expected_output:
            error_msg = embedding_rule.get('error_message', 'Output modality mismatch')
            print(f"⚠️  Documentation compliance issue: {model_name}")
            print(f"    Expected output: {expected_output}, Got: {actual_output}")
            print(f"    Rule: {error_msg}")
            return False
    
    return True


# =============================================================================
# SUPPORTING UTILITY FUNCTIONS
# =============================================================================

def enhance_license_information(model_name: str, current_license: Dict[str, str]) -> Dict[str, str]:
    """
    Enhance license information with patterns from database
    """
    # Use existing license mapping logic - already comprehensive
    return current_license

def standardize_provider_data(model_name: str, provider_country: str) -> str:
    """
    Standardize provider country data
    """
    # Google is consistently "United States"
    return 'United States'

def find_modality_mapping(model_name: str, modality_mapping: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """Find modality mapping using composite key matching"""
    # Try exact match first
    if model_name in modality_mapping:
        return modality_mapping[model_name]
    
    # Try matching against composite keys (display_name\napi_name format)
    for key, mapping in modality_mapping.items():
        if '\n' in key:
            display_name = key.split('\n')[0].strip()
            if display_name == model_name:
                return mapping
    
    return {}


# =============================================================================
# MAIN TRANSFORMATION FUNCTION
# =============================================================================

def transform_to_google_schema(row: Dict[str, str], modality_mapping: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """
    Transform flattened row to ai_models_main schema with documentation validation
    Implements official URL-driven requirements and enhanced normalization patterns
    """
    
    model_name = clean_model_name(row.get('name', ''))
    
    # Get modalities from mapping (documentation-sourced) or Gemma-specific
    modalities = find_modality_mapping(model_name, modality_mapping)
    
    # Apply Gemma-specific modality handling using https://ai.google.dev/gemma/docs
    if 'gemma' in model_name.lower():
        gemma_modalities = get_gemma_modalities(model_name)
        if not modalities:  # If no mapping found, use Gemma-specific
            modalities = gemma_modalities
        # Override with Gemma-specific if available
        input_modalities = gemma_modalities.get('input_modalities', modalities.get('input_modalities', 'Text'))
        output_modalities = gemma_modalities.get('output_modalities', modalities.get('output_modalities', 'Text'))
    else:
        input_modalities = modalities.get('input_modalities', 'Text')
        output_modalities = modalities.get('output_modalities', 'Text')
    
    # Apply documentation-based modality corrections per official sources
    config = load_filtering_configuration()
    if config != "Unknown":
        modality_mappings = config.get('modality_mappings_by_source', {})
        model_name_lower = model_name.lower()
        
        # Check each documentation source for pattern matches
        for source_type, source_config in modality_mappings.items():
            patterns = source_config.get('patterns', [])
            if any(pattern in model_name_lower for pattern in patterns):
                # Apply modalities from official documentation source
                doc_input = source_config.get('input_modalities')
                doc_output = source_config.get('output_modalities')
                
                # Only override if documentation specifies concrete modalities
                if doc_input and doc_input != 'varies_by_model':
                    input_modalities = doc_input
                if doc_output and doc_output != 'varies_by_model':
                    output_modalities = doc_output
                break
    
    # Apply modality standardization with proper ordering
    input_modalities = standardize_modalities(input_modalities)
    output_modalities = standardize_modalities(output_modalities)
    
    # Validate against documentation compliance
    validate_documentation_compliance(model_name, {'input_modalities': input_modalities, 'output_modalities': output_modalities})
    
    # Get official license info per user requirements
    license_info = get_license_info_google(model_name)
    
    # Enhance license information (using existing robust logic)
    enhanced_license = enhance_license_information(model_name, license_info)
    
    # Standardize provider data
    provider_country = standardize_provider_data(model_name, 'United States')
    
    # Build normalized record with official URL-driven data
    normalized = {
        'id': '',  # Auto-generated by database
        'inference_provider': 'Google',
        'model_provider': 'Google',
        'human_readable_name': model_name,
        'model_provider_country': provider_country,
        'official_url': get_official_url_google(model_name),  # Model-family specific URLs
        'input_modalities': input_modalities,
        'output_modalities': output_modalities,
        'license_info_text': enhanced_license['license_info_text'],
        'license_info_url': enhanced_license['license_info_url'],
        'license_name': enhanced_license['license_name'],
        'license_url': enhanced_license['license_url'],
        'rate_limits': get_rate_limits_google(model_name),  # From official documentation
        'provider_api_access': 'https://aistudio.google.com/apikey',
        'created_at': datetime.now().isoformat() + '+00:00',
        'updated_at': datetime.now().isoformat() + '+00:00'
    }
    
    return normalized


# =============================================================================
# PIPELINE FUNCTIONS
# =============================================================================

class GoogleNormalizationPipeline:
    def __init__(self):
        self.enriched_models = []
        self.normalized_models = []
        
    def load_enriched_data(self) -> bool:
        """Load enriched model data from 04_enriched_modalities.json"""
        try:
            with open(get_input_file_path('04_enriched_modalities.json'), 'r') as f:
                data = json.load(f)

                # Handle new JSON structure with metadata
                if isinstance(data, dict) and 'models' in data:
                    self.enriched_models = data['models']
                    print(f"✅ Loaded {len(self.enriched_models)} enriched models (with metadata)")
                elif isinstance(data, list):
                    self.enriched_models = data
                    print(f"✅ Loaded {len(self.enriched_models)} enriched models (legacy format)")
                else:
                    print(f"⚠️ Unexpected JSON structure in 04_enriched_modalities.json")
                    return False
                return True
        except FileNotFoundError:
            print(f"❌ {get_input_file_path('04_enriched_modalities.json')} not found")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing 04_enriched_modalities.json: {e}")
            return False
    
    def normalize_models(self) -> None:
        """Normalize all enriched models to database schema"""
        print(f"\n=== Normalizing {len(self.enriched_models)} models to database schema ===")
        
        for model in self.enriched_models:
            try:
                # Apply all normalization functions
                normalized_model = {
                    'id': '',  # Auto-generated by database
                    'inference_provider': 'Google',
                    'model_provider': 'Google',
                    'human_readable_name': clean_model_name(model.get('name', '')),
                    'provider_slug': model.get('provider_slug', ''),  # For working_version table
                    'model_provider_country': standardize_provider_data('', 'United States'),
                    'official_url': get_official_url_google(model.get('name', '')),
                    'input_modalities': standardize_modalities(model.get('input_modalities', 'Text')),
                    'output_modalities': standardize_modalities(model.get('output_modalities', 'Text')),
                    'rate_limits': get_rate_limits_google(model.get('name', '')),
                    'provider_api_access': 'https://aistudio.google.com/apikey',
                    'created_at': datetime.now().isoformat() + '+00:00',
                    'updated_at': datetime.now().isoformat() + '+00:00'
                }
                
                # Add license information
                license_info = get_license_info_google(model.get('name', ''))
                normalized_model.update({
                    'license_info_text': license_info['license_info_text'],
                    'license_info_url': license_info['license_info_url'],
                    'license_name': license_info['license_name'],
                    'license_url': license_info['license_url']
                })
                
                self.normalized_models.append(normalized_model)
                
            except Exception as e:
                print(f"❌ Error normalizing model {model.get('name', 'Unknown')}: {e}")
                continue
        
        print(f"✅ Successfully normalized {len(self.normalized_models)} models")
    
    def save_json_output(self) -> None:
        """Save normalized data to JSON file"""
        if not self.normalized_models:
            print("⚠️ No normalized models found - saving empty file")
            # Generate empty output file to maintain pipeline consistency
            try:
                with open(get_output_file_path('05_normalized_models.json'), 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
                print("✅ Saved empty normalized models file for pipeline consistency")
            except Exception as e:
                print(f"❌ Error saving empty JSON file: {e}")
            return

        try:
            with open(get_output_file_path('05_normalized_models.json'), 'w', encoding='utf-8') as f:
                json.dump(self.normalized_models, f, indent=2, ensure_ascii=False)

            print(f"✅ Saved {len(self.normalized_models)} normalized models to {get_output_file_path('05_normalized_models.json')}")
            
        except Exception as e:
            print(f"❌ Error saving JSON file: {e}")
    
    def generate_report(self) -> None:
        """Generate human-readable normalization report"""
        report_content = []

        # Header
        report_content.append("=== GOOGLE MODELS DATA NORMALIZATION REPORT ===")
        report_content.append(f"Generated: {get_ist_timestamp()}")
        report_content.append("")
        
        # Summary
        report_content.append("=== SUMMARY ===")
        report_content.append(f"Total Models Processed: {len(self.enriched_models)}")
        report_content.append(f"Successfully Normalized: {len(self.normalized_models)}")
        report_content.append(f"Normalization Success Rate: {len(self.normalized_models)/len(self.enriched_models)*100:.1f}%")
        report_content.append("")
        
        # Detailed model information
        report_content.append("=== NORMALIZED MODELS ===")
        for i, model in enumerate(self.normalized_models, 1):
            report_content.append(f"{i:3}. {model['human_readable_name']}")
            report_content.append(f"     ID: {model['id']}")
            report_content.append(f"     Inference Provider: {model['inference_provider']}")
            report_content.append(f"     Model Provider: {model['model_provider']}")
            report_content.append(f"     Model Provider Country: {model['model_provider_country']}")
            report_content.append(f"     Official URL: {model['official_url']}")
            report_content.append(f"     Input Modalities: {model['input_modalities']}")
            report_content.append(f"     Output Modalities: {model['output_modalities']}")
            report_content.append(f"     License Info Text: {model['license_info_text']}")
            report_content.append(f"     License Info URL: {model['license_info_url']}")
            report_content.append(f"     License Name: {model['license_name']}")
            report_content.append(f"     License URL: {model['license_url']}")
            report_content.append(f"     Rate Limits: {model['rate_limits']}")
            report_content.append(f"     Provider API Access: {model['provider_api_access']}")
            report_content.append(f"     Created At: {model['created_at']}")
            report_content.append(f"     Updated At: {model['updated_at']}")
            report_content.append("")
        
        # Save report
        try:
            with open(get_output_file_path('05_normalized_models_report.txt'), 'w') as f:
                f.write('\n'.join(report_content))
            print(f"✅ Normalization report saved to {get_output_file_path('05_normalized_models_report.txt')}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
    
    def run_normalization_pipeline(self) -> None:
        """Run the complete normalization pipeline"""
        print("=== Google Models Data Normalization Pipeline - Stage 5 ===")
        print(f"Started at: {get_ist_timestamp()}")
        print("="*80)
        
        # Load enriched data
        if not self.load_enriched_data():
            print("⚠️ Cannot load enriched data - generating empty output files")
            # Generate empty output files to maintain pipeline consistency
            self.save_json_output()
            self.save_txt_report()
            return
        
        # Normalize models
        self.normalize_models()
        
        # Save outputs
        self.save_json_output()
        self.generate_report()
        
        print("\n" + "="*80)
        print("STAGE 5 COMPLETE - DATA NORMALIZATION")
        print("="*80)
        print(f"Input: {get_input_file_path('04_enriched_modalities.json')} ({len(self.enriched_models)} models)")
        print(f"Output: {get_output_file_path('05_normalized_models.json')} ({len(self.normalized_models)} models)")
        print(f"Report: {get_output_file_path('05_normalized_models_report.txt')}")
        print("="*80)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    pipeline = GoogleNormalizationPipeline()
    pipeline.run_normalization_pipeline()