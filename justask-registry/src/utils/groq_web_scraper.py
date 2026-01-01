#!/usr/bin/env python3
"""
Groq Web Scraper Module
======================

Modular web scraping functions for the Groq pipeline with better
maintainability and testability.

Features:
- Production models scraping (dual-source: production-models + production-systems)
- Rate limits scraping with dynamic loading
- Modalities scraping with fallback patterns
- Configurable Chrome driver setup
- Comprehensive error handling and retry logic

Author: AI Models Discovery Pipeline
Version: 1.0
"""

import time
import datetime
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys
import os

from .config_manager import get_config
from .env_manager import get_environment, setup_chrome_environment
from .path_manager import get_output_path

# Web scraping dependencies (optional - only needed for Groq pipeline)
SELENIUM_AVAILABLE = False
webdriver = None
Service = None
Options = None
By = None
WebDriverWait = None
EC = None
ChromeDriverManager = None
BeautifulSoup = None

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    SELENIUM_AVAILABLE = True
except ImportError:
    # Selenium is optional - only needed for Groq web scraping
    pass


class GroqWebScraper:
    """Modular web scraper for Groq documentation"""

    def __init__(self):
        """Initialize scraper with configuration"""
        self.config = get_config()
        self.env = get_environment()
        self.driver = None

        # Load configurations
        self.endpoints = self.config.get_api_endpoints()
        self.timeouts = self.config.get_timeouts()
        self.chrome_options = self.config.get_chrome_options()

    def setup_chrome_driver(self) -> Any:
        """
        Set up Chrome driver with configuration-based options

        Returns:
            Configured Chrome WebDriver instance
        """
        # Setup environment for Chrome
        chrome_env = setup_chrome_environment()
        for key, value in chrome_env.items():
            os.environ[key] = value

        # Configure Chrome options
        options = Options()

        # Detect available Chrome binary (Google Chrome or Chromium)
        chrome_binary = None
        chrome_type = "chromium"

        possible_binaries = [
            ("/usr/bin/google-chrome", "chrome"),
            ("/usr/bin/google-chrome-stable", "chrome"),
            ("/usr/bin/chromium", "chromium"),
            ("/usr/bin/chromium-browser", "chromium")
        ]

        for binary_path, binary_type in possible_binaries:
            if Path(binary_path).exists():
                chrome_binary = binary_path
                chrome_type = binary_type
                print(f"✅ Found Chrome binary: {chrome_binary}")
                break

        if chrome_binary:
            options.binary_location = chrome_binary
        else:
            print("⚠️ No Chrome binary found, using system default")

        # Add standard headless Chrome options
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # Apply custom options from config
        for option in self.chrome_options:
            options.add_argument(option)

        # Set explicit Chrome binary location
        if chrome_binary:
            options.binary_location = chrome_binary
        else:
            # Default location on Ubuntu/Debian
            options.binary_location = "/usr/bin/google-chrome"

        # Create service with ChromeDriverManager for automatic version matching
        # Check if chromedriver is already in PATH (e.g., from CI setup)
        import shutil
        system_chromedriver = shutil.which('chromedriver')

        if system_chromedriver:
            print(f"✅ Using system ChromeDriver: {system_chromedriver}")
            service = Service(system_chromedriver)
        else:
            print("⚙️ Downloading ChromeDriver via webdriver-manager...")
            try:
                # ChromeDriverManager will choose a chromedriver compatible with installed Chrome
                driver_path = ChromeDriverManager(chrome_type=chrome_type).install()
                service = Service(driver_path)
                print(f"✅ Downloaded ChromeDriver: {driver_path}")
            except Exception as e:
                try:
                    print(f"⚠️ ChromeDriverManager with chrome_type={chrome_type} failed, trying default")
                    driver_path = ChromeDriverManager().install()
                    service = Service(driver_path)
                    print(f"✅ Downloaded ChromeDriver (default): {driver_path}")
                except Exception as e2:
                    raise RuntimeError(
                        f"ChromeDriver not available and webdriver-manager failed to download "
                        f"a matching binary. Chrome type: {chrome_type}, Errors: {e}, {e2}"
                    )

        # Create and configure driver
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(self.timeouts.get("selenium_implicit", 5))

        return driver

    def scrape_production_models(self) -> List[Dict[str, Any]]:
        """
        Scrape production models from both production-models and production-systems sections

        Returns:
            List of production model dictionaries
        """
        print("=" * 80)
        print("🚀 GROQ PRODUCTION MODELS EXTRACTION")
        print("=" * 80)
        print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        production_models = []

        try:
            self.driver = self.setup_chrome_driver()
            print("✅ ChromeDriver configured from settings")

            # Extract from production-models section only
            models_from_production = self._scrape_production_models_section()
            production_models.extend(models_from_production)

            # Skipping production-systems section per user requirements
            # models_from_systems = self._scrape_production_systems_section()
            # production_models.extend(models_from_systems)

        except Exception as error:
            print(f"❌ Error during production models scraping: {error}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Browser closed successfully")

        print(f"✅ Total production models extracted: {len(production_models)}")
        return production_models

    def _scrape_production_models_section(self) -> List[Dict[str, Any]]:
        """Scrape models from production-models section using robust selectors"""
        url = self.endpoints["production_models"]
        print(f"🔍 Extracting production models from: {url}")

        self.driver.get(url)
        print("⏳ Waiting for dynamic content...")

        WebDriverWait(self.driver, self.timeouts["page_load"]).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
        print("✅ Page content loaded")

        models = []

        # Find the production-models section by anchor/heading
        # The URL has #production-models anchor, find that section's table
        try:
            # Try to find element with id="production-models" or heading containing "Production Models"
            production_section = None
            try:
                production_section = self.driver.find_element(By.ID, 'production-models')
                print("✅ Found section by id='production-models'")
            except:
                # Try finding by heading text
                headings = self.driver.find_elements(By.TAG_NAME, 'h2')
                for heading in headings:
                    if 'production models' in heading.text.lower():
                        production_section = heading
                        print(f"✅ Found section by heading: {heading.text}")
                        break

            if not production_section:
                print("⚠️ Could not find production-models section, trying all tables")
                tables = self.driver.find_elements(By.TAG_NAME, 'table')
            else:
                # Find table after the section heading
                parent = production_section.find_element(By.XPATH, './ancestor::div[1]')
                tables = parent.find_elements(By.TAG_NAME, 'table')
                if not tables:
                    # Try looking in following siblings
                    tables = production_section.find_elements(By.XPATH, './following::table')

            # Find the right table (contains Model ID, Context Window, etc.)
            target_table = None
            for table in tables[:3]:  # Check first 3 tables only
                header_text = table.text.lower()
                if 'model id' in header_text and 'context window' in header_text:
                    target_table = table
                    print(f"✅ Found target table with production models")
                    break

            if not target_table:
                print("❌ Could not find production models table")
                return []

            tbody = target_table.find_element(By.TAG_NAME, 'tbody')
            rows = tbody.find_elements(By.TAG_NAME, 'tr')
            total_rows = len(rows)
            print(f"📊 Found {total_rows} data rows in tbody")

            # Iterate through ALL data rows in tbody
            for row_idx, row in enumerate(rows, 1):
                try:
                    # Get all cells in the row
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) < 4:
                        print(f"   ⚠️ Row {row_idx}: Not enough columns, skipping")
                        continue

                    # Column 1: Model ID (provider_slug) and name
                    # Try to extract model slug from span
                    try:
                        model_slug = cells[0].find_element(By.TAG_NAME, 'span').text.strip()
                    except:
                        # Fallback: try getting text from the cell
                        try:
                            cell_text = cells[0].text.strip()
                            # Model slug is usually the first line
                            model_slug = cell_text.split('\n')[0].strip()
                        except:
                            print(f"   ⚠️ Row {row_idx}: Could not find model slug, skipping")
                            continue

                    # Extract human_readable_name from link
                    try:
                        human_name = cells[0].find_element(By.TAG_NAME, 'a').text.strip()
                    except:
                        # Fallback to model slug
                        human_name = model_slug

                    # Column 4: Rate limits (may have multiple spans)
                    rate_limits_parts = []
                    try:
                        rate_limit_spans = cells[3].find_elements(By.TAG_NAME, 'span')
                        for span in rate_limit_spans:
                            text = span.text.strip()
                            if text:
                                rate_limits_parts.append(text)
                    except:
                        pass

                    # Fallback: try getting all text from rate limit cell
                    if not rate_limits_parts:
                        try:
                            rate_limit_text = cells[3].text.strip()
                            if rate_limit_text:
                                rate_limits_parts = [rate_limit_text]
                        except:
                            pass

                    rate_limits_str = "\n".join(rate_limits_parts) if rate_limits_parts else ""

                    # Skip invalid rows
                    if not model_slug or model_slug.lower() in ['model', 'model id', '']:
                        continue

                    model_data = {
                        "model_id": model_slug,
                        "model_display_name": human_name,
                        "object": "model",
                        "created": int(datetime.datetime.now().timestamp()),
                        "model_provider": "Groq",
                        "active": True,
                        "rate_limits": rate_limits_str,
                        "context_window": "",
                        "max_completion_tokens": "",
                        "public_apps": True,
                        "source_section": "production-models"
                    }

                    models.append(model_data)
                    print(f"   ✅ Row {row_idx}: {model_slug} - {human_name}")

                except Exception as e:
                    print(f"   ❌ Row {row_idx}: Error extracting data - {e}")
                    continue

        except Exception as e:
            print(f"❌ Error finding table or rows: {e}")
            import traceback
            traceback.print_exc()

        print(f"✅ Extracted {len(models)} production models")
        return models

    def _scrape_production_systems_section(self) -> List[Dict[str, Any]]:
        """Scrape models from production-systems section"""
        url = self.endpoints["production_systems"]
        print(f"\n🔍 Extracting production systems from: {url}")

        self.driver.get(url)
        print("⏳ Waiting for dynamic content...")

        WebDriverWait(self.driver, self.timeouts["page_load"]).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
        print("✅ Page content loaded")

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        tables = soup.find_all('table')
        print(f"📊 Found {len(tables)} tables in production-systems section")

        models = []

        for i, table in enumerate(tables):
            print(f"✅ Processing production systems table {i+1}")

            header_row = table.find('tr')
            if not header_row:
                continue

            headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
            print(f"📋 Production Systems headers: {headers}")

            # Look for model-related columns (more flexible matching)
            has_model_column = any('model' in h.lower() for h in headers)
            if not has_model_column:
                continue

            # Find column indices with flexible matching
            model_col = next((i for i, h in enumerate(headers) if 'model' in h.lower()), 0)
            developer_col = next((i for i, h in enumerate(headers) if any(keyword in h.lower() for keyword in ['developer', 'provider', 'company'])), 1)
            context_col = next((i for i, h in enumerate(headers) if 'context' in h.lower()), 2)
            completion_col = next((i for i, h in enumerate(headers) if any(keyword in h.lower() for keyword in ['completion', 'max', 'output'])), 3)

            # Parse data rows
            data_rows = table.find_all('tr')[1:]  # Skip header
            print(f"📊 Found {len(data_rows)} data rows in Production Systems")

            for row_num, row in enumerate(data_rows, 1):
                cells = row.find_all(['td', 'th'])
                if len(cells) > model_col:
                    # Extract slug from code element if present, otherwise use text
                    cell = cells[model_col]
                    code_elem = cell.find('code')
                    if code_elem:
                        model_slug = code_elem.get_text().strip()
                    else:
                        # Fallback: try to extract from full text
                        full_text = cell.get_text().strip()
                        # Pattern: "Display NameSlug" - extract after last uppercase sequence
                        parts = full_text.split()
                        model_slug = parts[-1] if parts else full_text

                    # Get display name from cell text (before code element)
                    model_display_name = cell.get_text().strip()
                    if code_elem:
                        model_display_name = model_display_name.replace(code_elem.get_text(), '').strip()

                    if model_slug and model_slug.lower() not in ['model', 'model id', '']:
                        model_data = {
                            'model_id': model_slug,
                            'model_display_name': model_display_name,
                            'object': 'model',
                            'created': int(time.time()),
                            'model_provider': cells[developer_col].get_text().strip() if len(cells) > developer_col else 'Groq',
                            'active': True,
                            'context_window': cells[context_col].get_text().strip().replace(',', '') if len(cells) > context_col else '',
                            'max_completion_tokens': cells[completion_col].get_text().strip().replace(',', '') if len(cells) > completion_col else '',
                            'public_apps': True,
                            'source_section': 'production-systems'
                        }

                        models.append(model_data)
                        print(f"   ✅ Row {row_num}: {model_data['model_id']} / {model_display_name} ({model_data['model_provider']}) [SYSTEMS]")

            break  # Only process first valid table

        return models

    def scrape_rate_limits(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape rate limits with dynamic loading support

        Returns:
            Dictionary mapping model IDs to rate limit data
        """
        print("\n" + "=" * 80)
        print("🚀 GROQ RATE LIMITS EXTRACTION")
        print("=" * 80)
        print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        rate_limits = {}

        try:
            self.driver = self.setup_chrome_driver()
            print("✅ ChromeDriver configured from settings")

            url = self.endpoints["rate_limits"]
            print(f"🔍 Extracting rate limits from: {url}")

            self.driver.get(url)
            print("⏳ Waiting for page and dynamic content to load...")

            WebDriverWait(self.driver, self.timeouts["page_load"]).until(
                EC.presence_of_element_located((By.TAG_NAME, 'table'))
            )

            # Wait for data to populate with retry logic
            rate_limits = self._extract_rate_limits_with_retry()

        except Exception as error:
            print(f"❌ Error scraping rate limits: {error}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Browser closed successfully")

        print(f"✅ Total rate limits extracted: {len(rate_limits)}")
        return rate_limits

    def _extract_rate_limits_with_retry(self) -> Dict[str, Dict[str, str]]:
        """Extract rate limits with retry logic for dynamic content"""
        max_attempts = self.timeouts.get("max_retries", 5)
        retry_delay = self.timeouts.get("retry_delay", 3)

        for attempt in range(max_attempts):
            print(f"⏳ Attempt {attempt + 1}/{max_attempts}: Waiting for data to populate...")
            time.sleep(retry_delay)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            tables = soup.find_all('table')

            for table in tables:
                header_row = table.find('tr')
                if header_row:
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                    if 'MODEL ID' in [h.upper() for h in headers]:
                        data_rows = table.find_all('tr')[1:]
                        if len(data_rows) > 0:
                            first_row_cells = [cell.get_text().strip() for cell in data_rows[0].find_all(['td', 'th'])]
                            if any(cell for cell in first_row_cells):
                                print(f"✅ Data loaded successfully on attempt {attempt + 1}")
                                return self._parse_rate_limits_table(table, headers)

        print("⚠️ Failed to load dynamic rate limits data after all attempts")
        return {}

    def _parse_rate_limits_table(self, table, headers: List[str]) -> Dict[str, Dict[str, str]]:
        """Parse rate limits from table"""
        rate_limits = {}

        print(f"✅ Processing rate limits table with headers: {headers}")

        # Find column indices
        model_col = next((i for i, h in enumerate(headers) if 'model' in h.lower()), 0)
        rpm_col = next((i for i, h in enumerate(headers) if h.upper() == 'RPM'), -1)
        rpd_col = next((i for i, h in enumerate(headers) if h.upper() == 'RPD'), -1)
        tpm_col = next((i for i, h in enumerate(headers) if h.upper() == 'TPM'), -1)
        tpd_col = next((i for i, h in enumerate(headers) if h.upper() == 'TPD'), -1)
        ash_col = next((i for i, h in enumerate(headers) if h.upper() == 'ASH'), -1)
        asd_col = next((i for i, h in enumerate(headers) if h.upper() == 'ASD'), -1)

        # Parse data rows
        data_rows = table.find_all('tr')[1:]  # Skip header

        for row_num, row in enumerate(data_rows, 1):
            cells = row.find_all(['td', 'th'])
            if len(cells) > model_col:
                model_id = cells[model_col].get_text().strip()

                if model_id and model_id.lower() not in ['model', 'model id', '']:
                    rate_limit_data = {
                        'model_id': model_id,
                        'RPM': cells[rpm_col].get_text().strip() if rpm_col >= 0 and len(cells) > rpm_col else '-',
                        'RPD': cells[rpd_col].get_text().strip() if rpd_col >= 0 and len(cells) > rpd_col else '-',
                        'TPM': cells[tpm_col].get_text().strip() if tpm_col >= 0 and len(cells) > tpm_col else '-',
                        'TPD': cells[tpd_col].get_text().strip() if tpd_col >= 0 and len(cells) > tpd_col else '-',
                        'ASH': cells[ash_col].get_text().strip() if ash_col >= 0 and len(cells) > ash_col else '-',
                        'ASD': cells[asd_col].get_text().strip() if asd_col >= 0 and len(cells) > asd_col else '-'
                    }

                    rate_limits[model_id] = rate_limit_data
                    print(f"   ✅ Row {row_num}: {model_id} - RPM:{rate_limit_data['RPM']}, TPM:{rate_limit_data['TPM']}")

        return rate_limits

    def scrape_model_modalities(self, production_models: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
        """
        Scrape input/output modalities for all production models

        Args:
            production_models: List of production model dictionaries

        Returns:
            Dictionary mapping model IDs to modality information
        """
        print("\n" + "=" * 80)
        print("🚀 GROQ INPUT/OUTPUT MODALITIES EXTRACTION")
        print("=" * 80)
        print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not production_models:
            print("⚠️ No production models provided for modality extraction")
            return {}

        print(f"📋 Found {len(production_models)} production models to process")

        all_modalities = {}

        try:
            self.driver = self.setup_chrome_driver()
            print("✅ ChromeDriver configured from settings")

            # Process each model
            for i, model in enumerate(production_models, 1):
                model_id = model.get('model_id')
                if not model_id:
                    print(f"⚠️ Model {i} has no 'model_id' field, skipping")
                    continue

                print(f"📊 Processing model {i}/{len(production_models)}: {model_id}")

                # Extract modalities for this model
                modalities = self._extract_modalities_for_model(model_id)
                all_modalities[model_id] = modalities

                # Brief pause between requests
                time.sleep(self.timeouts.get("model_scraping_delay", 1))

        except Exception as error:
            print(f"❌ Error in modalities extraction: {error}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Browser closed successfully")

        print(f"✅ Total models processed: {len(all_modalities)}")
        return all_modalities

    def _extract_modalities_for_model(self, model_id: str) -> Dict[str, List[str]]:
        """Extract input and output modalities for a specific model"""
        url_template = self.endpoints.get("model_details_template", "https://console.groq.com/docs/model/{model_id}")
        url = url_template.format(model_id=model_id)

        print(f"   🔍 Extracting modalities from: {url}")

        try:
            self.driver.get(url)

            WebDriverWait(self.driver, self.timeouts["element_wait"]).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )

            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            input_modalities = []
            output_modalities = []

            # Look for INPUT/OUTPUT div elements
            input_divs = soup.find_all(['div', 'span'], string=lambda text: text and text.strip().upper() == 'INPUT')
            output_divs = soup.find_all(['div', 'span'], string=lambda text: text and text.strip().upper() == 'OUTPUT')

            print(f"      🔍 Found {len(input_divs)} INPUT divs, {len(output_divs)} OUTPUT divs")

            # Extract content after INPUT sections
            for input_div in input_divs:
                if input_div.parent:
                    parent_text = input_div.parent.get_text().lower()

                    if 'audio' in parent_text and 'Audio' not in input_modalities:
                        input_modalities.append('Audio')
                        print(f"         ➡️ Input: Audio")
                    if 'text' in parent_text and 'Text' not in input_modalities:
                        input_modalities.append('Text')
                        print(f"         ➡️ Input: Text")
                    if 'image' in parent_text and 'Image' not in input_modalities:
                        input_modalities.append('Image')
                        print(f"         ➡️ Input: Image")
                    if 'video' in parent_text and 'Video' not in input_modalities:
                        input_modalities.append('Video')
                        print(f"         ➡️ Input: Video")

            # Extract content after OUTPUT sections
            for output_div in output_divs:
                if output_div.parent:
                    parent_text = output_div.parent.get_text().lower()

                    if 'audio' in parent_text and 'Audio' not in output_modalities:
                        output_modalities.append('Audio')
                        print(f"         ⬅️ Output: Audio")
                    if 'text' in parent_text and 'Text' not in output_modalities:
                        output_modalities.append('Text')
                        print(f"         ⬅️ Output: Text")
                    if 'image' in parent_text and 'Image' not in output_modalities:
                        output_modalities.append('Image')
                        print(f"         ⬅️ Output: Image")
                    if 'video' in parent_text and 'Video' not in output_modalities:
                        output_modalities.append('Video')
                        print(f"         ⬅️ Output: Video")

            # Fallback logic based on model type if no modalities found
            if not input_modalities and not output_modalities:
                print(f"      ⚠️ No modalities found in webpage content, using model type fallback")
                return self._get_fallback_modalities(model_id)

            return {
                'input_modalities': input_modalities,
                'output_modalities': output_modalities
            }

        except Exception as error:
            print(f"      ❌ Error extracting modalities for {model_id}: {error}")
            return self._get_fallback_modalities(model_id)

    def _get_fallback_modalities(self, model_id: str) -> Dict[str, List[str]]:
        """Get fallback modalities based on model type"""
        model_lower = model_id.lower()

        if 'whisper' in model_lower:
            modalities = {'input_modalities': ['Audio'], 'output_modalities': ['Text']}
        elif 'tts' in model_lower:
            modalities = {'input_modalities': ['Text'], 'output_modalities': ['Audio']}
        elif any(model_type in model_lower for model_type in ['llama', 'gpt', 'guard', 'qwen', 'gemma']):
            modalities = {'input_modalities': ['Text'], 'output_modalities': ['Text']}
            if 'guard' in model_lower:
                modalities['input_modalities'] = ['Image', 'Text']
        else:
            modalities = {'input_modalities': ['Text'], 'output_modalities': ['Text']}

        print(f"         ➡️ Fallback Input: {', '.join(modalities['input_modalities'])}")
        print(f"         ⬅️ Fallback Output: {', '.join(modalities['output_modalities'])}")

        return modalities


# Convenience functions for backward compatibility
def scrape_production_models() -> List[Dict[str, Any]]:
    """Scrape production models using the modular scraper"""
    scraper = GroqWebScraper()
    return scraper.scrape_production_models()


def scrape_rate_limits() -> Dict[str, Dict[str, str]]:
    """Scrape rate limits using the modular scraper"""
    scraper = GroqWebScraper()
    return scraper.scrape_rate_limits()


def scrape_all_modalities(production_models: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
    """Scrape modalities for all models using the modular scraper"""
    scraper = GroqWebScraper()
    return scraper.scrape_model_modalities(production_models)


if __name__ == "__main__":
    # Test the web scraper
    print("=== Groq Web Scraper Test ===")

    scraper = GroqWebScraper()

    # Test production models scraping
    print("\nTesting production models scraping...")
    models = scraper.scrape_production_models()
    print(f"Scraped {len(models)} production models")

    if models:
        # Test rate limits scraping
        print("\nTesting rate limits scraping...")
        rate_limits = scraper.scrape_rate_limits()
        print(f"Scraped {len(rate_limits)} rate limit entries")

        # Test modalities scraping (first 2 models only)
        print("\nTesting modalities scraping...")
        test_models = models[:2]
        modalities = scraper.scrape_model_modalities(test_models)
        print(f"Scraped modalities for {len(modalities)} models")

    print("\n✓ Web scraper test completed")