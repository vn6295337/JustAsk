#!/usr/bin/env python3

"""
Supabase OpenRouter Data Refresh Script - PostgreSQL Version
====================================

This script refreshes OpenRouter data in Supabase by:
1. Deleting existing OpenRouter records from 10_free-models-staging table
2. Loading finalized data from 18_validated_models.json
3. Inserting fresh OpenRouter data into Supabase

Features:
- Direct PostgreSQL connection with pipeline_writer role
- Comprehensive error handling and logging
- Data validation and safety checks
- Bulk insert with transactions
- Rollback capability with backup

Author: AI Models Discovery Pipeline
Version: 2.0 (PostgreSQL + RLS)
Last Updated: 2025-10-02
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Third-party imports
try:
    import psycopg2
    from psycopg2.extras import execute_batch, RealDictCursor
except ImportError:
    print("Error: psycopg2 package not found. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_input_file_path,
    get_ist_timestamp,
    ensure_output_dir_exists,
    set_current_pipeline,
    get_project_root,
    get_pipeline_db_connection,
    delete_rate_limits,
    upsert_rate_limits,
    parse_rate_limits,
)

# Import additional database utilities
try:
    from src.utils import (
        get_record_count,
        backup_records,
        delete_records,
        insert_records_batch,
        replace_provider_records_atomic,
    )
except ImportError as e:
    print(f"Error: Required utilities not found: {e}")
    sys.exit(1)

set_current_pipeline('openrouter')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "openrouter"

# Load environment variables
try:
    from dotenv import load_dotenv
    env_paths = [
        Path(__file__).parent.parent.parent / ".env.local",
        Path("/home/vn6295337/.env"),
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent / ".env"
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment variables from {env_path}")
            break
except ImportError:
    print("⚠️ python-dotenv not installed")

# Configuration
SCRIPT_DIR = Path(__file__).parent
JSON_FILE = SCRIPT_DIR / get_input_file_path("18_validated_models.json")
LOG_FILE = SCRIPT_DIR / get_output_file_path("19_refresh_working_report.txt")

# Database configuration
TABLE_NAME = 'justask."10_free-models-staging"'
INFERENCE_PROVIDER = "OpenRouter"

# Setup logging
def setup_logging():
    """Setup logging with timestamp"""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Supabase OpenRouter Working Version Refresh Report\n")
        f.write(f"Last Run: {get_ist_timestamp()}\n")
        f.write("=" * 60 + "\n\n")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


def load_finalized_json() -> Optional[List[Dict[str, Any]]]:
    """Load and validate finalized JSON data."""
    logger.info(f"📁 Loading finalized JSON data from {JSON_FILE}...")

    if not JSON_FILE.exists():
        logger.error(f"❌ JSON file not found: {JSON_FILE}")
        return None

    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Handle both formats
        models = data if isinstance(data, list) else data.get('models', [])

        if not models:
            logger.error(f"❌ No models found in JSON")
            return None

        # Validate OpenRouter provider
        valid_models = [m for m in models if m.get('inference_provider') == INFERENCE_PROVIDER]

        if not valid_models:
            logger.error(f"❌ No valid OpenRouter models found in JSON")
            return None

        logger.info(f"✅ Loaded {len(valid_models)} valid OpenRouter models from JSON")
        return valid_models

    except Exception as e:
        logger.error(f"❌ Failed to load JSON data: {str(e)}")
        return None


def prepare_data_for_insert(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare JSON data for database insertion."""
    logger.info("🧹 Preparing data for database insertion...")

    prepared_models = []
    auto_managed_fields = ['id', 'created_at', 'updated_at']

    for model in models:
        # Remove auto-managed fields
        clean_model = {k: v for k, v in model.items() if k not in auto_managed_fields}

        # Convert empty strings to None for nullable fields
        nullable_fields = ['license_info_text', 'license_info_url']
        for field in nullable_fields:
            if field in clean_model and clean_model[field] is not None and not str(clean_model[field]).strip():
                clean_model[field] = None

        prepared_models.append(clean_model)

    logger.info(f"✅ Prepared {len(prepared_models)} models for insertion")
    return prepared_models


def main():
    """Main orchestration function."""
    logger.info("=" * 60)
    logger.info("SUPABASE OPENROUTER DATA REFRESH STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    conn = None

    try:
        # Step 1: Connect to database
        conn = get_pipeline_db_connection()
        if not conn:
            logger.error("❌ REFRESH FAILED: Could not connect to database")
            return False

        logger.info("✅ Database connection established")
        logger.info(f"   Target table: {TABLE_NAME}")

        # Step 2: Get initial state
        initial_count = get_record_count(conn, TABLE_NAME, INFERENCE_PROVIDER)
        if initial_count is None:
            logger.error("❌ REFRESH FAILED: Could not query initial state")
            return False

        # Step 3: Load JSON data
        models = load_finalized_json()
        if not models:
            logger.error("❌ REFRESH FAILED: Could not load JSON data")
            return False

        # Step 4: Prepare data
        prepared_models = prepare_data_for_insert(models)
        if not prepared_models:
            logger.error("❌ REFRESH FAILED: No valid models to insert")
            return False

        # Rate limits (22) are published with the live list in the deploy step, not from staging.

        # Atomic: delete + insert + verify in ONE transaction.
        # Any failure rolls back, leaving the previous rows intact.
        logger.info(f"📤 Atomically replacing {initial_count} -> {len(prepared_models)} {INFERENCE_PROVIDER} rows in {TABLE_NAME}...")
        if not replace_provider_records_atomic(
            conn, TABLE_NAME, INFERENCE_PROVIDER, prepared_models,
            tolerance=0,
        ):
            logger.error("❌ REFRESH FAILED: transaction rolled back, original data untouched")
            return False

        final_count = len(prepared_models)
        logger.info(f"✅ Replaced and verified {final_count} models (committed)")

        # Success
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("=" * 60)
        logger.info("🎉 SUPABASE OPENROUTER DATA REFRESH COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"📊 Summary:")
        logger.info(f"   • Initial OpenRouter records: {initial_count}")
        logger.info(f"   • Records deleted: {initial_count}")
        logger.info(f"   • New records inserted: {len(prepared_models)}")
        logger.info(f"   • Final record count: {final_count}")
        logger.info(f"   • Model-AA mappings: Refreshed for {INFERENCE_PROVIDER}")
        logger.info(f"   • Processing time: {duration}")
        logger.info(f"   • Report file: {LOG_FILE}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR: {str(e)}")
        if conn:
            conn.rollback()
        return False

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
