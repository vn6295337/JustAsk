#!/usr/bin/env python3
"""
Groq Pipeline Configuration Manager
==================================

Centralized configuration management for the Groq pipeline following
OpenRouter/Google pipeline patterns.

Features:
- JSON-based configuration loading from 03_configs/
- Centralized API endpoint management
- License mapping coordination
- Error handling with fallback defaults
- Consistent path resolution

Author: AI Models Discovery Pipeline
Version: 1.0
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class GroqConfig:
    """Centralized configuration manager for Groq pipeline"""

    def __init__(self):
        """Initialize configuration manager with base paths"""
        # Project root is 3 levels up from src/utils/config_manager.py
        self.project_root = Path(__file__).parent.parent.parent
        # Configs are now in config/groq/
        self.configs_dir = self.project_root / "config" / "groq"
        self.outputs_dir = self.project_root / "outputs" / "groq"
        # Scripts are now in src/pipelines/groq/
        self.scripts_dir = self.project_root / "src" / "pipelines" / "groq" / "steps"

        # Cache for loaded configurations
        self._config_cache = {}

        # Ensure directories exist
        self.configs_dir.mkdir(exist_ok=True)
        self.outputs_dir.mkdir(exist_ok=True)

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load configuration from 03_configs/{config_name}.json

        Args:
            config_name: Name of config file (without .json extension)

        Returns:
            Dictionary containing configuration data
        """
        # Check cache first
        if config_name in self._config_cache:
            return self._config_cache[config_name]

        config_file = self.configs_dir / f"{config_name}.json"

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Cache the loaded config
            self._config_cache[config_name] = config_data
            return config_data

        except FileNotFoundError:
            # Silently return empty dict - callers use built-in defaults
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing configuration {config_name}: {e}")
            return {}

    def get_api_endpoints(self) -> Dict[str, str]:
        """
        Get Groq API endpoints and URLs

        Returns:
            Dictionary containing all API endpoints and documentation URLs
        """
        config = self.load_config("01_groq_api_endpoints")

        # Default endpoints if config file doesn't exist
        default_endpoints = {
            "base_url": "https://console.groq.com/docs",
            "production_models": "https://console.groq.com/docs/models#production-models",
            "production_systems": "https://console.groq.com/docs/models#production-systems",
            "rate_limits": "https://console.groq.com/docs/rate-limits",
            "model_details_template": "https://console.groq.com/docs/model/{model_id}"
        }

        endpoints = config.get("base_urls", default_endpoints)
        return endpoints

    def get_timeouts(self) -> Dict[str, int]:
        """
        Get timeout configurations for web scraping

        Returns:
            Dictionary containing timeout values in seconds
        """
        config = self.load_config("01_groq_api_endpoints")

        # Default timeouts
        default_timeouts = {
            "page_load": 15,
            "element_wait": 10,
            "request_timeout": 30,
            "selenium_implicit": 5,
            "retry_delay": 3
        }

        timeouts = config.get("timeouts", default_timeouts)
        return timeouts

    def get_chrome_options(self) -> List[str]:
        """
        Get Chrome driver options for web scraping

        Returns:
            List of Chrome command line options
        """
        config = self.load_config("01_groq_api_endpoints")

        # Default Chrome options
        default_options = [
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--allow-running-insecure-content',
            '--window-size=1920,1080',
            '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        chrome_options = config.get("chrome_options", default_options)
        return chrome_options

    def get_license_mappings(self) -> Dict[str, Any]:
        """
        Get centralized license mapping configuration

        Returns:
            Dictionary containing license patterns and mappings
        """
        # Load multiple license-related configs
        google_licenses = self.load_config("07_google_models_licenses")
        opensource_urls = self.load_config("05_opensource_license_urls")
        license_standardization = self.load_config("06_license_name_standardization")

        return {
            "google_models": google_licenses.get("google_models", {}),
            "opensource_licenses": opensource_urls.get("opensource_licenses", []),
            "standardization": license_standardization.get("license_name_standardization", {})
        }

    def get_provider_mappings(self) -> Dict[str, Any]:
        """
        Get provider information and mappings

        Returns:
            Dictionary containing provider country mappings and URLs
        """
        config = self.load_config("01_provider_mappings")

        # Default Groq provider info
        default_mappings = {
            "provider_mappings": {
                "groq": ["Groq", "United States"]
            },
            "official_urls": {
                "Groq": "https://groq.com/"
            },
            "model_name_standardization": {
                "remove_patterns": ["-instant", "-preview"],
                "replace_patterns": {
                    "_": " ",
                    "-": " "
                }
            }
        }

        return config if config else default_mappings

    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get database schema configuration

        Returns:
            Dictionary containing field definitions and validation rules
        """
        config = self.load_config("03_database_schema")

        # Default schema
        default_schema = {
            "required_fields": [
                "id", "inference_provider", "model_provider", "human_readable_name",
                "model_provider_country", "official_url", "input_modalities",
                "output_modalities", "license_info_text", "license_info_url",
                "license_name", "license_url", "rate_limits", "provider_api_access",
                "created_at", "updated_at"
            ],
            "field_types": {
                "id": "integer",
                "inference_provider": "string",
                "model_provider": "string",
                "human_readable_name": "string",
                "created_at": "datetime",
                "updated_at": "datetime"
            }
        }

        return config if config else default_schema

    def get_modality_standardization(self) -> Dict[str, Any]:
        """
        Get input/output modality standardization rules

        Returns:
            Dictionary containing modality mappings and ordering
        """
        config = self.load_config("08_modality_standardization")

        # Default modality settings
        default_modalities = {
            "modality_mappings": {
                "text": "Text",
                "audio": "Audio",
                "image": "Image",
                "video": "Video"
            },
            "ordering_priority": {
                "Text": 1,
                "Image": 2,
                "Audio": 3,
                "Video": 4
            }
        }

        return config if config else default_modalities

    def get_timestamp_patterns(self) -> Dict[str, str]:
        """
        Get timestamp formatting patterns

        Returns:
            Dictionary containing timestamp format templates
        """
        config = self.load_config("09_timestamp_patterns")

        # Default timestamp patterns
        default_patterns = {
            "iso_format": "%Y-%m-%dT%H:%M:%S+00:00",
            "display_format": "%Y-%m-%d %H:%M:%S",
            "filename_format": "%Y%m%d_%H%M%S"
        }

        return config if config else default_patterns

    def get_special_model_rules(self) -> Dict[str, str]:
        """
        Get special model name conversion rules

        Returns:
            Dictionary mapping model IDs to human-readable names
        """
        config = self.load_config("04_special_model_rules")
        return config.get("special_name_conversions", {})

    def reload_config(self, config_name: str) -> Dict[str, Any]:
        """
        Reload a specific configuration from disk (clears cache)

        Args:
            config_name: Name of config to reload

        Returns:
            Reloaded configuration data
        """
        # Clear from cache
        if config_name in self._config_cache:
            del self._config_cache[config_name]

        # Load fresh from disk
        return self.load_config(config_name)

    def clear_cache(self):
        """Clear all cached configurations"""
        self._config_cache.clear()
        print("✓ Configuration cache cleared")

    def validate_config(self, config_name: str) -> bool:
        """
        Validate that a configuration file exists and is valid JSON

        Args:
            config_name: Name of config file to validate

        Returns:
            True if valid, False otherwise
        """
        config_file = self.configs_dir / f"{config_name}.json"

        if not config_file.exists():
            print(f"❌ Config file missing: {config_file}")
            return False

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"✓ Config file valid: {config_name}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Config file invalid JSON: {config_name} - {e}")
            return False

    def list_available_configs(self) -> List[str]:
        """
        List all available configuration files

        Returns:
            List of config file names (without .json extension)
        """
        config_files = []
        for file_path in self.configs_dir.glob("*.json"):
            config_files.append(file_path.stem)

        return sorted(config_files)

    def get_config_info(self) -> Dict[str, Any]:
        """
        Get information about the configuration system

        Returns:
            Dictionary with configuration system metadata
        """
        available_configs = self.list_available_configs()

        return {
            "config_directory": str(self.configs_dir),
            "available_configs": available_configs,
            "cached_configs": list(self._config_cache.keys()),
            "config_count": len(available_configs)
        }


# Global configuration instance for easy access
groq_config = GroqConfig()


def get_config() -> GroqConfig:
    """
    Get global configuration instance

    Returns:
        Global GroqConfig instance
    """
    return groq_config


if __name__ == "__main__":
    # Test configuration loading
    config = GroqConfig()

    print("=== Groq Configuration Manager Test ===")
    print(f"Config directory: {config.configs_dir}")
    print(f"Available configs: {config.list_available_configs()}")
    print("\nTesting configuration loading:")

    # Test each config type
    endpoints = config.get_api_endpoints()
    print(f"API endpoints loaded: {len(endpoints)} endpoints")

    timeouts = config.get_timeouts()
    print(f"Timeouts loaded: {timeouts}")

    chrome_opts = config.get_chrome_options()
    print(f"Chrome options loaded: {len(chrome_opts)} options")

    print("\n✓ Configuration manager test completed")