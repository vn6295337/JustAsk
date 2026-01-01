#!/usr/bin/env python3
"""
RLS Policy Verification Script
Tests that Row-Level Security policies are working correctly on v3 tables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env.local"
if env_path.exists():
    load_dotenv(env_path)

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env.local")
    print("Please add these values to test RLS policies")
    exit(1)

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase package not installed")
    print("Install with: pip install supabase")
    exit(1)

# Create Supabase client with ANON key (public access)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print("=" * 70)
print("RLS POLICY VERIFICATION TEST")
print("=" * 70)
print(f"Testing with anon key (public access)")
print(f"Supabase URL: {SUPABASE_URL}")
print("=" * 70)
print()

# Test 1: Read from ai_models_main (should SUCCEED - public read policy)
print("Test 1: SELECT from ai_models_main (should SUCCEED)")
print("-" * 70)
try:
    response = supabase.table("ai_models_main").select("human_readable_name, inference_provider").limit(5).execute()
    if response.data:
        print(f"✅ SUCCESS: Read {len(response.data)} records from ai_models_main")
        for record in response.data[:3]:
            print(f"   - {record.get('human_readable_name')} ({record.get('inference_provider')})")
    else:
        print("⚠️  No data returned (table might be empty)")
except Exception as e:
    print(f"❌ FAILED: {e}")
print()

# Test 2: Write to ai_models_main (should FAIL - anon has no write access)
print("Test 2: INSERT into ai_models_main (should FAIL)")
print("-" * 70)
try:
    response = supabase.table("ai_models_main").insert({
        "human_readable_name": "test-model-delete-me",
        "inference_provider": "Test"
    }).execute()
    print(f"❌ SECURITY ISSUE: Write succeeded when it should have failed!")
    print(f"   Response: {response.data}")
except Exception as e:
    if "policy" in str(e).lower() or "permission" in str(e).lower() or "denied" in str(e).lower():
        print(f"✅ SUCCESS: Write blocked by RLS policy")
        print(f"   Error: {e}")
    else:
        print(f"⚠️  Write failed but with unexpected error: {e}")
print()

# Test 3: Read from working_version (should FAIL - no public policy)
print("Test 3: SELECT from working_version (should FAIL - private table)")
print("-" * 70)
try:
    response = supabase.table("working_version").select("human_readable_name").limit(5).execute()
    if response.data:
        print(f"❌ SECURITY ISSUE: Read succeeded when it should have failed!")
        print(f"   Retrieved {len(response.data)} records")
    else:
        print("✅ SUCCESS: No data returned (RLS blocking access)")
except Exception as e:
    if "policy" in str(e).lower() or "permission" in str(e).lower() or "denied" in str(e).lower():
        print(f"✅ SUCCESS: Read blocked by RLS policy")
        print(f"   Error: {e}")
    else:
        print(f"⚠️  Read failed but with unexpected error: {e}")
print()

# Test 4: Write to working_version (should FAIL - anon has no access)
print("Test 4: INSERT into working_version (should FAIL)")
print("-" * 70)
try:
    response = supabase.table("working_version").insert({
        "human_readable_name": "test-model-delete-me",
        "inference_provider": "Test"
    }).execute()
    print(f"❌ SECURITY ISSUE: Write succeeded when it should have failed!")
except Exception as e:
    if "policy" in str(e).lower() or "permission" in str(e).lower() or "denied" in str(e).lower():
        print(f"✅ SUCCESS: Write blocked by RLS policy")
        print(f"   Error: {e}")
    else:
        print(f"⚠️  Write failed but with unexpected error: {e}")
print()

print("=" * 70)
print("RLS VERIFICATION COMPLETE")
print("=" * 70)
print("Expected results:")
print("  ✅ Test 1: Read ai_models_main - SUCCESS (public read allowed)")
print("  ✅ Test 2: Write ai_models_main - FAIL (anon cannot write)")
print("  ✅ Test 3: Read working_version - FAIL (private table)")
print("  ✅ Test 4: Write working_version - FAIL (anon cannot access)")
print("=" * 70)
