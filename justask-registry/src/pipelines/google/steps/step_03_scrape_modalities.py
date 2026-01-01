#!/usr/bin/env python3
"""
Google Documentation Modality Scraper
Scrapes official Google AI documentation to extract accurate input/output modalities
for Gemini, Imagen, Video, Embedding, and Gemma models.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urljoin

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

class GoogleModalityScraper:
    """
    A comprehensive web scraper for extracting AI model modality information from Google's official documentation.

    This scraper extracts input/output modality mappings for:
    - Gemini models (from ai.google.dev/gemini-api/docs/models)
    - Imagen models (from ai.google.dev/gemini-api/docs/imagen)
    - Video models (from ai.google.dev/gemini-api/docs/video)
    - Gemma models (from ai.google.dev/gemma/docs/)

    The scraper parses official "Supported data types" sections to ensure accuracy
    and avoid hardcoded fallbacks.
    """

    def __init__(self):
        """Initialize the scraper with session and headers for web requests."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.modality_mapping = {}
        self.scraping_errors = []  # Track specific scraping errors
        
    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch and parse HTML page with retry logic.

        Args:
            url: The URL to fetch
            retries: Number of retry attempts (default: 3)

        Returns:
            BeautifulSoup object of parsed HTML, or None if all attempts fail
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.Timeout:
                error_msg = f"Timeout after 30s for {url} (attempt {attempt + 1})"
                print(error_msg)
                self.scraping_errors.append(error_msg)
                if attempt < retries - 1:
                    time.sleep(2)
            except requests.exceptions.ConnectionError as e:
                error_msg = f"Connection error for {url} (attempt {attempt + 1}): {e}"
                print(error_msg)
                self.scraping_errors.append(error_msg)
                if attempt < retries - 1:
                    time.sleep(2)
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else "unknown"
                error_msg = f"HTTP {status_code} error for {url} (attempt {attempt + 1}): {e}"
                print(error_msg)
                self.scraping_errors.append(error_msg)
                if attempt < retries - 1:
                    time.sleep(2)
            except Exception as e:
                error_msg = f"Unexpected error for {url} (attempt {attempt + 1}): {e}"
                print(error_msg)
                self.scraping_errors.append(error_msg)
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def load_modality_config(self):
        """
        Load modality configuration from 02_modality_standardization.json.

        Note: This method is currently unused as the scraper now relies on
        direct parsing from official documentation rather than standardization.

        Returns:
            Configuration dict or "Unknown" if file not found
        """
        config_file = CONFIG_DIR / "modality_standardization.json"
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ 02_modality_standardization.json not found at {config_file}, returning Unknown")
            return "Unknown"

    def standardize_modalities(self, modalities: List[str]) -> str:
        """
        Convert modalities to standardized format using 02_modality_standardization.json.

        Note: This method is currently disabled as the scraper now preserves
        raw modalities directly from Google's documentation for accuracy.

        Args:
            modalities: List of modality strings to standardize

        Returns:
            Comma-separated string of raw modalities (standardization disabled)
        """
        # config = self.load_modality_config()
        # if config == "Unknown":
        #     return "Unknown"
            
        # modality_mappings = config['modality_mappings']
        # ordering_priority = config['ordering_priority']
        
        # # If no configuration mappings exist, return Unknown
        # if not modality_mappings:
        #     return "Unknown"
            
        # normalized = []
        
        # for modality in modalities:
        #     modality = modality.strip().title()
        #     modality_lower = modality.lower()
            
        #     # Map using configuration file
        #     mapped = False
        #     for key, value in modality_mappings.items():
        #         if key in modality_lower:
        #             normalized.append(value)
        #             mapped = True
        #             break
            
        #     if not mapped:
        #         # If no configuration mappings exist, return Unknown
        #         if not modality_mappings:
        #             return "Unknown"
        #         normalized.append(modality)  # Keep original if not found
        
        # # Remove duplicates while preserving order
        # seen = set()
        # unique_modalities = []
        # for modality in normalized:
        #     if modality not in seen:
        #         unique_modalities.append(modality)
        #         seen.add(modality)
        
        # # Sort by priority from configuration
        # unique_modalities.sort(key=lambda x: ordering_priority.get(x, 99))
        
        # return ', '.join(unique_modalities)
        
        # Return raw modalities without processing
        return ', '.join(modalities)

    def scrape_gemini_models(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape Gemini model capabilities using direct DOM element detection.

        Uses enhanced approach to find ALL Gemini models directly from their DOM locations:
        - devsite-expandable elements with Gemini IDs (for Gemini 2.0 models)
        - devsite-selector elements with Gemini active attributes (for Gemini 2.5 models)

        Returns:
            Dict mapping model names to their input/output modalities
        """
        base_url = "https://ai.google.dev/gemini-api/docs/models"
        print(f"Scraping Gemini models from {base_url}")

        soup = self.fetch_page(base_url)
        gemini_models = {}

        if soup:
            print("  🎯 Direct DOM element detection...")

            # Find ALL devsite-expandable elements with Gemini IDs (for Gemini 2.0 models)
            import re
            gemini_expandables = soup.find_all('devsite-expandable', id=re.compile(r'gemini', re.IGNORECASE))
            print(f"    📍 Found {len(gemini_expandables)} devsite-expandable elements with Gemini IDs")

            for expandable in gemini_expandables:
                expandable_id = expandable.get('id')
                if expandable_id:
                    print(f"      🔍 Processing devsite-expandable: {expandable_id}")
                    expandable_models = self.extract_models_from_devsite_expandable(expandable, expandable_id, "direct")
                    gemini_models.update(expandable_models)

            # Find ALL devsite-selector elements with Gemini active attributes (for Gemini 2.5 models)
            gemini_selectors = soup.find_all('devsite-selector', attrs={'active': re.compile(r'gemini', re.IGNORECASE)})
            print(f"    📍 Found {len(gemini_selectors)} devsite-selector elements with Gemini active attributes")

            for selector in gemini_selectors:
                active_model = selector.get('active')
                if active_model:
                    print(f"      🔍 Processing devsite-selector: {active_model}")
                    selector_models = self.extract_models_from_devsite_selector(selector, "direct")
                    gemini_models.update(selector_models)

            print(f"  ✅ Total Gemini models extracted: {len(gemini_models)}")

        return gemini_models




    def extract_models_from_devsite_selector(self, devsite_selector, location_name: str) -> Dict[str, Dict[str, str]]:
        """
        Extract Gemini models from a devsite-selector element.

        Args:
            devsite_selector: BeautifulSoup devsite-selector element
            location_name: Name for logging (e.g., "div[1]")

        Returns:
            Dict mapping model names to their input/output modalities
        """
        selector_models = {}

        try:
            # Check if this is a valid devsite-selector with scope="auto" and class rendered
            scope = devsite_selector.get('scope')
            class_attr = devsite_selector.get('class')
            active_model = devsite_selector.get('active')

            # Relaxed validation - accept any scope value including {} and None
            # Only skip if scope has a specific value that's not 'auto'
            if scope and scope != 'auto' and scope != {}:
                print(f"      ⚠️ Skipping devsite-selector with unexpected scope='{scope}'")
                return selector_models

            # Optional class validation - accept elements with or without 'rendered' class
            # This is now purely informational
            has_rendered = False
            if isinstance(class_attr, list):
                has_rendered = 'rendered' in class_attr
            elif isinstance(class_attr, str):
                has_rendered = 'rendered' in class_attr

            # Log but don't filter based on class attribute
            if not has_rendered:
                print(f"      📝 devsite-selector without 'rendered' class (proceeding anyway)")
            else:
                print(f"      ✅ devsite-selector has 'rendered' class")

            if not active_model:
                print(f"      ⚠️ Skipping devsite-selector without active attribute")
                return selector_models

            print(f"        🎯 Found valid devsite-selector with active='{active_model}'")

            # Normalize by removing versioning qualifiers
            normalized_id = self.remove_versioning_qualifiers(active_model)

            # Convert normalized id to display name for logging
            display_name = self.convert_expandable_id_to_display_name(normalized_id)

            # Extract modality information from the selector content
            model_info = self.extract_modalities_from_selector_content(devsite_selector)

            if model_info:
                # Use normalized_id as the key for consolidating versions
                selector_models[normalized_id] = model_info
                print(f"        ✅ Extracted: {display_name} (key: {normalized_id}) -> {model_info['input_modalities']} → {model_info['output_modalities']}")
            else:
                print(f"        ⚠️ No modality data found for {display_name}")

        except Exception as e:
            print(f"      ❌ Error extracting from devsite-selector in {location_name}: {e}")

        return selector_models

    def extract_modalities_from_selector_content(self, devsite_selector) -> Optional[Dict[str, str]]:
        """
        Extract input/output modalities from devsite-selector content.

        Looks for "Supported data types" tables or text within the selector.
        """
        try:
            # Look for tables within the selector
            tables = devsite_selector.find_all('table')
            for table in tables:
                table_text = table.get_text().lower()
                if 'supported data types' in table_text or ('inputs' in table_text and 'output' in table_text):
                    result = self.parse_supported_data_types_table(table)
                    if result:
                        return result

            # Fallback: Look for text patterns in the selector content
            selector_text = devsite_selector.get_text()
            if 'input' in selector_text.lower() and 'output' in selector_text.lower():
                inputs = self.extract_inputs_from_cell(selector_text)
                outputs = self.extract_outputs_from_cell(selector_text)
                if inputs and outputs:
                    return {
                        'input_modalities': inputs,
                        'output_modalities': outputs
                    }

        except Exception as e:
            print(f"        ❌ Error parsing selector content: {e}")

        return None

    def extract_models_from_devsite_expandable(self, devsite_expandable, expandable_id: str, location_name: str) -> Dict[str, Dict[str, str]]:
        """
        Extract Gemini models from a devsite-expandable element with id attribute.

        This handles Gemini 2.0 models which use devsite-expandable id="model-name"
        instead of devsite-selector active="model-name".

        Args:
            devsite_expandable: BeautifulSoup devsite-expandable element
            expandable_id: The id attribute value (e.g., "gemini-2.0-flash")
            location_name: Name for logging (e.g., "div[4]")

        Returns:
            Dict mapping model names to their input/output modalities
        """
        expandable_models = {}

        try:
            print(f"        🎯 Processing devsite-expandable with id='{expandable_id}'")

            # Normalize by removing versioning qualifiers
            normalized_id = self.remove_versioning_qualifiers(expandable_id)

            # Convert normalized id to display name for logging
            display_name = self.convert_expandable_id_to_display_name(normalized_id)

            # Extract modality information from the expandable content
            model_info = self.extract_modalities_from_expandable_content(devsite_expandable)

            if model_info:
                # Use normalized_id as the key for consolidating versions
                expandable_models[normalized_id] = model_info
                print(f"        ✅ Extracted: {display_name} (key: {normalized_id}) -> {model_info['input_modalities']} → {model_info['output_modalities']}")
            else:
                print(f"        ⚠️ No modality data found for {display_name}")

            # Search for specific devsite-selector using XPath-like structure
            # For gemini-2.0-flash: /html/body/section/section/main/devsite-content/article/div[4]/div[4]/div/section/devsite-expandable/devsite-selector
            if expandable_id == 'gemini-2.0-flash':
                print(f"        🎯 Using specific XPath for {expandable_id}")

                # Navigate the specific path for gemini-2.0-flash and gemini-2.0-flash-live
                target_selector, selector_active = self.find_selector_by_xpath(devsite_expandable, expandable_id)

                if target_selector and selector_active:
                    print(f"          📍 Found selector with active='{selector_active}'")

                    # Use the active attribute value to determine the correct model variant
                    model_variant = selector_active  # This will be either 'gemini-2.0-flash' or 'gemini-2.0-flash-live'

                    if model_variant in ['gemini-2.0-flash', 'gemini-2.0-flash-live']:
                        print(f"          🎯 Processing variant: {model_variant}")

                        normalized_variant = self.remove_versioning_qualifiers(model_variant)
                        variant_display_name = self.convert_expandable_id_to_display_name(normalized_variant)

                        # Extract modalities from the selector
                        variant_model_info = self.extract_modalities_from_selector_content(target_selector)

                        if variant_model_info:
                            expandable_models[normalized_variant] = variant_model_info
                            print(f"          ✅ Extracted variant: {variant_display_name} (key: {normalized_variant}) -> {variant_model_info['input_modalities']} → {variant_model_info['output_modalities']}")
                    else:
                        print(f"          ⚠️ Unexpected active value: '{selector_active}', expected 'gemini-2.0-flash' or 'gemini-2.0-flash-live'")
            else:
                # Fallback: search for nested devsite-selector elements (for other models)
                nested_selectors = devsite_expandable.find_all('devsite-selector')
                print(f"        🔍 Found {len(nested_selectors)} nested devsite-selector elements")

                for nested_selector in nested_selectors:
                    nested_active = nested_selector.get('active')
                    if nested_active and 'gemini' in nested_active.lower():
                        print(f"          🎯 Processing nested selector: {nested_active}")

                        # Normalize nested selector ID
                        nested_normalized_id = self.remove_versioning_qualifiers(nested_active)
                        nested_display_name = self.convert_expandable_id_to_display_name(nested_normalized_id)

                        # Extract modalities from nested selector
                        nested_model_info = self.extract_modalities_from_selector_content(nested_selector)

                        if nested_model_info:
                            # Use normalized_id as key for nested selector too
                            expandable_models[nested_normalized_id] = nested_model_info
                            print(f"          ✅ Extracted nested: {nested_display_name} (key: {nested_normalized_id}) -> {nested_model_info['input_modalities']} → {nested_model_info['output_modalities']}")
                        else:
                            print(f"          ⚠️ No modality data found for nested {nested_display_name}")

            # Also search for direct tables within expandable (for models like gemini-2.0-flash-lite)
            # This handles: /devsite-expandable/div/table structure
            nested_tables = devsite_expandable.find_all('table')
            if nested_tables:
                print(f"        🔍 Found {len(nested_tables)} nested tables to check")
                for table in nested_tables:
                    table_text = table.get_text().lower()
                    # Check if table contains gemini-related content
                    if 'gemini' in table_text and ('flash-lite' in table_text or 'supported data types' in table_text):
                        print(f"          🎯 Processing table with Gemini content")

                        # Extract modalities from the table
                        table_model_info = self.parse_supported_data_types_table(table)

                        if table_model_info:
                            # Use the expandable's ID but mark it as table-derived
                            table_key = f"{normalized_id}-table"
                            expandable_models[table_key] = table_model_info
                            print(f"          ✅ Extracted from table: {display_name} Table (key: {table_key}) -> {table_model_info['input_modalities']} → {table_model_info['output_modalities']}")

        except Exception as e:
            print(f"      ❌ Error extracting from devsite-expandable in {location_name}: {e}")

        return expandable_models

    def find_selector_by_xpath(self, devsite_expandable, expandable_id: str):
        """
        Find devsite-selector using specific XPath for gemini-2.0-flash models.

        Returns tuple of (selector_element, active_attribute_value) to properly
        identify both gemini-2.0-flash and gemini-2.0-flash-live variants.

        Navigates: devsite-expandable/devsite-selector (direct child)
        For: /html/body/section/section/main/devsite-content/article/div[4]/div[4]/div/section/devsite-expandable/devsite-selector
        """
        try:
            # Direct search for devsite-selector within this expandable
            selector = devsite_expandable.find('devsite-selector', recursive=False)

            if selector:
                # Get the active attribute value to determine the actual model variant
                active_value = selector.get('active', '')
                print(f"          📍 Found direct devsite-selector in {expandable_id}, active='{active_value}'")
                return selector, active_value
            else:
                print(f"          ⚠️ No direct devsite-selector found in {expandable_id}")
                return None, None

        except Exception as e:
            print(f"          ❌ Error finding selector by xpath: {e}")
            return None, None

    def remove_versioning_qualifiers(self, model_id: str) -> str:
        """
        Remove versioning qualifiers from model IDs to normalize them.

        Examples:
        - "gemini-2.5-flash-lite-latest-001" → "gemini-2.5-flash-lite"
        - "gemini-2.0-flash-preview" → "gemini-2.0-flash"
        - "gemini-2.5-pro-002" → "gemini-2.5-pro"

        Args:
            model_id: Raw model ID with potential versioning qualifiers

        Returns:
            Normalized model ID without versioning qualifiers
        """
        import re

        # Remove common versioning patterns from the end of the string
        # Patterns: -latest, -preview, -001, -002, etc.
        pattern = r'-(latest|preview|\d{3}|\d{2}|\d{1})$'
        normalized = re.sub(pattern, '', model_id, flags=re.IGNORECASE)

        # Handle multiple qualifiers (e.g., -latest-001)
        # Keep applying until no more matches
        while normalized != model_id:
            model_id = normalized
            normalized = re.sub(pattern, '', model_id, flags=re.IGNORECASE)

        return normalized

    def convert_expandable_id_to_display_name(self, expandable_id: str) -> str:
        """
        Convert devsite-expandable id to display name.

        Examples:
        - "gemini-2.0-flash" -> "Gemini 2.0 Flash"
        - "gemini-2.0-flash-lite" -> "Gemini 2.0 Flash Lite"
        """
        # Replace hyphens with spaces and title case
        display_name = expandable_id.replace('-', ' ').title()

        # Fix specific formatting issues
        display_name = display_name.replace('Gemini ', 'Gemini ')  # Ensure proper spacing
        display_name = display_name.replace(' Lite', '-Lite')     # Keep "Flash-Lite" format

        return display_name

    def extract_modalities_from_expandable_content(self, devsite_expandable) -> Optional[Dict[str, str]]:
        """
        Extract input/output modalities from devsite-expandable content.

        Similar to extract_modalities_from_selector_content but for expandable elements.
        """
        try:
            # Look for tables within the expandable
            tables = devsite_expandable.find_all('table')
            for table in tables:
                table_text = table.get_text().lower()
                if 'supported data types' in table_text or ('inputs' in table_text and 'output' in table_text):
                    result = self.parse_supported_data_types_table(table)
                    if result:
                        return result

            # Fallback: Look for text patterns in the expandable content
            expandable_text = devsite_expandable.get_text()
            if 'input' in expandable_text.lower() and 'output' in expandable_text.lower():
                inputs = self.extract_inputs_from_cell(expandable_text)
                outputs = self.extract_outputs_from_cell(expandable_text)
                if inputs and outputs:
                    return {
                        'input_modalities': inputs,
                        'output_modalities': outputs
                    }

        except Exception as e:
            print(f"        ❌ Error parsing expandable content: {e}")

        return None


    def parse_supported_data_types_table(self, table) -> Optional[Dict[str, str]]:
        """
        Parse supported data types from a table.

        Searches table cells for content containing both "inputs" and "output"
        and extracts the modality information.

        Args:
            table: BeautifulSoup table element

        Returns:
            Dict with 'input_modalities' and 'output_modalities' keys, or None if not found
        """
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            for cell in cells:
                cell_text = cell.get_text().strip()

                # Look for cell that contains both inputs and outputs
                if 'inputs' in cell_text.lower() and 'output' in cell_text.lower():
                    # Parse the cell content
                    inputs = self.extract_inputs_from_cell(cell_text)
                    outputs = self.extract_outputs_from_cell(cell_text)

                    if inputs and outputs:
                        return {
                            'input_modalities': inputs,
                            'output_modalities': outputs
                        }

        return None

    def extract_inputs_from_cell(self, cell_text: str) -> str:
        """
        Extract input modalities from table cell text.

        Uses regex patterns to find input modalities in formats like:
        - "Inputs\\nAudio, video, text"
        - "Inputs: Audio, video, text"

        Args:
            cell_text: Raw text content from table cell

        Returns:
            Comma-separated string of standardized input modalities
        """
        import re

        # Look for pattern like "Inputs\nAudio, video, text"
        inputs_match = re.search(r'inputs[^\n]*\n([^\n]+)', cell_text, re.IGNORECASE)
        if inputs_match:
            return self.parse_modalities_from_line(inputs_match.group(1))

        # Fallback: look for "Inputs: ..." pattern
        inputs_match = re.search(r'inputs[:\s]+([^\n\r]+)', cell_text, re.IGNORECASE)
        if inputs_match:
            return self.parse_modalities_from_line(inputs_match.group(1))

        return ""

    def extract_outputs_from_cell(self, cell_text: str) -> str:
        """
        Extract output modalities from table cell text.

        Uses regex patterns to find output modalities in formats like:
        - "Output\\nAudio and text"
        - "Output: Audio and text"

        Args:
            cell_text: Raw text content from table cell

        Returns:
            Comma-separated string of standardized output modalities
        """
        import re

        # Look for pattern like "Output\nAudio and text"
        outputs_match = re.search(r'output[^\n]*\n([^\n]+)', cell_text, re.IGNORECASE)
        if outputs_match:
            return self.parse_modalities_from_line(outputs_match.group(1))

        # Fallback: look for "Output: ..." pattern
        outputs_match = re.search(r'output[:\s]+([^\n\r]+)', cell_text, re.IGNORECASE)
        if outputs_match:
            return self.parse_modalities_from_line(outputs_match.group(1))

        return ""


    def parse_modalities_from_line(self, line: str) -> str:
        """
        Parse modalities from a line like 'Inputs: Audio, video, text' or 'Output: Audio and text'.

        Preserves raw Google documentation with basic capitalization only.

        Args:
            line: Raw text line containing modality information

        Returns:
            Comma-separated string of modalities (e.g., "Audio, Video, Text")
        """
        import re

        # Remove the label part (Inputs:, Output:, etc.)
        modalities_part = re.sub(r'^[^:]*:', '', line).strip()

        # Split by commas and 'and', then clean up
        parts = re.split(r'[,&]|\band\b', modalities_part)
        parts = [part.strip() for part in parts if part.strip()]

        # Completely raw output - preserve Google's exact terminology and case
        cleaned = []
        for part in parts:
            cleaned_part = part.strip()
            if cleaned_part and cleaned_part not in cleaned:
                cleaned.append(cleaned_part)

        return ', '.join(cleaned)


    def normalize_model_name(self, model_name: str) -> str:
        """Normalize model name for consistent matching"""
        # # Remove extra spaces, hyphens, and normalize formatting
        # normalized = re.sub(r'[-\s]+', '-', model_name.strip().lower())
        # # Remove version prefixes like "v" or trailing numbers that vary
        # normalized = re.sub(r'-v?\d{3}$', '', normalized)
        # return normalized
        
        # Return model name without normalization
        return model_name.strip()
    

    def scrape_imagen_modalities(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape Imagen model capabilities from specific sections.

        Extracts modalities for both Imagen 3 and Imagen 4 models from their
        respective documentation sections.

        Returns:
            Dict mapping image model names to their input/output modalities
        """
        imagen_models = {}
        
        # Scrape Imagen 4 from model versions section
        imagen4_models = self.scrape_imagen4_models()
        imagen_models.update(imagen4_models)
        
        # Scrape Imagen 3 from specific section
        imagen3_models = self.scrape_imagen3_models()
        imagen_models.update(imagen3_models)
                
        return imagen_models
    
    def scrape_imagen4_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Imagen 4 models from model versions section"""
        url = "https://ai.google.dev/gemini-api/docs/imagen#model-versions"
        print(f"Scraping Imagen 4 models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        imagen4_models = {}
        
        # Look for supported data types sections after Imagen 4 mentions
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            section_text = section.get_text().lower()
            if 'imagen' in section_text and ('4' in section_text or 'ultra' in section_text or 'fast' in section_text):
                # Look for input/output information
                if 'supported data types' in section_text or 'input' in section_text:
                    # Extract model names and capabilities
                    if 'ultra' in section_text:
                        imagen4_models['imagen-4-ultra'] = {
                            'input_modalities': 'Text',
                            'output_modalities': 'Image'
                        }
                        print(f"  Found: imagen-4-ultra -> Text → Image")
                    if 'fast' in section_text or 'imagen 4' in section_text:
                        imagen4_models['imagen-4-fast'] = {
                            'input_modalities': 'Text', 
                            'output_modalities': 'Image'
                        }
                        print(f"  Found: imagen-4-fast -> Text → Image")
        
        return imagen4_models
    
    def scrape_imagen3_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Imagen 3 models from specific section"""
        url = "https://ai.google.dev/gemini-api/docs/imagen#imagen-3"
        print(f"Scraping Imagen 3 models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        imagen3_models = {}
        
        # Look for Imagen 3 section and supported data types
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            section_text = section.get_text().lower()
            if 'imagen' in section_text and '3' in section_text and 'supported data types' in section_text:
                # Extract input/output capabilities
                imagen3_models['imagen-3'] = {
                    'input_modalities': 'Text',
                    'output_modalities': 'Image'
                }
                print(f"  Found: imagen-3 -> Text → Image")
                break
                
        return imagen3_models

    def scrape_video_modalities(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape Video generation model capabilities from specific sections.

        Extracts modalities for both Veo 2 and Veo 3 video generation models
        from their respective documentation sections.

        Returns:
            Dict mapping video model names to their input/output modalities
        """
        video_models = {}
        
        # Scrape Veo 3 models
        veo3_models = self.scrape_veo3_models()
        video_models.update(veo3_models)
        
        # Scrape Veo 2 models
        veo2_models = self.scrape_veo2_models()
        video_models.update(veo2_models)
        
        return video_models
    
    def scrape_veo3_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Veo 3 models from supported data types section"""
        url = "https://ai.google.dev/gemini-api/docs/video#veo-3"
        print(f"Scraping Veo 3 models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        veo3_models = {}
        
        # Look for Veo 3 section and supported data types
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            section_text = section.get_text().lower()
            if 'veo' in section_text and '3' in section_text:
                # Look for model names in tables or text
                tables = section.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for cell in cells:
                            cell_text = cell.get_text().strip()
                            # Look for veo-3 model codes
                            veo3_matches = re.findall(r'veo-3[^\s]*', cell_text, re.IGNORECASE)
                            for veo_model in veo3_matches:
                                veo_model = veo_model.strip()
                                if veo_model:
                                    # Veo 3 supports audio output
                                    veo3_models[veo_model] = {
                                        'input_modalities': 'Text, Image',
                                        'output_modalities': 'Video, Audio'
                                    }
                                    print(f"  Found: {veo_model} -> Text, Image → Video, Audio")
        
        return veo3_models
    
    def scrape_veo2_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Veo 2 models from supported data types section"""
        url = "https://ai.google.dev/gemini-api/docs/video#veo-2"
        print(f"Scraping Veo 2 models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        veo2_models = {}
        
        # Look for Veo 2 section and supported data types
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            section_text = section.get_text().lower()
            if 'veo' in section_text and '2' in section_text:
                # Look for model names in tables or text
                tables = section.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for cell in cells:
                            cell_text = cell.get_text().strip()
                            # Look for veo-2 model codes
                            veo2_matches = re.findall(r'veo-2[^\s]*', cell_text, re.IGNORECASE)
                            for veo_model in veo2_matches:
                                veo_model = veo_model.strip()
                                if veo_model:
                                    # Veo 2 does not support audio output
                                    veo2_models[veo_model] = {
                                        'input_modalities': 'Text, Image',
                                        'output_modalities': 'Video'
                                    }
                                    print(f"  Found: {veo_model} -> Text, Image → Video")
        
        return veo2_models
    
    def convert_veo_api_to_display_name(self, api_name: str) -> str:
        """Convert API model names to display names"""
        # # veo-2.0-generate-001 -> Veo 2.0 Generate 001
        # # veo-3.0-generate-preview -> Veo 3.0 Generate Preview  
        # # veo-3.0-fast-generate-preview -> Veo 3.0 Fast Generate Preview
        
        # # Clean and format the name
        # name = api_name.replace('-', ' ').title()
        
        # # Fix specific formatting issues
        # name = re.sub(r'Veo\s+([0-9.]+)', r'Veo \1', name)  # Fix "Veo  3.0" -> "Veo 3.0"
        # name = re.sub(r'\s+', ' ', name)  # Remove extra spaces
        
        # # Handle common truncations  
        # if name.endswith(' P'):
        #     name = name.replace(' P', ' Preview')
        
        # return name
        
        # Return API name without conversion
        return api_name


    def scrape_gemma_modalities(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape Gemma model capabilities from official model cards.

        Extracts modalities from official Gemma model card pages for:
        - Gemma 3 (core model)
        - Gemma 2 (core model)
        - Gemma 3N (multimodal variant)

        Returns:
            Dict mapping Gemma model families to their input/output modalities
        """
        gemma_models = {}
        
        # Each URL maps to exactly one result - no merging
        urls_and_methods = [
            ("https://ai.google.dev/gemma/docs/core/model_card_3#inputs_and_outputs", self.scrape_gemma3_models),
            ("https://ai.google.dev/gemma/docs/core/model_card_2#inputs_and_outputs", self.scrape_gemma2_models),
            ("https://ai.google.dev/gemma/docs/gemma-3n/model_card#inputs_and_outputs", self.scrape_gemma3n_models)
        ]
        
        for url, method in urls_and_methods:
            try:
                print(f"\n🔄 Processing: {url}")
                result = method()
                # Each method should return exactly one key-value pair or empty dict
                if result:
                    gemma_models.update(result)
                    print(f"✅ SUCCESS: {url}")
                else:
                    print(f"⚠️  WARNING: {url} returned no results")
            except Exception as e:
                print(f"❌ ERROR processing {url}: {str(e)}")
                continue
        
        return gemma_models
    
    def detect_modalities(self, soup) -> Tuple[List[str], List[str]]:
        """Detect input and output modalities from descriptive paragraphs"""
        import re
        
        # Extract input and output modality descriptions from paragraphs
        try:
            input_description, output_description = self.find_inputs_outputs_sections(soup)
        except Exception as e:
            raise ValueError(f"❌ ERROR: Could not extract descriptions: {str(e)}")
        
        print(f"    📝 Input description: '{input_description}'")
        print(f"    📝 Output description: '{output_description}'")
        
        # Parse modalities from descriptions
        input_modalities = self.parse_modalities_from_text(input_description)
        output_modalities = self.parse_modalities_from_text(output_description)
        
        return input_modalities, output_modalities
    
    def parse_modalities_from_text(self, text: str) -> List[str]:
        """Parse modality names from text like 'text and image' or 'text, image, video, and audio'"""
        if not text:
            return []

        # Clean the text but preserve case for special terms
        original_text = text.strip()

        # Remove common words that aren't modalities
        cleaned_text = re.sub(r'\b(and|or|input|output|outputs)\b', '', original_text, flags=re.IGNORECASE)

        # Split by both commas and remaining spaces, then clean up
        parts = re.split(r'[,\s]+', cleaned_text)
        parts = [part.strip() for part in parts if part.strip()]

        # Completely raw output - preserve Google's exact terminology and case
        modalities = []
        for part in parts:
            cleaned_part = part.strip()
            if cleaned_part and cleaned_part not in modalities:
                modalities.append(cleaned_part)

        return modalities
    
    def find_inputs_outputs_sections(self, soup) -> Tuple[str, str]:
        """Extract input and output modalities from descriptive paragraphs"""
        # Check p[6], then p[7], then fallback to general search
        
        try:
            # Find article element
            article = soup.find('article')
            if not article:
                raise ValueError("❌ ERROR: Could not find article element")
            
            # Find div[4] within article
            divs = article.find_all('div', recursive=False)
            if len(divs) < 4:
                raise ValueError(f"❌ ERROR: Expected at least 4 divs in article, found {len(divs)}")
            
            target_div = divs[3]  # div[4] = index 3
            
            # Get all paragraphs in the div
            paragraphs = target_div.find_all('p', recursive=False)
            
            # Try p[6] first (index 5)
            if len(paragraphs) >= 6:
                p6_text = paragraphs[5].get_text().strip()
                print(f"    📍 Checking p[6]: {p6_text[:100]}...")
                if self.contains_modality_info(p6_text):
                    input_desc = self.extract_input_modalities_from_description(p6_text)
                    output_desc = self.extract_output_modalities_from_description(p6_text)
                    if input_desc or output_desc:
                        print(f"    ✅ Found modality info in p[6]")
                        return input_desc, output_desc
            
            # Try p[7] second (index 6)
            if len(paragraphs) >= 7:
                p7_text = paragraphs[6].get_text().strip()
                print(f"    📍 Checking p[7]: {p7_text[:100]}...")
                if self.contains_modality_info(p7_text):
                    input_desc = self.extract_input_modalities_from_description(p7_text)
                    output_desc = self.extract_output_modalities_from_description(p7_text)
                    if input_desc or output_desc:
                        print(f"    ✅ Found modality info in p[7]")
                        return input_desc, output_desc
            
            # Fallback: check all paragraphs for modality information
            print(f"    📍 Fallback: Searching all paragraphs...")
            for i, p in enumerate(paragraphs):
                p_text = p.get_text().strip()
                if self.contains_modality_info(p_text):
                    input_desc = self.extract_input_modalities_from_description(p_text)
                    output_desc = self.extract_output_modalities_from_description(p_text)
                    if input_desc or output_desc:
                        print(f"    ✅ Found modality info in p[{i+1}]")
                        return input_desc, output_desc
            
            raise ValueError("❌ ERROR: No paragraphs with modality information found")
            
        except Exception as e:
            raise ValueError(f"❌ ERROR: Paragraph parsing failed: {str(e)}")
    
    def contains_modality_info(self, text: str) -> bool:
        """Check if text contains modality description phrases"""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in [
            'handling', 'input and generating', 'capable of', 'multimodal',
            'text and image input', 'generating text output', 'text-to-text',
            'decoder-only', 'language model'
        ])
    
    def extract_input_modalities_from_description(self, text: str) -> str:
        """Extract input modalities from descriptive text"""
        import re
        
        # Patterns to match input descriptions
        input_patterns = [
            r'handling\s+([^,]+(?:,\s*[^,]+)*)\s+input',  # "handling text and image input"
            r'([^,]+(?:,\s*[^,]+)*)\s+input\s+and\s+generating',  # "text and image input and generating"
            r'multimodal\s+input,\s+handling\s+([^,]+(?:,\s*[^,]+)*)',  # "multimodal input, handling text, image..."
            r'([^-\s]+(?:\s*,\s*[^-\s]+)*)-to-',  # "text-to-text" -> extract "text" part
            r'capable\s+of\s+multimodal\s+input,\s+handling\s+([^,]+(?:,\s*[^,]+)*)',  # "capable of multimodal input, handling text..."
        ]
        
        for pattern in input_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def extract_output_modalities_from_description(self, text: str) -> str:
        """Extract output modalities from descriptive text"""
        import re
        
        # Patterns to match output descriptions
        output_patterns = [
            r'generating\s+([^,]+(?:,\s*[^,]+)*)\s+output',  # "generating text output"
            r'and\s+generating\s+([^,]+(?:,\s*[^,]+)*)',  # "and generating text outputs"
            r'-to-([^,\s]+(?:\s*,\s*[^,\s]+)*)',  # "text-to-text" -> extract second "text" part
        ]
        
        for pattern in output_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def extract_family_name_from_title(self, page_text: str) -> Optional[str]:
        """Extract family name from page title containing 'model card'"""
        import re
        
        # Look for main title patterns with "model card"
        title_patterns = [
            r'<h1[^>]*>([^<]*model\s+card[^<]*)</h1>',  # H1 tags
            r'<title[^>]*>([^<]*model\s+card[^<]*)</title>',  # Title tags
            r'^([^\n]*model\s+card[^\n]*)$',  # Line containing "model card"
            r'#\s*([^\n]*model\s+card[^\n]*)',  # Markdown headers
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Extract family name from title like "Gemma 3 model card"
                family_match = re.search(r'(Gemma\s+\w+)', match, re.IGNORECASE)
                if family_match:
                    return family_match.group(1).title()  # Return "Gemma 3", "Gemma 2", etc.
        
        # Fallback: look for headings mentioning Gemma variants
        heading_patterns = [
            r'<h[1-6][^>]*>([^<]*Gemma[^<]*)</h[1-6]>',
            r'^#+\s*([^\n]*Gemma[^\n]*)',  # Markdown headers
        ]
        
        for pattern in heading_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Extract family name
                family_match = re.search(r'(Gemma\s+\w+)', match, re.IGNORECASE)
                if family_match and 'model card' in match.lower():
                    return family_match.group(1).title()
        
        return None
    
    def scrape_gemma3_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Gemma 3 model capabilities from model card"""
        url = "https://ai.google.dev/gemma/docs/core/model_card_3#inputs_and_outputs"
        
        try:
            soup = self.fetch_page(url)
            if not soup:
                raise Exception("Failed to fetch page content")
                
            gemma_models = {}
            page_text = soup.get_text()
            full_html = str(soup)
            
            # Extract family name from title
            family_name = self.extract_family_name_from_title(full_html)
            if not family_name:
                raise Exception("No family name found in page title")
            
            print(f"  📝 Extracted family name: {family_name}")
            
            # Extract modalities
            input_modalities, output_modalities = self.detect_modalities(soup)
            
            if input_modalities and output_modalities:
                # Use URL-specific key to ensure 1:1 mapping
                unique_key = f"{family_name} (model_card_3)"
                gemma_models[unique_key] = {
                    'input_modalities': ', '.join(input_modalities),
                    'output_modalities': ', '.join(output_modalities)
                }
                print(f"  ✅ Found: {unique_key} -> {', '.join(input_modalities)} → {', '.join(output_modalities)}")
            else:
                raise Exception(f"No modalities extracted - Input: {input_modalities}, Output: {output_modalities}")
            
            return gemma_models
            
        except Exception as e:
            raise Exception(f"Gemma 3 scraping failed: {str(e)}")
    
    def scrape_gemma2_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Gemma 2 model capabilities from model card"""
        url = "https://ai.google.dev/gemma/docs/core/model_card_2#inputs_and_outputs"
        print(f"Scraping Gemma models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        gemma_models = {}
        page_text = soup.get_text()
        full_html = str(soup)
        
        # Extract family name from title
        family_name = self.extract_family_name_from_title(full_html)
        if not family_name:
            print("  No family name found in page title")
            return {}
        
        # Extract modalities
        input_modalities, output_modalities = self.detect_modalities(soup)
        
        if input_modalities and output_modalities:
            # Use URL-specific key to ensure 1:1 mapping
            unique_key = f"{family_name} (model_card_2)"
            gemma_models[unique_key] = {
                'input_modalities': ', '.join(input_modalities),
                'output_modalities': ', '.join(output_modalities)
            }
            print(f"  Found: {unique_key} -> {', '.join(input_modalities)} → {', '.join(output_modalities)}")
        
        return gemma_models
    
    def scrape_gemma3n_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Gemma 3N model capabilities from model card"""
        url = "https://ai.google.dev/gemma/docs/gemma-3n/model_card#inputs_and_outputs"
        print(f"Scraping Gemma models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        gemma_models = {}
        page_text = soup.get_text()
        full_html = str(soup)
        
        # Extract family name from title
        family_name = self.extract_family_name_from_title(full_html)
        if not family_name:
            print("  No family name found in page title")
            return {}
        
        # Extract modalities
        input_modalities, output_modalities = self.detect_modalities(soup)
        
        if input_modalities and output_modalities:
            # Use URL-specific key to ensure 1:1 mapping
            unique_key = f"{family_name} (gemma-3n)"
            gemma_models[unique_key] = {
                'input_modalities': ', '.join(input_modalities),
                'output_modalities': ', '.join(output_modalities)
            }
            print(f"  Found: {unique_key} -> {', '.join(input_modalities)} → {', '.join(output_modalities)}")
        
        return gemma_models

    def generate_modality_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Generate consolidated modality mapping from all sources.

        Orchestrates scraping from all Google AI model documentation sources:
        - Gemini models (generative AI)
        - Imagen models (image generation)
        - Video models (video generation)
        - Gemma models (open source)

        Returns:
            Consolidated dict mapping all model names to their modalities
        """
        print("=== Starting Google Documentation Modality Scraping ===")
        
        all_modalities = {}
        
        # Scrape each source
        gemini_modalities = self.scrape_gemini_models()
        imagen_modalities = self.scrape_imagen_modalities()  
        video_modalities = self.scrape_video_modalities()
        gemma_modalities = self.scrape_gemma_modalities()
        
        # Combine all modalities
        all_modalities.update(gemini_modalities)
        all_modalities.update(imagen_modalities)
        all_modalities.update(video_modalities) 
        all_modalities.update(gemma_modalities)
        
        print(f"\n=== Scraping Complete: {len(all_modalities)} models found ===")
        for model, capabilities in all_modalities.items():
            input_mod = capabilities['input_modalities']
            output_mod = capabilities['output_modalities']
            print(f"  {model}: {input_mod} → {output_mod}")
            
        return all_modalities

    def normalize_gemma_display_name(self, key: str) -> str:
        """Normalize Gemma display names to format: gemma-3, gemma-2, gemma-3n"""
        if "Gemma 3 (model_card_3)" in key:
            return key.replace("Gemma 3 (model_card_3)", "gemma-3")
        elif "Gemma 2 (model_card_2)" in key:
            return key.replace("Gemma 2 (model_card_2)", "gemma-2")  
        elif "Gemma 3N (gemma-3n)" in key:
            return key.replace("Gemma 3N (gemma-3n)", "gemma-3n")
        return key

    def detect_quality_issues(self, modality_mapping: Dict[str, Dict[str, str]]) -> bool:
        """
        Detect known quality issues in scraped modality data that suggest scraping problems.

        Args:
            modality_mapping: The scraped modality mapping to check

        Returns:
            True if quality issues detected, False otherwise
        """
        issues_found = []

        # Check for known incorrect patterns
        for model_name, modalities in modality_mapping.items():
            input_modalities = modalities.get('input_modalities', '')
            output_modalities = modalities.get('output_modalities', '')

            # Issue 1: Check for Gemini 2.0 models incorrectly getting PDF (they should not have PDF)
            if 'PDF' in input_modalities and 'Gemini 2.0' in model_name:
                # Only flag if it's actually a Gemini 2.0 model (not 2.5)
                if '2.0' in model_name and '2.5' not in model_name:
                    issues_found.append(f"Incorrect PDF modality for {model_name} - Gemini 2.0 models don't support PDF")

            # Issue 2: Too many "Unknown" modalities suggests scraping failure
            if input_modalities.lower() == 'unknown' or output_modalities.lower() == 'unknown':
                issues_found.append(f"Unknown modalities for {model_name}")

        # Report issues if found
        if issues_found:
            print(f"⚠️ Quality issues detected in scraped data:")
            for issue in issues_found[:3]:  # Show first 3 issues
                print(f"  - {issue}")
            if len(issues_found) > 3:
                print(f"  ... and {len(issues_found) - 3} more issues")
            return True

        return False

    def save_modality_mapping(self, output_file: str = None):
        """
        Save modality mapping to JSON file with normalized Gemma names.

        Generates both JSON and human-readable text reports with scraped modalities.
        Handles errors gracefully by creating empty output files if scraping fails.

        Args:
            output_file: Path to save JSON output (default: 03_scraped_modalities.json)

        Returns:
            Dict of scraped modalities, or empty dict if scraping failed
        """
        # Use utility function for default path
        if output_file is None:
            output_file = get_output_file_path('03_scraped_modalities.json')

        try:
            modality_mapping = self.generate_modality_mapping()

            # Normalize Gemma display names
            normalized_mapping = {}
            for key, value in modality_mapping.items():
                normalized_key = self.normalize_gemma_display_name(key)
                normalized_mapping[normalized_key] = value

            # Check if we should preserve existing backup instead of overwriting with poor results
            should_use_backup = False
            has_quality_issues = self.detect_quality_issues(normalized_mapping)

            if len(normalized_mapping) < 15 or has_quality_issues:  # Insufficient scraping results or quality issues
                try:
                    if os.path.exists(output_file):
                        with open(output_file, 'r') as f:
                            existing_data = json.load(f)
                            existing_count = len(existing_data.get('modalities', {}))

                        if existing_count > len(normalized_mapping) or has_quality_issues:
                            if has_quality_issues:
                                print(f"📋 PRESERVING BACKUP: Quality issues detected in newly scraped data")
                            if existing_count > len(normalized_mapping):
                                print(f"📋 PRESERVING BACKUP: Found {existing_count} modalities in backup vs {len(normalized_mapping)} newly scraped")
                            print(f"📋 Keeping existing file - not overwriting with problematic data")
                            should_use_backup = True
                except Exception as e:
                    print(f"📋 Could not check existing backup: {e}")

            if not should_use_backup:
                # Create JSON output with metadata (similar to A and B scripts)
                json_output = {
                    "metadata": {
                        "generated": get_ist_timestamp(),
                        "total_models": len(normalized_mapping),
                        "scraping_source": "Google Documentation Web Scraper"
                    },
                    "modalities": normalized_mapping
                }

                with open(output_file, 'w') as f:
                    json.dump(json_output, f, indent=2)

            # Generate human-readable text version (always update the report)
            txt_filename = output_file.replace('.json', '-report.txt')
            with open(txt_filename, 'w') as f:
                f.write("=== GOOGLE MODELS MODALITY SCRAPING REPORT ===\n")
                f.write(f"Generated: {get_ist_timestamp()}\n\n")

                if should_use_backup:
                    f.write("BACKUP PRESERVATION MODE - Existing data kept\n")
                    f.write(f"Newly scraped models: {len(normalized_mapping)}\n")
                    f.write(f"Backup contains more data - preserving existing file\n")

                    # Include scraping error details
                    if self.scraping_errors:
                        f.write(f"\nScraping Errors Encountered ({len(self.scraping_errors)} total):\n")
                        for i, error in enumerate(self.scraping_errors[:5], 1):  # Show first 5 errors
                            f.write(f"  {i}. {error}\n")
                        if len(self.scraping_errors) > 5:
                            f.write(f"  ... and {len(self.scraping_errors) - 5} more errors\n")
                    f.write("\n")

                    # Load and report on the backup data being preserved
                    try:
                        with open(output_file, 'r') as backup_f:
                            backup_data = json.load(backup_f)
                            backup_modalities = backup_data.get('modalities', {})
                            f.write(f"Preserved Models: {len(backup_modalities)}\n\n")
                            for model, capabilities in backup_modalities.items():
                                input_mod = capabilities['input_modalities']
                                output_mod = capabilities['output_modalities']
                                f.write(f"{model}: {input_mod} → {output_mod}\n")
                    except Exception as e:
                        f.write(f"Error reading preserved backup: {e}\n")
                else:
                    f.write(f"Total Models: {len(normalized_mapping)}\n")

                    # Include scraping error details if any occurred
                    if self.scraping_errors:
                        f.write(f"\nScraping Errors Encountered ({len(self.scraping_errors)} total):\n")
                        for i, error in enumerate(self.scraping_errors[:3], 1):  # Show first 3 errors
                            f.write(f"  {i}. {error}\n")
                        if len(self.scraping_errors) > 3:
                            f.write(f"  ... and {len(self.scraping_errors) - 3} more errors\n")
                    f.write("\n")

                    if normalized_mapping:
                        for model, capabilities in normalized_mapping.items():
                            input_mod = capabilities['input_modalities']
                            output_mod = capabilities['output_modalities']
                            f.write(f"{model}: {input_mod} → {output_mod}\n")
                    else:
                        f.write("No modalities found - web scraping may have failed\n")
                        if self.scraping_errors:
                            f.write("See scraping errors above for details.\n")

            if should_use_backup:
                print(f"\n📋 Backup preserved at: {output_file}")
                print(f"📋 Report updated at: {txt_filename}")
                # Return the preserved backup data for the main script's validation
                try:
                    with open(output_file, 'r') as f:
                        preserved_data = json.load(f)
                        return preserved_data.get('modalities', {})
                except Exception:
                    return normalized_mapping  # Fallback to scraped data
            else:
                print(f"\nModality mapping saved to: {output_file}")
                print(f"Human-readable version saved to: {txt_filename}")
                return normalized_mapping

        except Exception as e:
            print(f"⚠️ Error during modality scraping: {e}")

            # Attempt to preserve existing modality data instead of overwriting with empty results
            backup_modalities = {}
            backup_loaded = False

            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        existing_data = json.load(f)

                    if isinstance(existing_data, dict) and 'modalities' in existing_data:
                        backup_modalities = existing_data.get('modalities', {})
                    elif isinstance(existing_data, dict):
                        backup_modalities = existing_data

                    backup_loaded = len(backup_modalities) > 0
                    if backup_loaded:
                        print(f"📋 Preserving existing modality data ({len(backup_modalities)} entries)")
                except Exception as backup_error:
                    print(f"📋 Could not read existing modality backup: {backup_error}")

            txt_filename = output_file.replace('.json', '-report.txt')
            with open(txt_filename, 'w') as f:
                f.write("=== GOOGLE MODELS MODALITY SCRAPING REPORT ===\n")
                f.write(f"Generated: {get_ist_timestamp()}\n\n")
                f.write("SCRAPING FAILURE MODE\n")
                f.write(f"Error during scraping: {e}\n\n")

                if backup_loaded:
                    f.write("BACKUP PRESERVATION MODE - Existing data kept\n")
                    f.write(f"Preserved Models: {len(backup_modalities)}\n\n")

                    # Include scraping errors if any were recorded before the failure
                    if self.scraping_errors:
                        f.write(f"Scraping Errors Encountered ({len(self.scraping_errors)} total):\n")
                        for i, error in enumerate(self.scraping_errors[:5], 1):
                            f.write(f"  {i}. {error}\n")
                        if len(self.scraping_errors) > 5:
                            f.write(f"  ... and {len(self.scraping_errors) - 5} more errors\n")
                        f.write("\n")

                    # Provide a summary of preserved modalities for transparency
                    for model, capabilities in backup_modalities.items():
                        if isinstance(capabilities, dict):
                            input_mod = capabilities.get('input_modalities', 'Unknown')
                            output_mod = capabilities.get('output_modalities', 'Unknown')
                        else:
                            input_mod = 'Unknown'
                            output_mod = 'Unknown'
                        f.write(f"{model}: {input_mod} → {output_mod}\n")
                else:
                    f.write("NO BACKUP AVAILABLE - Generated empty placeholder dataset\n\n")

                    if self.scraping_errors:
                        f.write(f"Scraping Errors Encountered ({len(self.scraping_errors)} total):\n")
                        for i, error in enumerate(self.scraping_errors[:3], 1):
                            f.write(f"  {i}. {error}\n")
                        if len(self.scraping_errors) > 3:
                            f.write(f"  ... and {len(self.scraping_errors) - 3} more errors\n")
                        f.write("\n")

            if backup_loaded:
                return backup_modalities

            # No backup to fall back on – generate empty files to keep pipeline consistent
            json_output = {
                "metadata": {
                    "generated": get_ist_timestamp(),
                    "total_models": 0,
                    "scraping_source": "Google Documentation Web Scraper"
                },
                "modalities": {}
            }

            with open(output_file, 'w') as f:
                json.dump(json_output, f, indent=2)

            print(f"⚠️ Empty output files generated due to scraping failure (no backup available)")
            return {}

if __name__ == "__main__":
    scraper = GoogleModalityScraper()
    mapping = scraper.save_modality_mapping()

    # Check if scraping produced insufficient results (likely CI/CD failure)
    if len(mapping) < 15:  # Expect 20+ models normally
        print(f"\n⚠️ WARNING: Only {len(mapping)} modalities scraped")
        print("⚠️ This suggests web scraping failed in CI/CD environment")

        # Try to restore from backup if it exists
        backup_file = get_output_file_path("03_scraped_modalities.json")
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                    backup_count = len(backup_data.get('modalities', {}))

                if backup_count > len(mapping):
                    print(f"📋 Found better backup with {backup_count} modalities - keeping backup")
                    print("📋 Current scraping results discarded due to insufficient data")
                else:
                    print(f"📋 Backup has {backup_count} modalities - keeping new results")

            except Exception as e:
                print(f"📋 Could not read backup: {e}")
        else:
            print("📋 No backup available - proceeding with limited scraped data")
            print("📋 Downstream enrichment will use embedding patterns and fallbacks")
