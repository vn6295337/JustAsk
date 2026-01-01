"""
Shared utilities for AI Models Discoverer pipelines.

This module consolidates utilities from all pipelines:
- Database operations (db.py)
- API key management (key_client.py)
- Output file handling (output.py)
- Configuration management (config_manager.py)
- Environment management (env_manager.py)
- Path management (path_manager.py)
- Rate limit parsing (rate_limit_parser.py)
- Model-AA mapping (model_aa_mapping.py)
- Groq-specific utilities (groq_web_scraper.py, groq_data_processor.py)
"""

from .db import (
    get_pipeline_db_connection,
    get_record_count,
    backup_records,
    delete_records,
    insert_records_batch,
    load_staging_data,
    delete_rate_limits,
    upsert_rate_limits,
)

from .key_client import (
    KeyClient,
    get_api_key,
    log_usage,
    get_notifications,
)

from .output import (
    set_current_pipeline,
    get_current_pipeline,
    get_project_root,
    get_output_dir,
    get_output_file_path,
    get_input_file_path,
    ensure_output_directory,
    ensure_output_dir_exists,  # Alias for backward compatibility
    clean_output_directory,
    get_ist_timestamp,
)

from .rate_limit_parser import parse_rate_limits

from .groq_web_scraper import GroqWebScraper

from .groq_data_processor import GroqDataProcessor

__all__ = [
    # Database utilities
    'get_pipeline_db_connection',
    'get_record_count',
    'backup_records',
    'delete_records',
    'insert_records_batch',
    'load_staging_data',
    'delete_rate_limits',
    'upsert_rate_limits',
    # Key client utilities
    'KeyClient',
    'get_api_key',
    'log_usage',
    'get_notifications',
    # Output utilities
    'set_current_pipeline',
    'get_current_pipeline',
    'get_project_root',
    'get_output_dir',
    'get_output_file_path',
    'get_input_file_path',
    'ensure_output_directory',
    'ensure_output_dir_exists',
    'clean_output_directory',
    'get_ist_timestamp',
    # Rate limit parser
    'parse_rate_limits',
    # Groq utilities
    'GroqWebScraper',
    'GroqDataProcessor',
]
