#!/usr/bin/env python3
"""
Refresh AA Performance Metrics Table (justask."20_router-benchmark-scores")

Fetches latest model performance data from the Artificial Analysis API
(Free endpoint: /api/v2/language/models/free) and updates the justask."20_router-benchmark-scores" table in Supabase.

This script runs daily via GitHub Actions at 00:00 UTC.
"""

import os
import sys
import requests
import psycopg2
from datetime import datetime
from typing import List, Dict, Optional

# API Configuration
AA_API_BASE_URL = "https://artificialanalysis.ai/api/v2"
AA_API_KEY = os.getenv("ARTIFICIALANALYSIS_API_KEY")
PIPELINE_SUPABASE_URL = os.getenv("PIPELINE_SUPABASE_URL")

# Sanity limits: refuse to replace the table with a truncated/empty API result
MIN_RECORDS = int(os.getenv("AA_MIN_RECORDS", "50"))
MIN_RATIO_OF_EXISTING = float(os.getenv("AA_MIN_RATIO_OF_EXISTING", "0.5"))
MAX_PAGES = 20  # safety cap for pagination

# Columns written by this script (one per AA Free-tier field); must match the transform's record keys
DB_COLUMNS = [
    "aa_model_id", "aa_slug", "name", "release_date", "creator_id", "creator_name",
    "intelligence_index_version", "intelligence_index", "coding_index", "agentic_index",
    "finance_and_accounting_index", "strategy_and_ops_index", "legal_index",
    "healthcare_and_medical_index", "engineering_index", "economics_index",
    "intelligence_index_cost_total", "intelligence_index_cost_per_task",
    "price_1m_input_tokens", "price_1m_output_tokens",
    "price_1m_cache_hit_tokens", "price_1m_cache_write_tokens",
    "mean_output_tokens_per_second", "mean_time_to_first_token_seconds",
    "mean_time_to_first_answer_token_seconds",
]

