#!/usr/bin/env python3
"""
Test pipeline_writer role access to v3 tables
Verifies that Claude Code can read/write using PIPELINE_SUPABASE_URL
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# Import database utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
try:
    from src.utils.db import get_pipeline_db_connection
except ImportError:
    get_pipeline_db_connection = None

# Load environment variables
env_path = Path(__file__).parent / ".env.local"
if env_path.exists():
    load_dotenv(env_path)

PIPELINE_URL = os.getenv("PIPELINE_SUPABASE_URL")

if not PIPELINE_URL:
    print("❌ Missing PIPELINE_SUPABASE_URL in .env.local")
    exit(1)

print("=" * 70)
print("PIPELINE_WRITER ACCESS VERIFICATION")
print("=" * 70)
print(f"Testing with pipeline_writer role")
print("=" * 70)
print()

conn = None

try:
    if get_pipeline_db_connection is None:
        print("❌ db_utils not available - cannot create database connection")
        exit(1)

    conn = get_pipeline_db_connection()
    if not conn:
        print("❌ Failed to initialize database connection using PIPELINE_SUPABASE_URL")
        exit(1)

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Test 1: Read from ai_models_main_v3
    print("Test 1: SELECT from ai_models_main_v3")
    print("-" * 70)
    cursor.execute("SELECT human_readable_name, inference_provider FROM ai_models_main_v3 LIMIT 3")
    rows = cursor.fetchall()
    print(f"✅ SUCCESS: Read {len(rows)} records")
    for row in rows:
        print(f"   - {row['human_readable_name']} ({row['inference_provider']})")
    print()

    # Test 2: Read from working_version_v3
    print("Test 2: SELECT from working_version_v3 (private table)")
    print("-" * 70)
    cursor.execute("SELECT human_readable_name, inference_provider FROM working_version_v3 LIMIT 3")
    rows = cursor.fetchall()
    print(f"✅ SUCCESS: Read {len(rows)} records from private table")
    for row in rows:
        print(f"   - {row['human_readable_name']} ({row['inference_provider']})")
    print()

    # Test 3: Insert into ai_models_main_v3
    print("Test 3: INSERT into ai_models_main_v3")
    print("-" * 70)
    cursor.execute("""
        INSERT INTO ai_models_main_v3
        (inference_provider, human_readable_name, model_provider)
        VALUES ('Test', 'Claude Code Test Model', 'Test Provider')
        RETURNING id, human_readable_name
    """)
    inserted = cursor.fetchone()
    print(f"✅ SUCCESS: Inserted record with id={inserted['id']}")
    print(f"   Model: {inserted['human_readable_name']}")

    # Clean up - delete the test record
    cursor.execute("DELETE FROM ai_models_main_v3 WHERE id = %s", (inserted['id'],))
    print(f"✅ Cleanup: Deleted test record")
    print()

    # Test 4: Insert into working_version_v3
    print("Test 4: INSERT into working_version_v3 (private table)")
    print("-" * 70)
    cursor.execute("""
        INSERT INTO working_version_v3
        (inference_provider, human_readable_name, model_provider)
        VALUES ('Test', 'Claude Code Test Staging', 'Test Provider')
        RETURNING id, human_readable_name
    """)
    inserted = cursor.fetchone()
    print(f"✅ SUCCESS: Inserted record with id={inserted['id']}")
    print(f"   Model: {inserted['human_readable_name']}")

    # Clean up - delete the test record
    cursor.execute("DELETE FROM working_version_v3 WHERE id = %s", (inserted['id'],))
    print(f"✅ Cleanup: Deleted test record")
    print()

    # Test 5: Count records per provider
    print("Test 5: Query record counts by provider")
    print("-" * 70)
    cursor.execute("""
        SELECT inference_provider, COUNT(*) as count
        FROM ai_models_main_v3
        GROUP BY inference_provider
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()
    print(f"✅ SUCCESS: Retrieved statistics")
    for row in rows:
        print(f"   - {row['inference_provider']}: {row['count']} models")
    print()

    conn.commit()
    cursor.close()
    conn.close()

    print("=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print("pipeline_writer role has full access to:")
    print("  ✅ ai_models_main_v3 (read/write)")
    print("  ✅ working_version_v3 (read/write)")
    print("=" * 70)

except Exception as e:
    print(f"❌ FAILED: {e}")
    if conn:
        conn.rollback()
        conn.close()
    exit(1)
