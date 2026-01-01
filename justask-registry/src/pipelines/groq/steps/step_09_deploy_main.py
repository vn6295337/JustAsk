#!/usr/bin/env python3

"""
Production Deployment Script: Groq Data Migration - PostgreSQL Version
==============================================

This script deploys Groq data from working_version to ai_models_main by:
1. Backing up existing Groq records from ai_models_main
2. Deleting existing Groq records from ai_models_main
3. Copying Groq data from working_version to ai_models_main

Features:
- Direct PostgreSQL connection with pipeline_writer role
- Complete rollback protection with backup/restore
- Bulk operations with transactions
- Comprehensive error handling and logging

Author: AI Models Discovery Pipeline
Version: 2.0 (PostgreSQL + RLS)
Last Updated: 2025-12-03
"""

import os
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
    get_record_count,
    backup_records,
    delete_records,
    insert_records_batch,
    load_staging_data,
)
set_current_pipeline('groq')

# Path resolution
PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config" / "groq"

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
LOG_FILE = get_output_file_path('09_deploy_main_report.txt')

# Database configuration
STAGING_TABLE = "working_version"
PRODUCTION_TABLE = "ai_models_main"
INFERENCE_PROVIDER = "Groq"

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

    for model in staging_data:
        # Remove auto-managed fields
        clean_model = {k: v for k, v in model.items() if k not in auto_managed_fields}

        # Convert empty strings to None for nullable fields
        nullable_fields = ['license_info_text', 'license_info_url']
        for field in nullable_fields:
            if field in clean_model and clean_model[field] is not None and not str(clean_model[field]).strip():
                clean_model[field] = None

        prepared_models.append(clean_model)

    logger.info(f"✅ Prepared {len(prepared_models)} models for production deployment")
    return prepared_models


def restore_production_backup(conn, backup_data: List[Dict[str, Any]]) -> bool:
    """Restore backed up records to production (rollback operation)."""
    logger.info(f"🔄 Rolling back: Restoring {len(backup_data)} Groq records to production...")

    if not backup_data:
        logger.info("✅ No production data to restore")
        return True

    # Remove auto-managed fields
    auto_managed_fields = ['id', 'created_at', 'updated_at']
    clean_backup = [{k: v for k, v in record.items() if k not in auto_managed_fields}
                    for record in backup_data]

    logger.info(f"   Prepared {len(clean_backup)} records for restoration")

    # Use batch insert
    if insert_records_batch(conn, PRODUCTION_TABLE, clean_backup, batch_size=50):
        final_count = get_record_count(conn, PRODUCTION_TABLE, INFERENCE_PROVIDER)
        logger.info(f"✅ Rollback successful: {final_count} Groq records restored to production")
        return True
    else:
        logger.error(f"❌ Rollback failed")
        return False


def main():
    """Main orchestration function for production deployment."""
    logger.info("=" * 70)
    logger.info("GROQ PRODUCTION DEPLOYMENT STARTED")
    logger.info("=" * 70)
    start_time = datetime.now()
    conn = None
    backup_data = None

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
            logger.error("❌ DEPLOYMENT FAILED: No Groq data in staging table")
            return False

        # Step 3: Load staging data
        logger.info(f"📁 Loading Groq data from {STAGING_TABLE}...")
        staging_data = load_staging_data(conn, STAGING_TABLE, INFERENCE_PROVIDER)
        if not staging_data:
            logger.error("❌ DEPLOYMENT FAILED: Could not load staging data")
            return False

        logger.info(f"✅ Loaded {len(staging_data)} Groq records from staging")

        # Step 4: Prepare data for production
        prepared_data = prepare_data_for_production(staging_data)
        if not prepared_data:
            logger.error("❌ DEPLOYMENT FAILED: No valid data to deploy")
            return False

        # Step 5: Backup existing production data
        logger.info("🛡️ CREATING PRODUCTION BACKUP FOR ROLLBACK PROTECTION...")
        backup_data = backup_records(conn, PRODUCTION_TABLE, INFERENCE_PROVIDER)
        if backup_data is None:
            logger.error("❌ DEPLOYMENT FAILED: Could not backup production data - ABORTING")
            return False

        logger.info(f"✅ Backed up {len(backup_data)} existing Groq records from production")

        # Step 6: Delete existing production data
        logger.info(f"🗑️ Deleting existing Groq records from {PRODUCTION_TABLE}...")
        if not delete_records(conn, PRODUCTION_TABLE, INFERENCE_PROVIDER):
            logger.error("❌ DEPLOYMENT FAILED: Could not delete existing production data")
            return False

        logger.info(f"✅ Successfully deleted {production_count} Groq records from production")

        # Step 7: Deploy new data
        logger.info(f"🚀 Deploying {len(prepared_data)} models to production ({PRODUCTION_TABLE})...")
        if not insert_records_batch(conn, PRODUCTION_TABLE, prepared_data, batch_size=100):
            logger.error("❌ DEPLOYMENT FAILED: Data deployment failed - INITIATING ROLLBACK")
            if restore_production_backup(conn, backup_data):
                logger.info("✅ ROLLBACK SUCCESSFUL: Original production data restored")
            else:
                logger.error("❌ ROLLBACK FAILED: Manual intervention required!")
            return False

        logger.info(f"✅ Successfully deployed {len(prepared_data)} models to production")

        # Step 8: Verify deployment
        logger.info("🔍 Verifying production deployment results...")
        final_count = get_record_count(conn, PRODUCTION_TABLE, INFERENCE_PROVIDER)

        tolerance = max(1, int(len(prepared_data) * 0.05))  # 5% tolerance
        if abs(final_count - len(prepared_data)) > tolerance:
            logger.error(f"❌ Verification failed: Expected ~{len(prepared_data)}, found {final_count}")
            logger.error("❌ DEPLOYMENT FAILED: Verification failed - INITIATING ROLLBACK")
            if restore_production_backup(conn, backup_data):
                logger.info("✅ ROLLBACK SUCCESSFUL: Original production data restored")
            else:
                logger.error("❌ ROLLBACK FAILED: Manual intervention required!")
            return False

        # Success
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("=" * 70)
        logger.info("🎉 GROQ PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"📊 Deployment Summary:")
        logger.info(f"   • Staging records processed: {len(staging_data)}")
        logger.info(f"   • Production records backed up: {len(backup_data)}")
        logger.info(f"   • Production records deleted: {production_count}")
        logger.info(f"   • New records deployed: {len(prepared_data)}")
        logger.info(f"   • Final production count: {final_count}")
        logger.info(f"   • Deployment time: {duration}")
        logger.info(f"   • Log file: {LOG_FILE}")
        logger.info("=" * 70)
        logger.info("🚀 Groq models successfully deployed to production!")

        return True

    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR: {str(e)}")
        if backup_data and conn:
            logger.info("🔄 Attempting emergency rollback...")
            if restore_production_backup(conn, backup_data):
                logger.info("✅ EMERGENCY ROLLBACK SUCCESSFUL")
            else:
                logger.error("❌ EMERGENCY ROLLBACK FAILED")
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
