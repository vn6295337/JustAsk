#!/usr/bin/env python3
"""
Groq Pipeline Environment Manager
================================

Handles environment variables, API keys, and external service configuration
following OpenRouter/Google pipeline patterns.

Features:
- Multi-source API key retrieval (Supabase → env vars → user prompts)
- Supabase configuration management
- Chrome driver environment setup
- Environment validation and fallbacks

Author: AI Models Discovery Pipeline
Version: 1.0
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Try to import Supabase for advanced key management
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    Client = None
    SUPABASE_AVAILABLE = False


class GroqEnvironment:
    """Environment and credentials manager for Groq pipeline"""

    def __init__(self):
        """Initialize environment manager and load environment variables"""
        self.supabase_client = None
        self._load_environment_files()

    def _load_environment_files(self):
        """Load environment variables from multiple possible .env locations"""
        # Check for .env in multiple possible locations following OpenRouter pattern
        env_paths = [
            Path("/home/vn6295337/.env"),  # Home directory
            Path(__file__).parent.parent / ".env",  # justask-registry root
            Path(__file__).parent / ".env"  # utils directory
        ]

        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                return

        # No warning needed - env vars may come from GitHub Actions or system environment

    def get_supabase_client(self) -> Optional[Client]:
        """
        Initialize Supabase client for secret retrieval

        Returns:
            Supabase client instance or None if unavailable
        """
        if not SUPABASE_AVAILABLE:
            return None

        if self.supabase_client:
            return self.supabase_client

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            print("⚠️ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
            return None

        try:
            self.supabase_client = create_client(supabase_url, supabase_key)
            print("✓ Supabase client initialized successfully")
            return self.supabase_client
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            return None

    def get_groq_api_key(self) -> Optional[str]:
        """
        Get GROQ_API_KEY from multiple sources with fallbacks

        Priority:
        1. Supabase secrets table
        2. Environment variable GROQ_API_KEY
        3. User prompt (if interactive)

        Returns:
            GROQ API key or None if not found
        """
        # Method 1: Try Supabase secrets
        if SUPABASE_AVAILABLE:
            client = self.get_supabase_client()
            if client:
                try:
                    response = client.table('secrets').select('value').eq('name', 'GROQ_API_KEY').execute()
                    if response.data and len(response.data) > 0:
                        api_key = response.data[0].get('value')
                        if api_key:
                            print("✓ Retrieved GROQ API key from Supabase secrets")
                            return api_key
                except Exception as e:
                    print(f"⚠️ Failed to retrieve GROQ API key from Supabase: {e}")

        # Method 2: Try environment variable
        api_key = os.getenv('GROQ_API_KEY')
        if api_key:
            print("✓ Retrieved GROQ API key from environment variable")
            return api_key

        # Method 3: Interactive prompt (only if running interactively)
        if sys.stdin.isatty():
            try:
                api_key = input("Enter GROQ_API_KEY: ").strip()
                if api_key:
                    print("✓ GROQ API key provided interactively")
                    return api_key
            except (KeyboardInterrupt, EOFError):
                pass

        # No key found
        print("❌ GROQ API key not found")
        print("Please add GROQ_API_KEY to:")
        print("  1. Supabase secrets table")
        print("  2. Environment variable")
        print("  3. /home/vn6295337/.env file")
        return None

    def get_supabase_config(self) -> Dict[str, Optional[str]]:
        """
        Get Supabase configuration for database operations

        Returns:
            Dictionary with Supabase URL and key
        """
        return {
            "url": os.getenv("SUPABASE_URL"),
            "key": os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
        }

    def validate_supabase_config(self) -> bool:
        """
        Validate that Supabase configuration is available

        Returns:
            True if configuration is valid, False otherwise
        """
        config = self.get_supabase_config()

        if not config["url"]:
            print("❌ SUPABASE_URL not found in environment")
            return False

        if not config["key"]:
            print("❌ SUPABASE_ANON_KEY not found in environment")
            return False

        print("✓ Supabase configuration valid")
        return True

    def setup_chrome_environment(self) -> Dict[str, str]:
        """
        Setup environment variables for Chrome/Selenium

        Returns:
            Dictionary of environment variables for Chrome
        """
        chrome_env = {}

        # Set display for headless Chrome (useful in CI/CD)
        if not os.getenv("DISPLAY"):
            chrome_env["DISPLAY"] = ":99"

        # Chrome sandbox settings for containerized environments
        chrome_env["CHROME_NO_SANDBOX"] = "true"
        chrome_env["CHROME_DISABLE_DEV_SHM"] = "true"

        # WebDriver manager settings
        chrome_env["WDM_LOG_LEVEL"] = "0"  # Suppress webdriver-manager logs
        chrome_env["WDM_PRINT_FIRST_LINE"] = "False"

        return chrome_env

    def get_pipeline_environment(self) -> Dict[str, str]:
        """
        Get complete environment configuration for pipeline execution

        Returns:
            Dictionary containing all necessary environment variables
        """
        env_vars = {}

        # Core API keys
        groq_key = self.get_groq_api_key()
        if groq_key:
            env_vars["GROQ_API_KEY"] = groq_key

        # Supabase configuration
        supabase_config = self.get_supabase_config()
        if supabase_config["url"]:
            env_vars["SUPABASE_URL"] = supabase_config["url"]
        if supabase_config["key"]:
            env_vars["SUPABASE_ANON_KEY"] = supabase_config["key"]

        # Chrome environment
        chrome_env = self.setup_chrome_environment()
        env_vars.update(chrome_env)

        return env_vars

    def validate_environment(self) -> Dict[str, bool]:
        """
        Validate all required environment configurations

        Returns:
            Dictionary with validation results for each component
        """
        results = {}

        # Check GROQ API key
        results["groq_api_key"] = self.get_groq_api_key() is not None

        # Check Supabase configuration
        results["supabase_config"] = self.validate_supabase_config()

        # Check Supabase connectivity
        results["supabase_connection"] = self.get_supabase_client() is not None

        return results

    def get_environment_info(self) -> Dict[str, any]:
        """
        Get comprehensive information about the environment setup

        Returns:
            Dictionary with environment status and configuration
        """
        validation = self.validate_environment()
        supabase_config = self.get_supabase_config()

        return {
            "supabase_available": SUPABASE_AVAILABLE,
            "validation": validation,
            "supabase_url_configured": bool(supabase_config["url"]),
            "supabase_key_configured": bool(supabase_config["key"]),
            "environment_files_checked": [
                "/home/vn6295337/.env",
                str(Path(__file__).parent.parent / ".env"),
                str(Path(__file__).parent / ".env")
            ]
        }

    def export_environment(self) -> None:
        """Export environment variables to current process"""
        env_vars = self.get_pipeline_environment()
        for key, value in env_vars.items():
            os.environ[key] = value
        print(f"✓ Exported {len(env_vars)} environment variables")


# Global environment instance
groq_env = GroqEnvironment()


def get_environment() -> GroqEnvironment:
    """
    Get global environment instance

    Returns:
        Global GroqEnvironment instance
    """
    return groq_env


# Convenience functions for common environment access
def setup_chrome_environment() -> Dict[str, str]:
    """Setup Chrome environment variables"""
    return groq_env.setup_chrome_environment()


if __name__ == "__main__":
    # Test environment management
    env_manager = GroqEnvironment()

    print("=== Groq Environment Manager Test ===")
    print("\nEnvironment Information:")
    env_info = env_manager.get_environment_info()
    for key, value in env_info.items():
        print(f"  {key}: {value}")

    print("\nValidation Results:")
    validation = env_manager.validate_environment()
    for component, is_valid in validation.items():
        status = "✓" if is_valid else "❌"
        print(f"  {status} {component}")

    print("\nTesting API key retrieval...")
    api_key = env_manager.get_groq_api_key()
    if api_key:
        print(f"  ✓ GROQ API key found (length: {len(api_key)})")
    else:
        print("  ❌ GROQ API key not found")

    print("\n✓ Environment manager test completed")