#!/usr/bin/env python3

"""
Production Deployment Script: OpenRouter Data Migration - PostgreSQL Version
==============================================

This script deploys OpenRouter data from 10_free-models-staging to 11_free-models-live by:
1. Backing up existing OpenRouter records from 11_free-models-live
2. Deleting existing OpenRouter records from 11_free-models-live
3. Copying OpenRouter data from 10_free-models-staging to 11_free-models-live

Features:
- Direct PostgreSQL connection with pipeline_writer role
- Complete rollback protection with backup/restore
- Bulk operations with transactions
- Comprehensive error handling and logging

Author: AI Models Discovery Pipeline
Version: 2.0 (PostgreSQL + RLS)
Last Updated: 2025-10-02
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Third-party imports
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2 package not found. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from src.utils import (
    get_output_file_path,
    get_ist_timestamp,
    set_current_pipeline,
    get_project_root,
    get_pipeline_db_connection,
)

# Import additional database utilities
try:
    from src.utils import (
        get_record_count,
        backup_records,
        delete_records,
        insert_records_batch,
        load_staging_data,
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
LOG_FILE = get_output_file_path("21_deploy_main_report.txt")

# Database configuration
STAGING_TABLE = 'justask."10_free-models-staging"'
PRODUCTION_TABLE = 'justask."11_free-models-live"'
INFERENCE_PROVIDER = "OpenRouter"

# Setup logging
def setup_logging():
    """Setup logging with timestamp"""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Deploy to AI Models Main Log\n")
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


def prepare_data_for_production(staging_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare staging data for production deployment."""
    logger.info("🧹 Preparing staging data for production deployment...")

    prepared_models = []
    auto_managed_fields = ['id', 'created_at', 'updated_at']
    excluded_fields = ['provider_slug']  # Fields that exist in 10_free-models-staging but not in 11_free-models-live

    for model in staging_data:
        # Remove auto-managed and excluded fields
        clean_model = {k: v for k, v in model.items() if k not in auto_managed_fields + excluded_fields}

        # Convert empty strings to None for nullable fields
        nullable_fields = ['license_info_text', 'license_info_url']
        for field in nullable_fields:
            if field in clean_model and clean_model[field] is not None and not str(clean_model[field]).strip():
                clean_model[field] = None

        prepared_models.append(clean_model)

    logger.info(f"✅ Prepared {len(prepared_models)} models for production deployment")
    return prepared_models


def main():
    """Main orchestration function for production deployment."""
    logger.info("=" * 70)
    logger.info("OPENROUTER PRODUCTION DEPLOYMENT STARTED")
    logger.info("=" * 70)
    start_time = datetime.now()
    conn = None

    try:
        # Step 1: Connect to database
        conn = get_pipeline_db_connection()
        if not conn:
            logger.error("❌ DEPLOYMENT FAILED: Could not connect to database")
            return False

        logger.info("✅ Database connection established")
        logger.info(f"   Staging table: {STAGING_TABLE}")
        logger.info(f"   Production table: {PRODUCTION_TABLE}")

        # Step 2: Get initial state
        staging_count = get_record_count(conn, STAGING_TABLE, INFERENCE_PROVIDER)
        production_count = get_record_count(conn, PRODUCTION_TABLE, INFERENCE_PROVIDER)

        if staging_count is None or production_count is None:
            logger.error("❌ DEPLOYMENT FAILED: Could not query initial state")
            return False

        if staging_count == 0:
            logger.error("❌ DEPLOYMENT FAILED: No OpenRouter data in staging table")
            return False

        # Step 3: Load staging data
        logger.info(f"📁 Loading OpenRouter data from {STAGING_TABLE}...")
        staging_data = load_staging_data(conn, STAGING_TABLE, INFERENCE_PROVIDER)
        if not staging_data:
            logger.error("❌ DEPLOYMENT FAILED: Could not load staging data")
            return False

        logger.info(f"✅ Loaded {len(staging_data)} OpenRouter records from staging")

        # Step 4: Prepare data for production
        prepared_data = prepare_data_for_production(staging_data)
        if not prepared_data:
            logger.error("❌ DEPLOYMENT FAILED: No valid data to deploy")
            return False

        # Atomic: delete + insert + verify in ONE transaction; any failure rolls back.
        logger.info(f"🚀 Atomically deploying {len(prepared_data)} models to {PRODUCTION_TABLE} (replacing {production_count})...")
        if not replace_provider_records_atomic(
            conn, PRODUCTION_TABLE, INFERENCE_PROVIDER, prepared_data, tolerance=0
        ):
            logger.error("❌ DEPLOYMENT FAILED: transaction rolled back, production data untouched")
            return False

        final_count = len(prepared_data)
        logger.info(f"✅ Deployed and verified {final_count} models (committed)")

        # Success
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("=" * 70)
        logger.info("🎉 OPENROUTER PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"📊 Deployment Summary:")
        logger.info(f"   • Staging records processed: {len(staging_data)}")
        logger.info(f"   • Production records deleted: {production_count}")
        logger.info(f"   • New records deployed: {len(prepared_data)}")
        logger.info(f"   • Final production count: {final_count}")
        logger.info(f"   • Deployment time: {duration}")
        logger.info(f"   • Log file: {LOG_FILE}")
        logger.info("=" * 70)
        logger.info("🚀 OpenRouter models successfully deployed to production!")

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
        logger.info("\n⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
