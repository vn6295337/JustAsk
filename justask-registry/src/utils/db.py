#!/usr/bin/env python3
"""
Database Utility Module for Pipeline Scripts
Provides PostgreSQL connection helpers for pipeline_writer role
"""

import os
import socket
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)



from urllib.parse import unquote, parse_qsl


def _resolve_ipv4(hostname: str) -> Optional[str]:
    """Resolve hostname to IPv4 address only (for GitHub Actions IPv6 compatibility).

    Args:
        hostname: The hostname to resolve

    Returns:
        IPv4 address string or None if resolution fails
    """
    try:
        # Get IPv4 addresses only (AF_INET)
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        if addr_info:
            # Return the first IPv4 address
            ipv4_addr = addr_info[0][4][0]
            print(f"[DB_UTILS] Resolved {hostname} to IPv4: {ipv4_addr}")
            return ipv4_addr
    except socket.gaierror as e:
        print(f"[DB_UTILS] Failed to resolve {hostname} to IPv4: {e}")
    return None


def _parse_postgres_url(url: str):
    """Parse PostgreSQL connection URI into connection kwargs.

    Returns a dict suitable for psycopg2.connect(**kwargs) or None if parsing fails."""
    if not url or '://' not in url:
        return None

    scheme, rest = url.split('://', 1)
    if scheme not in ('postgres', 'postgresql'):
        return None

    if '@' not in rest:
        return None

    user_part, host_part = rest.rsplit('@', 1)

    if ':' in user_part:
        user, password = user_part.split(':', 1)
    else:
        user, password = user_part, ''

    user = unquote(user)
    password = unquote(password)

    if '?' in host_part:
        host_main, query = host_part.split('?', 1)
    else:
        host_main, query = host_part, ''

    query_params = {}
    if query:
        for key, value in parse_qsl(query, keep_blank_values=True):
            if key:
                query_params[key] = unquote(value)

    if '/' in host_main:
        host_port, db_path = host_main.split('/', 1)
        dbname = unquote(db_path) if db_path else None
    else:
        host_port, dbname = host_main, None

    host = host_port
    port = None

    if host_port.startswith('['):
        # IPv6 literal like [::1]:5432
        if ']' in host_port:
            closing = host_port.find(']')
            host = host_port[1:closing]
            remainder = host_port[closing + 1:]
            if remainder.startswith(':'):
                port = remainder[1:]
    elif ':' in host_port:
        host, port = host_port.split(':', 1)

    host = unquote(host)
    if port:
        port = unquote(port)

    conn_kwargs = {}
    if user:
        conn_kwargs['user'] = user
    if password:
        conn_kwargs['password'] = password
    if host:
        conn_kwargs['host'] = host
    if port:
        conn_kwargs['port'] = port
    if dbname:
        # Strip additional path components if present
        dbname = dbname.split('/', 1)[0]
        if dbname:
            conn_kwargs['dbname'] = dbname

    # Merge query params (sslmode, options, etc.)
    for key, value in query_params.items():
        if value:
            conn_kwargs[key] = value

    return conn_kwargs if conn_kwargs else None


def get_pipeline_db_connection():
    """
    Create PostgreSQL connection using PIPELINE_SUPABASE_URL.

    Returns:
        connection: psycopg2 connection instance
        None: If connection fails
    """
    pipeline_url = os.getenv("PIPELINE_SUPABASE_URL")

    if not pipeline_url:
        logger.error("Missing required environment variable: PIPELINE_SUPABASE_URL")
        return None

    try:
        conn_kwargs = _parse_postgres_url(pipeline_url)
        if conn_kwargs:
            # Force IPv4 resolution for GitHub Actions compatibility
            if 'host' in conn_kwargs:
                original_host = conn_kwargs['host']
                ipv4_addr = _resolve_ipv4(original_host)
                if ipv4_addr:
                    # Use hostaddr for direct IPv4 connection while preserving host for SSL
                    conn_kwargs['hostaddr'] = ipv4_addr
                else:
                    print(f"[DB_UTILS] Warning: Could not resolve {original_host} to IPv4, attempting connection anyway")

            conn = psycopg2.connect(**conn_kwargs)
        else:
            conn = psycopg2.connect(pipeline_url)
        conn.autocommit = False  # Use transactions
        return conn
    except Exception as e:
        error_msg = f"Failed to connect to database: {str(e)}"
        logger.error(error_msg)
        print(f"[DB_UTILS ERROR] {error_msg}")  # Also print to stdout for visibility
        return None


