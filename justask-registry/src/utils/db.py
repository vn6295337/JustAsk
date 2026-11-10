#!/usr/bin/env python3
"""
Database Utility Module for Pipeline Scripts
Provides PostgreSQL connection helpers for pipeline_writer role
"""

import os
import re
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


_IDENT_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _check_ident(name: str) -> str:
    """Validate a SQL identifier (column name); raise ValueError otherwise."""
    if not isinstance(name, str) or not _IDENT_RE.match(name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return name


def _check_table(name: str) -> str:
    """Validate a (optionally schema-qualified / quoted) table name."""
    if not isinstance(name, str) or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*(\.("[A-Za-z0-9_]+"|[A-Za-z_][A-Za-z0-9_]*))?$', name):
        raise ValueError(f"Unsafe SQL table name: {name!r}")
    return name


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


def delete_records(conn, table_name: str, inference_provider: str, commit: bool = True) -> bool:
    """Delete all records for a specific inference provider."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {table_name} WHERE inference_provider = %s",
                (inference_provider,)
            )
        if commit:
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to delete records: {str(e)}")
        conn.rollback()
        return False


def insert_records_batch(conn, table_name: str, records: List[Dict[str, Any]], batch_size: int = 100, commit: bool = True) -> bool:
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
        columns = [_check_ident(c) for c in records[0].keys()]
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)

        _check_table(table_name)
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # Convert records to tuples
        values = [tuple(record.get(col) for col in columns) for record in records]

        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, values, page_size=batch_size)

        if commit:
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


def delete_rate_limits(conn, table_name: str, inference_provider: str, commit: bool = True) -> bool:
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
        if commit:
            conn.commit()
        logger.info(f"Deleted {deleted_count} rate limit records for {inference_provider}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete rate limits: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        conn.rollback()
        return False


def upsert_rate_limits(conn, table_name: str, rate_limit_records: List[Dict[str, Any]], commit: bool = True) -> bool:
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

        if commit:
            conn.commit()
        logger.info(f"Successfully upserted {len(rate_limit_records)} rate limit records")
        return True

    except Exception as e:
        logger.error(f"Failed to upsert rate limits: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        conn.rollback()
        return False


def replace_provider_records_atomic(
    conn,
    table_name: str,
    inference_provider: str,
    records: List[Dict[str, Any]],
    tolerance: int = 0,
    rate_limit_table: Optional[str] = None,
    rate_limit_records: Optional[List[Dict[str, Any]]] = None,
    batch_size: int = 100,
) -> bool:
    """Replace all rows of a provider in ONE transaction: delete + insert (+ rate
    limits) + verify. Commits only if every step succeeded; otherwise rolls back,
    leaving the previous rows untouched (no in-memory backup/restore needed).

    Args:
        tolerance: allowed abs difference between inserted and counted rows.
        rate_limit_table / rate_limit_records: if both given, provider rate limits
            are deleted and re-upserted inside the same transaction.
    """
    if not records:
        logger.error("Refusing to replace provider records with an empty set")
        return False
    try:
        if not delete_records(conn, table_name, inference_provider, commit=False):
            conn.rollback()
            return False
        if not insert_records_batch(conn, table_name, records, batch_size=batch_size, commit=False):
            conn.rollback()
            return False
        if rate_limit_table and rate_limit_records:
            if not delete_rate_limits(conn, rate_limit_table, inference_provider, commit=False):
                conn.rollback()
                return False
            if not upsert_rate_limits(conn, rate_limit_table, rate_limit_records, commit=False):
                conn.rollback()
                return False
        final_count = get_record_count(conn, table_name, inference_provider)
        if final_count is None or abs(final_count - len(records)) > tolerance:
            logger.error(f"Verification failed: expected {len(records)}, found {final_count}; rolling back")
            conn.rollback()
            return False
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Atomic replace failed, rolled back: {str(e)}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