def log(message: str):
    """Print timestamped log message"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] {message}")

def fetch_aa_performance_data() -> List[Dict]:
    """
    Fetch language model data from the Artificial Analysis Free endpoint.

    The legacy /api/v2/data/llms/models endpoint was retired on 2026-11-04 (HTTP 410).
    Replacement: GET /api/v2/language/models/free (paginated, x-api-key header).
    Free-tier quota: 100 requests per 24-hour window; one refresh uses ~2-3 pages.

    Returns:
        List of model dictionaries (Free-shape)
    """
    log("Fetching data from Artificial Analysis API...")

    if not AA_API_KEY or AA_API_KEY == "your-api-key-here":
        raise ValueError("ARTIFICIALANALYSIS_API_KEY not configured")

    url = f"{AA_API_BASE_URL}/language/models/free"
    headers = {
        "x-api-key": AA_API_KEY,
        "Accept": "application/json"
    }

    models: List[Dict] = []
    page = 1
    while True:
        if page > MAX_PAGES:
            raise Exception(f"Pagination did not finish within {MAX_PAGES} pages; aborting")

        response = requests.get(url, headers=headers, params={"page": page}, timeout=30)
        if not response.ok:
            raise Exception(f"API request failed (page {page}): {response.status_code} - {response.text[:500]}")

        data = response.json()
        batch = data.get("data")
        if not isinstance(batch, list):
            raise Exception(f"Invalid API response format (page {page})")

        if page == 1:
            log(f"Tier: {data.get('tier')} | Intelligence Index version: {data.get('intelligence_index_version')}")
        # intelligence_index_version is response-level; keep it with each model of this page
        for m in batch:
            if isinstance(m, dict):
                m["_intelligence_index_version"] = data.get("intelligence_index_version")
        models.extend(batch)

        pagination = data.get("pagination") or {}
        log(f"Page {page}/{pagination.get('total_pages', '?')}: {len(batch)} models")
        if not pagination.get("has_more"):
            break
        page += 1

    rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
    if rate_limit_remaining:
        log(f"Rate limit: {rate_limit_remaining} requests remaining in the current window")

    log(f"Fetched {len(models)} models from API")
    return models

def transform_to_db_format(api_data: List[Dict]) -> List[Dict]:
    """
    Transform Free-shape API data to the justask."20_router-benchmark-scores" schema.

    One column per Free-tier field (AA leaf names without the "artificial_analysis_" prefix).
    - coding_index and agentic_index: AA no longer publishes them (always null); kept to match the API.
    - Speed comes from performance_v3 (means); the old "performance" medians are null from 2026-12-10.
    - Per-benchmark scores, creator slug and blended price are Pro-only and not stored.

    Args:
        api_data: Raw data from Artificial Analysis API

    Returns:
        List of dictionaries matching database schema
    """
    log("Transforming data to database format...")

    records = []

    for model in api_data:
        evaluations = model.get("evaluations") or {}
        pricing = model.get("pricing") or {}
        creator = model.get("model_creator") or {}
        performance_v3 = model.get("performance_v3") or {}
        index_cost = model.get("artificial_analysis_intelligence_index_cost") or {}
        cost_per_task = index_cost.get("cost_per_task") or {}

        # Extract intelligence index (primary metric)
        intelligence_index = evaluations.get("artificial_analysis_intelligence_index")

        # Skip models without intelligence index or slug (slug is the join key)
        if intelligence_index is None or not model.get("slug"):
            continue

        record = {
            "aa_model_id": model.get("id"),
            "aa_slug": model.get("slug"),
            "name": model.get("name"),
            "release_date": model.get("release_date"),
            "creator_id": creator.get("id"),
            "creator_name": creator.get("name"),

            # Evaluations
            "intelligence_index_version": model.get("_intelligence_index_version"),
            "intelligence_index": intelligence_index,
            "coding_index": evaluations.get("artificial_analysis_coding_index"),
            "agentic_index": evaluations.get("artificial_analysis_agentic_index"),
            "finance_and_accounting_index": evaluations.get("artificial_analysis_finance_and_accounting_index"),
            "strategy_and_ops_index": evaluations.get("artificial_analysis_strategy_and_ops_index"),
            "legal_index": evaluations.get("artificial_analysis_legal_index"),
            "healthcare_and_medical_index": evaluations.get("artificial_analysis_healthcare_and_medical_index"),
            "engineering_index": evaluations.get("artificial_analysis_engineering_index"),
            "economics_index": evaluations.get("artificial_analysis_economics_index"),

            # Cost to run the Intelligence Index (USD)
            "intelligence_index_cost_total": index_cost.get("total_cost"),
            "intelligence_index_cost_per_task": cost_per_task.get("total_cost"),

            # Pricing (per 1M tokens)
            "price_1m_input_tokens": pricing.get("price_1m_input_tokens"),
            "price_1m_output_tokens": pricing.get("price_1m_output_tokens"),
            "price_1m_cache_hit_tokens": pricing.get("price_1m_cache_hit_tokens"),
            "price_1m_cache_write_tokens": pricing.get("price_1m_cache_write_tokens"),

            # Speed (performance_v3 headline means)
            "mean_output_tokens_per_second": performance_v3.get("mean_output_tokens_per_second"),
            "mean_time_to_first_token_seconds": performance_v3.get("mean_time_to_first_token_seconds"),
            "mean_time_to_first_answer_token_seconds": performance_v3.get("mean_time_to_first_answer_token_seconds"),
        }

        records.append(record)

    log(f"Transformed {len(records)} records (filtered out {len(api_data) - len(records)} without intelligence index or slug)")

    return records

def refresh_database_table(records: List[Dict]):
    """
    Refresh the justask."20_router-benchmark-scores" table

    Strategy: DELETE + INSERT in one transaction.
    A failure rolls back to the original rows, so no backup table is needed
    (and the CI role needs no CREATE privilege on schema ims).

    Args:
        records: List of dictionaries to insert
    """
    log("Connecting to Supabase PostgreSQL...")

    if not PIPELINE_SUPABASE_URL:
        raise ValueError("PIPELINE_SUPABASE_URL not configured")

    conn = psycopg2.connect(PIPELINE_SUPABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Sanity check against the current table BEFORE touching anything
        cur.execute('SELECT COUNT(*) FROM justask."20_router-benchmark-scores";')
        existing_count = cur.fetchone()[0]
        log(f"Existing records: {existing_count}")

        if existing_count > 0 and len(records) < existing_count * MIN_RATIO_OF_EXISTING:
            raise ValueError(
                f"Refusing to replace {existing_count} existing records with only "
                f"{len(records)} (< {MIN_RATIO_OF_EXISTING:.0%}); aborting without changes"
            )

        # Diagnostic only: do the mapped slugs (21_router-model-benchmark-map) still exist in the new data?
        # The API migration could have changed slugs; a low match rate means the
        # mapping needs a refresh before the next ranking run.
        cur.execute("SAVEPOINT slug_check;")
        try:
            cur.execute('SELECT DISTINCT aa_slug FROM justask."21_router-model-benchmark-map" WHERE aa_slug IS NOT NULL;')
            mapped = {row[0] for row in cur.fetchall()}
            new_slugs = {r["aa_slug"] for r in records}
            if mapped:
                matched = len(mapped & new_slugs)
                log(f"Mapped slugs found in new data: {matched}/{len(mapped)}")
                if matched < len(mapped):
                    log(f"⚠️  Missing mapped slugs (sample): {sorted(mapped - new_slugs)[:10]}")
            cur.execute("RELEASE SAVEPOINT slug_check;")
        except Exception as e:
            cur.execute("ROLLBACK TO SAVEPOINT slug_check;")
            log(f"Slug check skipped: {e}")

        # Step 1: Delete all existing records (same transaction as the insert)
        log("Deleting existing records...")
        cur.execute('DELETE FROM justask."20_router-benchmark-scores";')
        log(f"Deleted {cur.rowcount} records")

        # Step 2: Insert new records
        log(f"Inserting {len(records)} new records...")

        insert_sql = (
            'INSERT INTO justask."20_router-benchmark-scores" ('
            + ", ".join(DB_COLUMNS)
            + ") VALUES ("
            + ", ".join(f"%({c})s" for c in DB_COLUMNS)
            + ")"
        )

        cur.executemany(insert_sql, records)

        # executemany().rowcount is unreliable; verify with a count
        cur.execute('SELECT COUNT(*) FROM justask."20_router-benchmark-scores";')
        inserted_count = cur.fetchone()[0]
        if inserted_count != len(records):
            raise RuntimeError(f"Insert verification failed: expected {len(records)}, found {inserted_count}")
        log(f"Inserted {inserted_count} records")

        # Step 3: Commit
        conn.commit()
        log("Transaction committed successfully")

        log("✅ Refresh completed successfully")

    except Exception as e:
        log(f"❌ Error during refresh: {e}")
        log("Rolling back transaction (existing data is left unchanged)...")
        # Delete and insert ran in one transaction, so rollback restores the original rows.
        conn.rollback()

        raise

    finally:
        cur.close()
        conn.close()
        log("Database connection closed")

def main():
    """Main execution flow"""
    try:
        log("=" * 80)
        log("AA PERFORMANCE METRICS REFRESH - STARTING")
        log("=" * 80)

        # Step 1: Fetch data from API
        api_data = fetch_aa_performance_data()

        # Step 2: Transform to database format
        db_records = transform_to_db_format(api_data)

        if len(db_records) < MIN_RECORDS:
            raise ValueError(
                f"Only {len(db_records)} usable records (minimum {MIN_RECORDS}); "
                "aborting without modifying the table"
            )

        # Step 3: Refresh database table
        refresh_database_table(db_records)

        log("=" * 80)
        log("✅ REFRESH COMPLETED SUCCESSFULLY")
        log(f"   Total models processed: {len(api_data)}")
        log(f"   Records inserted: {len(db_records)}")
        log("=" * 80)

    except Exception as e:
        log("=" * 80)
        log(f"❌ REFRESH FAILED: {e}")
        log("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    main()
