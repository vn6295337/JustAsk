#!/usr/bin/env python3
"""
Groq Data Processing Module
===========================

Modular data processing functions for the Groq pipeline including
data normalization, report generation, and configuration management.

Features:
- Data normalization with standardization rules
- Configuration loading utilities
- Report generation functions
- Model name standardization logic
- Timestamp formatting and modality processing

Author: AI Models Discovery Pipeline
Version: 1.0
"""

import json
import csv
import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .config_manager import get_config
from .path_manager import get_output_path, get_config_path


class GroqDataProcessor:
    """Data processing and normalization for Groq pipeline"""

    def __init__(self):
        """Initialize data processor with configuration"""
        self.config = get_config()

    def extract_final_model_slug(self, model_id: str) -> str:
        """
        Extracts the final clean model slug by:
        1. Using a regex to dynamically identify and strip the non-standard
           Groq prefix (e.g., '8B', 'Whisper', 'Turbo'). This fulfills the
           programmatic breakpoint identification requirement.
        2. Splitting by the forward slash '/' to remove upstream provider
           prefixes (e.g., 'meta-llama/' or 'openai/').

        Args:
            model_id: Raw model ID from scraper (e.g., "8Bllama-3.1-8b-instant")

        Returns:
            Clean model slug (e.g., "llama-3.1-8b-instant")
        """
        # Step 1: Dynamically Strip the Groq-specific prefix
        # Regex:
        #   Group 1: (\d+[B]?|[A-Z][A-Za-z]*) - Matches the prefix:
        #            - \d+[B]?        (e.g., 8B, 70B, 120B)
        #            - [A-Z][A-Za-z]* (e.g., Whisper, Turbo)
        #   Group 2: ([a-z].*$) - Captures the slug: The remainder of the string
        #            must start with a lowercase letter.
        # IMPORTANT: Anchor to start with ^ to prevent mid-string matching
        match = re.search(r'^(\d+[B]?|[A-Z][A-Za-z]*)([a-z].*$)', model_id)

        intermediate_slug = model_id
        if match:
            # Group 2 is the actual model slug (e.g., 'llama-3.1-8b-instant', 'openai/gpt-oss-120b')
            intermediate_slug = match.group(2)

        # Step 2: Check for a forward slash delimiter and extract the final model name
        # This is your final check to get the model name after the provider prefix (e.g., 'meta-llama/')
        if '/' in intermediate_slug:
            # Capture only the portion AFTER the LAST forward slash (the actual model name)
            return intermediate_slug.split('/')[-1]

        # Step 3: If no slash is found, return the intermediate slug
        return intermediate_slug

    def load_json_file(self, filename: str) -> Dict[str, Any]:
        """
        Load JSON file with error handling

        Args:
            filename: Filename relative to 02_outputs directory

        Returns:
            Dictionary containing loaded data
        """
        file_path = get_output_path(filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in {filename}: {e}")
            return {}

    def load_special_model_rules(self) -> Dict[str, str]:
        """
        Load special model name conversion rules

        Returns:
            Dictionary mapping model IDs to human-readable names
        """
        return self.config.get_special_model_rules()

    def clean_model_name(self, model_id: str, standardization_rules: Dict[str, Any]) -> str:
        """
        Clean and standardize model name with special rules support

        Args:
            model_id: Original model ID
            standardization_rules: Standardization configuration

        Returns:
            Cleaned and standardized model name
        """
        # Load special model rules
        special_rules = self.load_special_model_rules()

        # Extract base name (remove provider prefix if exists)
        base_name = model_id.split('/')[-1] if '/' in model_id else model_id

        # Check for special conversion rules first
        if base_name in special_rules:
            return special_rules[base_name]

        # Apply standard processing
        name = model_id

        # Remove patterns
        for pattern in standardization_rules.get('remove_patterns', []):
            name = name.replace(pattern, '')

        # Replace patterns
        for old, new in standardization_rules.get('replace_patterns', {}).items():
            name = name.replace(old, new)

        # Extract human readable name (remove provider prefix if exists)
        if '/' in name:
            name = name.split('/')[-1]

        # Capitalize first letter of each word
        name = ' '.join(word.capitalize() for word in name.replace('-', ' ').split())

        return name

    def get_provider_info(self, model_provider: str, provider_mappings: Dict[str, Any]) -> Tuple[str, str]:
        """
        Get provider country and official URL

        Args:
            model_provider: Provider name
            provider_mappings: Provider configuration

        Returns:
            Tuple of (country, official_url)
        """
        provider_data = provider_mappings.get('provider_mappings', {}).get(model_provider.lower(), [model_provider, "Unknown"])
        country = provider_data[1] if len(provider_data) > 1 else "Unknown"

        official_urls = provider_mappings.get('official_urls', {})
        official_url = official_urls.get(model_provider, "")

        return country, official_url

    def load_modality_standardization(self) -> Tuple[Dict[str, str], Dict[str, int]]:
        """
        Load modality standardization mappings

        Returns:
            Tuple of (modality_mappings, ordering_priority)
        """
        config = self.config.get_modality_standardization()
        mappings = config.get('modality_mappings', {})
        ordering = config.get('ordering_priority', {})
        return mappings, ordering

    def load_timestamp_patterns(self) -> Dict[str, str]:
        """
        Load timestamp formatting patterns

        Returns:
            Dictionary containing timestamp patterns
        """
        return self.config.get_timestamp_patterns()

    def standardize_modalities(self, modalities_list: List[str], modality_mappings: Dict[str, str]) -> List[str]:
        """
        Standardize modality names using mappings

        Args:
            modalities_list: List of raw modality names
            modality_mappings: Standardization mappings

        Returns:
            List of standardized modality names
        """
        if not modalities_list:
            return []

        standardized = []
        for modality in modalities_list:
            standardized_mod = modality_mappings.get(modality.lower(), modality)
            if standardized_mod not in standardized:
                standardized.append(standardized_mod)

        return standardized

    def sort_modalities(self, modalities_list: List[str], ordering_priority: Dict[str, int]) -> List[str]:
        """
        Sort modalities based on priority order

        Args:
            modalities_list: List of modalities to sort
            ordering_priority: Priority mappings

        Returns:
            Sorted list of modalities
        """
        if not modalities_list or not ordering_priority:
            return modalities_list

        return sorted(modalities_list, key=lambda x: ordering_priority.get(x, 999))

    def format_timestamp(self, unix_timestamp: Optional[int], timestamp_patterns: Dict[str, str]) -> str:
        """
        Format timestamp using standardized patterns

        Args:
            unix_timestamp: Unix timestamp or None
            timestamp_patterns: Formatting patterns

        Returns:
            Formatted timestamp string
        """
        if not timestamp_patterns:
            # Fallback to default formatting
            if unix_timestamp:
                return datetime.fromtimestamp(int(unix_timestamp)).isoformat() + '+00:00'
            else:
                return datetime.now().isoformat() + '+00:00'

        try:
            if unix_timestamp:
                # Use unix conversion template
                return datetime.fromtimestamp(int(unix_timestamp)).isoformat() + '+00:00'
            else:
                # Use default fallback template
                return datetime.now().isoformat() + '+00:00'
        except (ValueError, TypeError):
            # Error handling - use fallback
            return datetime.now().isoformat() + '+00:00'

    def get_modalities(self, model_id: str, modalities_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Get input/output modalities for a model with standardization

        Args:
            model_id: Model identifier
            modalities_data: Modalities dataset

        Returns:
            Tuple of (input_modalities_str, output_modalities_str)
        """
        model_data = modalities_data.get('modalities', {}).get(model_id, {})

        # Load standardization mappings
        modality_mappings, ordering_priority = self.load_modality_standardization()

        # Get raw modalities
        input_modalities = model_data.get('input_modalities', [])
        output_modalities = model_data.get('output_modalities', [])

        # Standardize and sort modalities
        input_standardized = self.standardize_modalities(input_modalities, modality_mappings)
        output_standardized = self.standardize_modalities(output_modalities, modality_mappings)

        input_sorted = self.sort_modalities(input_standardized, ordering_priority)
        output_sorted = self.sort_modalities(output_standardized, ordering_priority)

        # Join with commas and spaces for proper formatting
        input_mods = ', '.join(input_sorted)
        output_mods = ', '.join(output_sorted)

        return input_mods, output_mods

    def get_license_info(self, model_id: str, model_provider: str, license_mappings: Dict[str, Any]) -> Tuple[str, str, str, str]:
        """
        Get license information for a specific model

        Args:
            model_id: Model identifier
            model_provider: Model provider name
            license_mappings: License mappings data

        Returns:
            Tuple of (license_info_text, license_info_url, license_name, license_url)
        """
        # Get provider's license mappings
        provider_licenses = license_mappings.get('provider_license_mappings', {}).get(model_provider, {})

        # Extract model key (remove provider prefix if exists)
        model_key = model_id.split('/')[-1] if '/' in model_id else model_id

        # Get model-specific license info
        model_license_info = provider_licenses.get(model_key, {})

        license_info_text = model_license_info.get('license_info_text', '')
        license_info_url = model_license_info.get('license_info_url', '')
        license_name = model_license_info.get('license_name', '')
        license_url = model_license_info.get('license_url', '')

        # If no license_url in model info, try to get from global license_urls mapping
        if not license_url and license_name:
            license_url = license_mappings.get('license_urls', {}).get(license_name, '')

        return license_info_text, license_info_url, license_name, license_url

    def format_rate_limits(self, model_id: str, rate_limits_data: Dict[str, Any]) -> str:
        """
        Format rate limits data

        Args:
            model_id: Model identifier
            rate_limits_data: Rate limits dataset

        Returns:
            Formatted rate limits string
        """
        model_limits = rate_limits_data.get('rate_limits', {}).get(model_id, {})
        if not model_limits:
            return ""

        # Format as "RPM: X, TPM: Y, RPD: Z, TPD: W"
        rpm = model_limits.get('RPM', '')
        tpm = model_limits.get('TPM', '')
        rpd = model_limits.get('RPD', '')
        tpd = model_limits.get('TPD', '')
        ash = model_limits.get('ASH', '')
        asd = model_limits.get('ASD', '')

        parts = []
        if rpm and rpm != '-': parts.append(f"RPM: {rpm}")
        if tpm and tpm != '-': parts.append(f"TPM: {tpm}")
        if rpd and rpd != '-': parts.append(f"RPD: {rpd}")
        if tpd and tpd != '-': parts.append(f"TPD: {tpd}")
        if ash and ash != '-': parts.append(f"ASH: {ash}")
        if asd and asd != '-': parts.append(f"ASD: {asd}")

        return ', '.join(parts)

    def generate_normalization_report(self, production_models: Dict[str, Any], normalized_data: List[Dict[str, Any]],
                                    report_filename: Optional[str] = None) -> str:
        """
        Generate detailed normalization report

        Args:
            production_models: Production models data
            normalized_data: Normalized data records
            report_filename: Optional custom report filename

        Returns:
            Path to generated report file
        """
        if not report_filename:
            report_filename = '06_normalized_models_report.txt'

        report_path = get_output_path(report_filename)

        total_extracted = len(production_models.get('production_models', []))
        total_normalized = len(normalized_data)
        success_rate = (total_normalized / total_extracted * 100) if total_extracted > 0 else 0

        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("GROQ PIPELINE NORMALIZATION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            # Summary
            f.write("SUMMARY:\n")
            f.write(f"  Total models extracted: {total_extracted}\n")
            f.write(f"  Models filtered out: 0\n")  # Groq only extracts production models
            f.write(f"  Models normalized: {total_normalized}\n")
            f.write(f"  Models unchanged: 0\n")
            f.write(f"  Success rate: {success_rate:.1f}%\n\n")

            # Models normalized details
            f.write(f"MODELS NORMALIZED: {total_normalized}\n")
            f.write("-" * 40 + "\n")

            for idx, record in enumerate(normalized_data, 1):
                provider = record['model_provider'].upper()
                human_name = record['human_readable_name']

                # Find original model data by matching record ID with list index
                original_model = None
                original_model_id = ""
                production_models_list = production_models.get('production_models', [])
                if idx <= len(production_models_list):
                    original_model = production_models_list[idx - 1]  # idx is 1-based, list is 0-based
                    original_model_id = original_model.get('model_id', '')

                f.write(f"   {idx}. {provider} - {human_name}\n")
                if original_model_id and original_model_id != human_name:
                    f.write(f"      Model Name: {original_model_id} -> {human_name}\n")

                # Input/Output modalities
                if record.get('input_modalities'):
                    f.write(f"      Input Modalities: {record['input_modalities']}\n")
                if record.get('output_modalities'):
                    f.write(f"      Output Modalities: {record['output_modalities']}\n")

                # License info
                if record.get('license_name'):
                    f.write(f"      License: {record.get('license_info_text', '')} -> {record['license_name']}\n")

                # Rate limits summary
                if record.get('rate_limits'):
                    rate_limits_display = record['rate_limits'][:50]
                    if len(record['rate_limits']) > 50:
                        rate_limits_display += '...'
                    f.write(f"      Rate Limits: {rate_limits_display}\n")

                f.write("\n")

            # Provider summary
            f.write("PROVIDER SUMMARY:\n")
            f.write("-" * 40 + "\n")

            provider_counts = {}
            for record in normalized_data:
                provider = record['model_provider']
                provider_counts[provider] = provider_counts.get(provider, 0) + 1

            for provider, count in sorted(provider_counts.items()):
                f.write(f"  {provider}: {count} models\n")

            f.write(f"\nTotal providers: {len(provider_counts)}\n")

        print(f"📄 Normalization report generated: {report_path}")
        return str(report_path)

    def populate_normalized_data(self) -> List[Dict[str, Any]]:
        """
        Populate normalized data from all extracted sources

        Returns:
            List of normalized data records
        """
        print("\n" + "=" * 80)
        print("🚀 STAGE 5: DATA NORMALIZATION")
        print("=" * 80)
        print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Load all data files
        print("Loading data files...")
        production_models = self.load_json_file('01_scraped_models.json')
        modalities = self.load_json_file('02_scraped_modalities.json')
        provider_mappings = self.config.get_provider_mappings()
        license_mappings = self.load_json_file('05_consolidated_licenses.json')
        database_schema = self.config.get_database_schema()

        # Get standardization rules
        standardization = provider_mappings.get('model_name_standardization', {})

        # Load timestamp patterns
        timestamp_patterns = self.load_timestamp_patterns()

        normalized_data = []
        current_timestamp = datetime.now().isoformat() + '+00:00'

        production_models_list = production_models.get('production_models', [])
        print(f"Processing {len(production_models_list)} models...")

        # Process each production model
        for idx, model in enumerate(production_models_list, 1):
            model_id = model['model_id']
            model_provider = model['model_provider']

            print(f"Processing {model_id}...")

            # Get provider info
            country, official_url = self.get_provider_info(model_provider, provider_mappings)

            # Get modalities
            input_mods, output_mods = self.get_modalities(model_id, modalities)

            # Get license info
            license_text, license_url_info, license_name, license_url = self.get_license_info(model_id, model_provider, license_mappings)

            # Get rate limits directly from model (now stored in production models JSON)
            rate_limits_str = model.get('rate_limits', '')

            # Create normalized record
            record = {
                'id': idx,
                'inference_provider': 'Groq',
                'model_provider': model_provider,
                'human_readable_name': self.clean_model_name(model_id, standardization),
                'provider_slug': self.extract_final_model_slug(model_id),
                'model_provider_country': country,
                'official_url': official_url,
                'input_modalities': input_mods,
                'output_modalities': output_mods,
                'license_info_text': license_text,
                'license_info_url': license_url_info,
                'license_name': license_name,
                'license_url': license_url,
                'rate_limits': rate_limits_str,
                'provider_api_access': 'https://console.groq.com/keys',
                'created_at': self.format_timestamp(model.get('created'), timestamp_patterns),
                'updated_at': current_timestamp
            }

            normalized_data.append(record)

        # Save as JSON
        json_filename = '06_normalized_models.json'
        json_path = get_output_path(json_filename)
        print(f"Writing to {json_path}...")

        normalization_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_models': len(normalized_data),
                'pipeline_stage': '06_normalize_data',
                'source_files': [
                    '01_scraped_models.json',
                    '02_scraped_modalities.json',
                    '05_consolidated_licenses.json'
                ]
            },
            'models': normalized_data
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(normalization_data, f, indent=2)

        # Create TXT report
        txt_filename = json_filename.replace('.json', '-report.txt')
        txt_path = get_output_path(txt_filename)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("GROQ DATA NORMALIZATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {normalization_data['metadata']['generated_at']}\n")
            f.write(f"Total Models: {normalization_data['metadata']['total_models']}\n")
            f.write(f"Pipeline Stage: {normalization_data['metadata']['pipeline_stage']}\n\n")

            f.write("SOURCE FILES:\n")
            f.write("-" * 40 + "\n")
            for source_file in normalization_data['metadata']['source_files']:
                f.write(f"• {source_file}\n")
            f.write("\n")

            f.write("NORMALIZED MODEL DATA:\n")
            f.write("-" * 80 + "\n")
            for i, model in enumerate(normalized_data[:5], 1):  # Show first 5 models
                f.write(f"Model {i}: {model.get('human_readable_name', 'N/A')}\n")
                f.write(f"  Provider: {model.get('model_provider', 'N/A')}\n")
                f.write(f"  License: {model.get('license_name', 'N/A')}\n")
                f.write(f"  Modalities: {model.get('input_modalities', 'N/A')} → {model.get('output_modalities', 'N/A')}\n")
                f.write("\n")

            if len(normalized_data) > 5:
                f.write(f"... and {len(normalized_data) - 5} more models\n")

        print(f"✅ Successfully populated {len(normalized_data)} records to {json_path}")
        print(f"✅ Saved normalization report to: {txt_path}")

        # Generate detailed normalization report
        report_file = self.generate_normalization_report(production_models, normalized_data)

        # Print summary
        print("\nSummary:")
        providers = set(record['model_provider'] for record in normalized_data)
        print(f"- Total models: {len(normalized_data)}")
        print(f"- Providers: {', '.join(sorted(providers))}")
        print(f"- Models with modalities: {sum(1 for r in normalized_data if r['input_modalities'])}")
        print(f"- Models with rate limits: {sum(1 for r in normalized_data if r['rate_limits'])}")
        print(f"- Normalization report: {report_file}")

        return normalized_data


# Convenience functions for backward compatibility
def populate_normalized_data() -> List[Dict[str, Any]]:
    """Populate normalized data using the modular processor"""
    processor = GroqDataProcessor()
    return processor.populate_normalized_data()


def clean_model_name(model_id: str, standardization_rules: Dict[str, Any]) -> str:
    """Clean model name using the modular processor"""
    processor = GroqDataProcessor()
    return processor.clean_model_name(model_id, standardization_rules)


def get_modalities(model_id: str, modalities_data: Dict[str, Any]) -> Tuple[str, str]:
    """Get modalities using the modular processor"""
    processor = GroqDataProcessor()
    return processor.get_modalities(model_id, modalities_data)


if __name__ == "__main__":
    # Test the data processor
    print("=== Groq Data Processor Test ===")

    processor = GroqDataProcessor()

    # Test configuration loading
    print("\nTesting configuration loading...")
    special_rules = processor.load_special_model_rules()
    print(f"Special model rules loaded: {len(special_rules)}")

    modality_mappings, ordering = processor.load_modality_standardization()
    print(f"Modality mappings loaded: {len(modality_mappings)}")

    # Test model name cleaning
    print("\nTesting model name cleaning...")
    test_model = "meta-llama/llama-3.1-8b-instant"
    standardization = {"remove_patterns": ["-instant"], "replace_patterns": {"-": " ", "/": " "}}
    cleaned = processor.clean_model_name(test_model, standardization)
    print(f"Cleaned name: {test_model} → {cleaned}")

    # Test modality processing
    print("\nTesting modality processing...")
    test_modalities = ['text', 'audio']
    standardized = processor.standardize_modalities(test_modalities, {"text": "Text", "audio": "Audio"})
    print(f"Standardized modalities: {test_modalities} → {standardized}")

    print("\n✓ Data processor test completed")