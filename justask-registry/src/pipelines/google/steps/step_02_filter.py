#!/usr/bin/env python3
"""
Google Models Filter Script
Filters 01_fetched_models.json through criteria in configs and outputs filtered models.
"""

import json
import re
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Set

# Add project root to path for imports
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

class GoogleModelsFilter:
    def __init__(self):
        self.filtering_config = {}
        self.filtered_models = []
        self.excluded_models = []
        
    def load_filtering_config(self) -> Dict[str, Any]:
        """Load filtering configuration from configs"""
        config_file = CONFIG_DIR / "filtering_rules.json"
        try:
            with open(config_file, 'r') as f:
                self.filtering_config = json.load(f)
                print(f"✅ Loaded filtering configuration from {config_file.name}")
                return self.filtering_config
        except FileNotFoundError:
            print(f"❌ {config_file.name} not found at {config_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {config_file.name}: {e}")
            return {}

    def load_input_models(self) -> List[Dict[str, Any]]:
        """Load models from 01_fetched_models.json"""
        input_file = get_input_file_path('01_fetched_models.json')
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)

                # Handle new JSON structure with metadata
                if isinstance(data, dict) and 'models' in data:
                    models = data['models']
                    print(f"✅ Loaded {len(models)} models from 01_fetched_models.json (with metadata)")
                elif isinstance(data, list):
                    models = data
                    print(f"✅ Loaded {len(models)} models from 01_fetched_models.json (legacy format)")
                else:
                    print(f"⚠️ Unexpected JSON structure in 01_fetched_models.json")
                    return []

                return models
        except FileNotFoundError:
            print(f"❌ 01_fetched_models.json not found at {input_file}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing 01_fetched_models.json: {e}")
            return []

    def should_exclude_model(self, model: Dict[str, Any]) -> tuple[bool, str]:
        """Check if model should be excluded based on filtering criteria"""
        if not self.filtering_config:
            return False, ""

        exclude_keywords = self.filtering_config.get('exclude_keywords', [])
        exclude_descriptions = self.filtering_config.get('exclude_descriptions', [])
        exclude_specific_models = self.filtering_config.get('exclude_specific_models', [])
        exclude_reasons = self.filtering_config.get('exclude_reasons', {})

        # Check model name, displayName, and description for exclusion keywords
        model_name = model.get('name', '').lower()
        display_name = model.get('displayName', '').lower()
        description = model.get('description', '').lower()

        # Check for specific model exclusions first
        for specific_model in exclude_specific_models:
            if model.get('name', '') == specific_model.get('name', ''):
                return True, specific_model.get('reason', 'Specifically excluded model')

        # Check for keyword exclusions in name, display name, and description
        for keyword in exclude_keywords:
            keyword_lower = keyword.lower()
            # Use word boundaries and exclude "non-keyword" patterns
            import re

            # Check if keyword appears but not as "non-keyword"
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            non_pattern = r'\bnon-' + re.escape(keyword_lower) + r'\b'

            for text in [model_name, display_name, description]:
                if re.search(pattern, text) and not re.search(non_pattern, text):
                    reason = exclude_reasons.get(keyword, f"Contains excluded keyword: {keyword}")
                    return True, reason

        # Check for description-based exclusions
        for exclude_desc in exclude_descriptions:
            if exclude_desc in description:
                reason = exclude_reasons.get('billing_required', 'Model requires billing/payment - free models only')
                return True, reason

        return False, ""

    def should_include_model(self, model: Dict[str, Any]) -> tuple[bool, str]:
        """Check if model matches include patterns"""
        if not self.filtering_config:
            return True, "No filtering config - include all"
            
        include_patterns = self.filtering_config.get('include_patterns', {})
        include_descriptions = self.filtering_config.get('include_descriptions', {})
        
        model_name = model.get('name', '').lower()
        display_name = model.get('displayName', '').lower()
        description = model.get('description', '').lower()
        
        # Check all include pattern categories
        for category, patterns in include_patterns.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if (pattern_lower in model_name or 
                    pattern_lower in display_name or 
                    pattern_lower in description):
                    reason = include_descriptions.get(category, f"Matches pattern: {pattern}")
                    return True, reason
                    
        # If model doesn't match any specific patterns, include it (general models)
        return True, "General model - no exclusions apply"

    def filter_models(self, models: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Filter models based on configuration criteria"""
        filtered_models = []
        excluded_models = []
        
        print(f"\n=== Filtering {len(models)} models ===")
        
        for model in models:
            model_name = model.get('name', 'Unknown')
            display_name = model.get('displayName', 'Unknown')
            
            # First check exclusions
            should_exclude, exclude_reason = self.should_exclude_model(model)
            if should_exclude:
                excluded_info = {
                    'model': model,
                    'reason': exclude_reason,
                    'excluded_by': 'exclude_keywords'
                }
                excluded_models.append(excluded_info)
                print(f"❌ Excluded: {display_name} ({model_name}) - {exclude_reason}")
                continue
            
            # Then check inclusions
            should_include, include_reason = self.should_include_model(model)
            if should_include:
                filtered_info = {
                    'model': model,
                    'reason': include_reason,
                    'included_by': 'include_patterns'
                }
                filtered_models.append(filtered_info)
                print(f"✅ Included: {display_name} ({model_name}) - {include_reason}")
            else:
                excluded_info = {
                    'model': model,
                    'reason': "Does not match any include patterns",
                    'excluded_by': 'include_patterns'
                }
                excluded_models.append(excluded_info)
                print(f"❌ Excluded: {display_name} ({model_name}) - Does not match include patterns")
        
        return filtered_models, excluded_models

    def save_filtered_models(self, filtered_models: List[Dict[str, Any]]) -> None:
        """Save filtered models to 02_filtered_models.json"""
        # Extract just the model data without filtering metadata
        models_data = [item['model'] for item in filtered_models]

        # Create JSON output with metadata (similar to A script)
        json_output = {
            "metadata": {
                "generated": get_ist_timestamp(),
                "total_models": len(models_data),
                "filtering_source": "Google Pipeline B-Filter"
            },
            "models": models_data
        }

        output_file = get_output_file_path('02_filtered_models.json')
        try:
            with open(output_file, 'w') as f:
                json.dump(json_output, f, indent=2)
            print(f"\n✅ Saved {len(models_data)} filtered models to 02_filtered_models.json")
        except Exception as e:
            print(f"❌ Error saving filtered models: {e}")

    def generate_filtering_report(self, filtered_models: List[Dict[str, Any]], excluded_models: List[Dict[str, Any]]) -> None:
        """Generate summary report of filtering results"""
        print(f"\n=== Filtering Summary ===")
        print(f"Total Input Models: {len(filtered_models) + len(excluded_models)}")
        print(f"Models Included: {len(filtered_models)}")
        print(f"Models Excluded: {len(excluded_models)}")
        print(f"Filtering Success Rate: {len(filtered_models)/(len(filtered_models) + len(excluded_models))*100:.1f}%")
        
        if excluded_models:
            print(f"\n=== Exclusion Breakdown ===")
            exclusion_reasons = {}
            for excluded in excluded_models:
                reason = excluded['reason']
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            
            for reason, count in sorted(exclusion_reasons.items()):
                print(f"  {count} models: {reason}")

    def save_txt_report(self, filtered_models: List[Dict[str, Any]], excluded_models: List[Dict[str, Any]]) -> None:
        """Save detailed filtering report to txt file"""
        report_content = []
        
        # Header
        report_content.append("=== GOOGLE MODELS FILTERING REPORT ===")
        report_content.append(f"Generated: {get_ist_timestamp()}")
        report_content.append("")
        
        # Summary
        total_models = len(filtered_models) + len(excluded_models)
        report_content.append("=== SUMMARY ===")
        report_content.append(f"Total Input Models: {total_models}")
        report_content.append(f"Models Included: {len(filtered_models)}")
        report_content.append(f"Models Excluded: {len(excluded_models)}")
        report_content.append(f"Filtering Success Rate: {len(filtered_models)/total_models*100:.1f}%")
        report_content.append("")
        
        # Excluded Models (First)
        report_content.append("=== EXCLUDED MODELS ===")
        if excluded_models:
            for i, item in enumerate(excluded_models, 1):
                model = item['model']
                model_name = model.get('name', 'Unknown')
                # Extract just the model ID part after "models/"
                if model_name.startswith('models/'):
                    model_name = model_name[7:]  # Remove "models/" prefix
                report_content.append(f"{i:2d}. {model_name}")
        else:
            report_content.append("No models excluded.")
        report_content.append("")
        
        # Filtered Models (Included) - Second
        report_content.append("=== INCLUDED MODELS ===")
        if filtered_models:
            for i, item in enumerate(filtered_models, 1):
                model = item['model']
                model_name = model.get('name', 'Unknown')
                # Extract just the model ID part after "models/"
                if model_name.startswith('models/'):
                    model_name = model_name[7:]  # Remove "models/" prefix
                report_content.append(f"{i:2d}. {model_name}")
        else:
            report_content.append("No models included.")
        report_content.append("")
        
        # Exclusion Breakdown
        if excluded_models:
            report_content.append("=== EXCLUSION BREAKDOWN ===")
            exclusion_reasons = {}
            for excluded in excluded_models:
                reason = excluded['reason']
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            
            for reason, count in sorted(exclusion_reasons.items()):
                report_content.append(f"{count:2d} models: {reason}")
        
        # Write to file
        report_file = get_output_file_path('02_filtered_models_report.txt')
        try:
            with open(report_file, 'w') as f:
                f.write('\n'.join(report_content))
            print(f"\n✅ Detailed filtering report saved to: 02_filtered_models_report.txt")
        except Exception as e:
            print(f"❌ Error saving filtering report: {e}")

    def run_filtering_pipeline(self) -> None:
        """Run the complete filtering pipeline"""
        print("=== Google Models Filtering Pipeline ===")
        
        # Load configuration
        config = self.load_filtering_config()
        if not config:
            print("⚠️ No filtering configuration found - proceeding with basic filtering")
            # Use default minimal config to allow processing to continue
            config = {"exclude_keywords": [], "include_patterns": {}}
        
        # Load input models
        models = self.load_input_models()
        if not models:
            print("⚠️ No input models found - generating empty output files")
            # Generate empty output files to maintain pipeline consistency
            self.save_filtered_models([])
            self.save_txt_report([], [])
            return
        
        # Apply filters
        filtered_models, excluded_models = self.filter_models(models)
        
        # Save results
        self.save_filtered_models(filtered_models)
        
        # Generate reports
        self.generate_filtering_report(filtered_models, excluded_models)
        self.save_txt_report(filtered_models, excluded_models)
        
        # Store results for potential further processing
        self.filtered_models = filtered_models
        self.excluded_models = excluded_models

if __name__ == "__main__":
    filter_processor = GoogleModelsFilter()
    filter_processor.run_filtering_pipeline()