def get_record_count(conn, table_name: str, inference_provider: str) -> Optional[int]:
    """Get count of records for a specific inference provider."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE inference_provider = %s",
                (inference_provider,)
            )
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Failed to count records: {str(e)}")
        return None


def backup_records(conn, table_name: str, inference_provider: str) -> Optional[List[Dict[str, Any]]]:
    """Backup all records for a specific inference provider."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {table_name} WHERE inference_provider = %s",
                (inference_provider,)
            )
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Failed to backup records: {str(e)}")
        return None


def delete_records(conn, table_name: str, inference_provider: str) -> bool:
    """Delete all records for a specific inference provider."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {table_name} WHERE inference_provider = %s",
                (inference_provider,)
            )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to delete records: {str(e)}")
        conn.rollback()
        return False


def insert_records_batch(conn, table_name: str, records: List[Dict[str, Any]], batch_size: int = 100) -> bool:
    """
    Insert records in batches.

    Args:
        conn: Database connection
        table_name: Target table
        records: List of dictionaries with column:value pairs
        batch_size: Number of records per batch

    Returns:
        bool: True if successful
    """
    if not records:
        return True

    try:
        # Get column names from first record
        columns = list(records[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)

        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # Convert records to tuples
        values = [tuple(record[col] for col in columns) for record in records]

        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, values, page_size=batch_size)

        conn.commit()
        return True

    except Exception as e:
        logger.error(f"Failed to insert records: {str(e)}")
        conn.rollback()
        return False


def load_staging_data(conn, staging_table: str, inference_provider: str) -> Optional[List[Dict[str, Any]]]:
    """Load data from staging table for specific provider."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {staging_table} WHERE inference_provider = %s",
                (inference_provider,)
            )
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Failed to load staging data: {str(e)}")
        return None


def delete_rate_limits(conn, table_name: str, inference_provider: str) -> bool:
    """Delete all rate limit records for a specific inference provider.

    Args:
        table_name: Fully qualified table name (e.g., 'ims."30_rate_limits"')
    """
    try:
        with conn.cursor() as cur:
            query = f'DELETE FROM {table_name} WHERE inference_provider = %s'
            logger.info(f"Executing: {query} with provider={inference_provider}")
            cur.execute(query, (inference_provider,))
            deleted_count = cur.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_count} rate limit records for {inference_provider}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete rate limits: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        conn.rollback()
        return False


def upsert_rate_limits(conn, table_name: str, rate_limit_records: List[Dict[str, Any]]) -> bool:
    """
    Upsert rate limit records using ON CONFLICT strategy.

    Args:
        conn: Database connection
        table_name: Fully qualified table name (e.g., 'ims."30_rate_limits"')
        rate_limit_records: List of dictionaries with rate limit data

    Returns:
        bool: True if successful
    """
    if not rate_limit_records:
        logger.warning("No rate limit records to upsert")
        return True

    try:
        logger.info(f"Upserting {len(rate_limit_records)} rate limit records to {table_name}")
        logger.info(f"Sample record: {rate_limit_records[0]}")

        # Define columns for rate limits table
        columns = ['human_readable_name', 'inference_provider', 'rpm', 'rpd', 'tpm', 'tpd', 'raw_string', 'parseable']
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)

        # ON CONFLICT clause for upsert
        update_columns = ['rpm', 'rpd', 'tpm', 'tpd', 'raw_string', 'parseable', 'updated_at']
        update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns[:-1]])
        update_str += ', updated_at = CURRENT_TIMESTAMP'

        upsert_sql = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (human_readable_name)
            DO UPDATE SET {update_str}
        """

        logger.info(f"SQL: {upsert_sql}")

        # Convert records to tuples
        values = [tuple(record.get(col) for col in columns) for record in rate_limit_records]

        with conn.cursor() as cur:
            execute_batch(cur, upsert_sql, values, page_size=100)

        conn.commit()
        logger.info(f"Successfully upserted {len(rate_limit_records)} rate limit records")
        return True

    except Exception as e:
        logger.error(f"Failed to upsert rate limits: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        conn.rollback()
        return False
