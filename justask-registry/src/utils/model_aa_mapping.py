#!/usr/bin/env python3
"""
Shared Model-to-AA Mapping Utilities
=====================================

Single source of truth for refreshing ims.10_model_aa_mapping table.
Used by all pipeline working_version refresh scripts.

Purpose:
- Maps (inference_provider, provider_slug) from working_version to aa_slug
- Uses UPSERT pattern with ON CONFLICT for safe, idempotent updates
- Provides enhanced error reporting for unmatched models

Author: AI Models Discovery Pipeline
Version: 3.0 (Unified)
Last Updated: 2025-12-04
"""

import sys
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import logging

try:
    import psycopg2
    from psycopg2.extras import execute_values
    import re
    from difflib import SequenceMatcher
except ImportError:
    print("Error: psycopg2 package not found. Install with: pip install psycopg2-binary")
    sys.exit(1)


def normalize_slug(slug: str) -> str:
    """
    Normalize provider_slug to match aa_slug format.

    Converts special characters (periods, spaces, underscores) to hyphens
    to maintain consistency with aa_slug naming convention.
    Also strips common suffixes like -it, -instruct, -chat.

    Examples:
        "gpt-4.0" -> "gpt-4-0"
        "llama 3.1" -> "llama-3-1"
        "model_name_v2" -> "model-name-v2"
        "gemma-3-12b-it" -> "gemma-3-12b"

    Args:
        slug: Original provider_slug from working_version

    Returns:
        Normalized slug with special characters converted to hyphens
    """
    if not slug:
        return slug

    # Replace periods, spaces, and underscores with hyphens
    normalized = re.sub(r'[.\s_]+', '-', slug)

    # Remove consecutive hyphens
    normalized = re.sub(r'-+', '-', normalized)

    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')

    # Convert to lowercase for consistency
    normalized = normalized.lower()

    # Strip common model suffixes for better matching
    # Order matters: strip longer suffixes first
    suffixes_to_strip = [
        '-instruct',
        '-chat',
        '-it',
        '-turbo',
        '-preview',
        '-exp'
    ]
    for suffix in suffixes_to_strip:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            break  # Only strip one suffix

    return normalized


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity ratio between two strings using SequenceMatcher.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity ratio between 0.0 and 1.0 (1.0 = identical)
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def find_nearest_aa_slugs(
    provider_slug: str,
    aa_slugs: List[str],
    top_n: int = 5
) -> List[Tuple[str, float]]:
    """
    Find the top N nearest aa_slugs for a given provider_slug using similarity scoring.

    Args:
        provider_slug: The provider slug to match
        aa_slugs: List of available aa_slug values
        top_n: Number of top matches to return (default: 5)

    Returns:
        List of (aa_slug, similarity_score) tuples, sorted by similarity (highest first)
    """
    # Normalize provider_slug for comparison
    normalized_provider = normalize_slug(provider_slug)

    # Calculate similarity scores for all aa_slugs
    similarities = []
    for aa_slug in aa_slugs:
        score = calculate_similarity(normalized_provider, aa_slug)
        similarities.append((aa_slug, score))

    # Sort by similarity score (descending) and return top N
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]


def fetch_working_version_models(
    conn,
    inference_provider: Optional[str] = None
) -> List[Tuple[str, str]]:
    """
    Fetch all unique (inference_provider, provider_slug) pairs from working_version.

    Args:
        conn: Database connection
        inference_provider: Optional filter for specific provider

    Returns:
        List of (inference_provider, provider_slug) tuples
    """
    try:
        with conn.cursor() as cur:
            if inference_provider:
                cur.execute("""
                    SELECT DISTINCT
                        inference_provider,
                        provider_slug
                    FROM public.working_version
                    WHERE provider_slug IS NOT NULL
                      AND provider_slug != ''
                      AND inference_provider = %s
                    ORDER BY inference_provider, provider_slug
                """, (inference_provider,))
            else:
                cur.execute("""
                    SELECT DISTINCT
                        inference_provider,
                        provider_slug
                    FROM public.working_version
                    WHERE provider_slug IS NOT NULL
                      AND provider_slug != ''
                    ORDER BY inference_provider, provider_slug
                """)

            models = cur.fetchall()
            return models
    except Exception as e:
        print(f"ERROR: Failed to fetch working_version models: {e}")
        return []


def fetch_aa_performance_slugs(conn) -> List[str]:
    """
    Fetch all unique aa_slug values from ims.20_aa_performance_metrics.

    Args:
        conn: Database connection

    Returns:
        List of aa_slug strings
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT aa_slug
                FROM ims."20_aa_performance_metrics"
                ORDER BY aa_slug
            """)
            aa_slugs = [row[0] for row in cur.fetchall()]
            return aa_slugs
    except Exception as e:
        print(f"ERROR: Failed to fetch AA performance slugs: {e}")
        return []


def match_provider_slug_to_aa_slug(
    provider_slug: str,
    inference_provider: str,
    aa_slugs: List[str]
) -> Optional[str]:
    """
    Attempt to match provider_slug to aa_slug using multiple strategies.

    Normalizes provider_slug first to match aa_slug format (converts special
    characters like periods, spaces, underscores to hyphens).

    Matching strategies (in order):
    1. Exact match: normalized_provider_slug == aa_slug
    2. Suffix match: aa_slug ends with normalized_provider_slug
    3. Contains match: normalized_provider_slug in aa_slug

    Args:
        provider_slug: The model slug from provider (will be normalized)
        inference_provider: The provider name (for logging)
        aa_slugs: List of available aa_slug values

    Returns:
        Matched aa_slug or None if no match found
    """
    # Normalize provider_slug to match aa_slug format
    normalized_slug = normalize_slug(provider_slug)

    # Strategy 1: Exact match
    for aa_slug in aa_slugs:
        if aa_slug.lower() == normalized_slug:
            return aa_slug

    # Strategy 2: Suffix match (e.g., "llama-3-1-8b-instant" matches "meta-llama-3-1-8b-instant")
    for aa_slug in aa_slugs:
        if aa_slug.lower().endswith(normalized_slug):
            return aa_slug

    # Strategy 3: Contains match (e.g., "gpt-4o" in "gpt-4o-2024-05-13")
    for aa_slug in aa_slugs:
        if normalized_slug in aa_slug.lower():
            return aa_slug

    return None


def create_mappings(
    models: List[Tuple[str, str]],
    aa_slugs: List[str],
    logger: Optional[logging.Logger] = None
) -> Tuple[List[Tuple], Dict[str, List[Tuple[str, List[Tuple[str, float]]]]]]:
    """
    Create mappings between provider_slug and aa_slug with enhanced reporting.

    Args:
        models: List of (inference_provider, provider_slug) tuples
        aa_slugs: List of available aa_slug values
        logger: Optional logger for output

    Returns:
        Tuple of (mappings_list, unmatched_with_nearest_dict)
        where unmatched_with_nearest_dict maps provider to list of
        (provider_slug, nearest_matches) tuples
    """
    log = logger.info if logger else print

    mappings = []
    unmatched_by_provider: Dict[str, List[Tuple[str, List[Tuple[str, float]]]]] = {}
    matched_by_provider: Dict[str, int] = {}

    log("")
    log("=" * 70)
    log("MATCHING PROVIDER MODELS TO AA PERFORMANCE SLUGS")
    log("=" * 70)

    for inference_provider, provider_slug in models:
        aa_slug = match_provider_slug_to_aa_slug(provider_slug, inference_provider, aa_slugs)

        if aa_slug:
            # Normalize provider_slug to match aa_slug format (convert special chars to hyphens)
            normalized_provider_slug = normalize_slug(provider_slug)

            mappings.append((
                inference_provider,
                normalized_provider_slug,
                aa_slug,
                datetime.utcnow(),
                datetime.utcnow()
            ))
            matched_by_provider[inference_provider] = matched_by_provider.get(inference_provider, 0) + 1
        else:
            # Find nearest aa_slugs for unmatched models
            nearest_matches = find_nearest_aa_slugs(provider_slug, aa_slugs, top_n=5)

            if inference_provider not in unmatched_by_provider:
                unmatched_by_provider[inference_provider] = []
            unmatched_by_provider[inference_provider].append((provider_slug, nearest_matches))

    # Calculate statistics
    total_models = len(models)
    total_matched = len(mappings)
    total_unmatched = total_models - total_matched
    match_rate = (total_matched / total_models * 100) if total_models > 0 else 0

    log("")
    log("=" * 70)
    log("MAPPING RESULTS SUMMARY")
    log("=" * 70)
    log(f"✅ Total models processed: {total_models}")
    log(f"✅ Successfully matched: {total_matched} ({match_rate:.1f}%)")
    log(f"⚠️  Unmatched models: {total_unmatched}")
    log("")

    # Show matched breakdown by provider
    if matched_by_provider:
        log("Matched by provider:")
        for provider in sorted(matched_by_provider.keys()):
            log(f"  • {provider}: {matched_by_provider[provider]} models")
        log("")

    # Enhanced unmatched reporting - TABULAR display with nearest matches
    if unmatched_by_provider:
        log("⚠️" * 35)
        log("UNMATCHED MODELS WITH NEAREST AA_SLUG CANDIDATES")
        log("⚠️" * 35)
        log("")
        log("The following models from working_version could not be automatically")
        log("mapped to AA performance metrics. Review the nearest candidates below:")
        log("")

        # Table header
        log("=" * 120)
        log(f"{'PROVIDER':<20} | {'PROVIDER_SLUG':<35} | {'NEAREST AA_SLUG CANDIDATES (Top 5)'}")
        log("=" * 120)

        for provider in sorted(unmatched_by_provider.keys()):
            unmatched_models = unmatched_by_provider[provider]

            for provider_slug, nearest_matches in sorted(unmatched_models, key=lambda x: x[0]):
                # First row with provider and slug
                if nearest_matches:
                    # First candidate on same line as provider and slug
                    aa_slug, score = nearest_matches[0]
                    log(f"{provider:<20} | {provider_slug:<35} | • {aa_slug:<40} (similarity: {score*100:.1f}%)")

                    # Remaining candidates on subsequent lines
                    for aa_slug, score in nearest_matches[1:]:
                        log(f"{'':<20} | {'':<35} | • {aa_slug:<40} (similarity: {score*100:.1f}%)")
                else:
                    log(f"{provider:<20} | {provider_slug:<35} | (no similar candidates found)")

                # Separator between models
                log(f"{'-'*20}-|-{'-'*35}-|-{'-'*60}")

            # Extra spacing between providers
            log("")

        log("=" * 120)
        log("END OF UNMATCHED MODELS REPORT")
        log("=" * 120)
        log("")

    return mappings, unmatched_by_provider


def upsert_mappings(
    conn,
    mappings: List[Tuple],
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Insert or update mappings in ims.10_model_aa_mapping using UPSERT pattern.

    Uses ON CONFLICT (inference_provider, provider_slug) DO UPDATE
    to safely handle duplicate keys.

    Args:
        conn: Database connection
        mappings: List of (inference_provider, provider_slug, aa_slug, created_at, updated_at) tuples
        logger: Optional logger for output

    Returns:
        True if successful, False otherwise
    """
    log = logger.info if logger else print

    if not mappings:
        log("⚠️  No mappings to insert")
        return True

    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO ims."10_model_aa_mapping"
                (inference_provider, provider_slug, aa_slug, created_at, updated_at)
                VALUES %s
                ON CONFLICT (inference_provider, provider_slug)
                DO UPDATE SET
                    aa_slug = EXCLUDED.aa_slug,
                    updated_at = EXCLUDED.updated_at
                """,
                mappings
            )
            conn.commit()
            log(f"✅ Successfully upserted {len(mappings)} mappings to ims.10_model_aa_mapping")
            return True
    except Exception as e:
        conn.rollback()
        log(f"❌ ERROR: Failed to upsert mappings: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return False


def write_comparison_report(
    unmatched_by_provider: Dict[str, List[Tuple[str, List[Tuple[str, float]]]]],
    output_file: str
) -> bool:
    """
    Write unmatched models comparison report to a file.

    Args:
        unmatched_by_provider: Dictionary mapping provider to list of (slug, nearest_matches)
        output_file: Path to output file

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Slug Comparison Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 120 + "\n\n")

            if not unmatched_by_provider:
                f.write("✅ All models successfully matched to AA performance metrics!\n")
                f.write("No unmatched models to report.\n")
                return True

            f.write("UNMATCHED MODELS WITH NEAREST AA_SLUG CANDIDATES\n")
            f.write("=" * 120 + "\n\n")
            f.write("The following models from working_version could not be automatically\n")
            f.write("mapped to AA performance metrics. Review the nearest candidates below:\n\n")

            # Table header
            f.write("=" * 120 + "\n")
            f.write(f"{'PROVIDER':<20} | {'PROVIDER_SLUG':<35} | {'NEAREST AA_SLUG CANDIDATES (Top 5)'}\n")
            f.write("=" * 120 + "\n")

            for provider in sorted(unmatched_by_provider.keys()):
                unmatched_models = unmatched_by_provider[provider]

                for provider_slug, nearest_matches in sorted(unmatched_models, key=lambda x: x[0]):
                    # First row with provider and slug
                    if nearest_matches:
                        # First candidate on same line as provider and slug
                        aa_slug, score = nearest_matches[0]
                        f.write(f"{provider:<20} | {provider_slug:<35} | • {aa_slug:<40} (similarity: {score*100:.1f}%)\n")

                        # Remaining candidates on subsequent lines
                        for aa_slug, score in nearest_matches[1:]:
                            f.write(f"{'':<20} | {'':<35} | • {aa_slug:<40} (similarity: {score*100:.1f}%)\n")
                    else:
                        f.write(f"{provider:<20} | {provider_slug:<35} | (no similar candidates found)\n")

                    # Separator between models
                    f.write(f"{'-'*20}-|-{'-'*35}-|-{'-'*60}\n")

                # Extra spacing between providers
                f.write("\n")

            f.write("=" * 120 + "\n")
            f.write("END OF COMPARISON REPORT\n")
            f.write("=" * 120 + "\n")

        return True

    except Exception as e:
        print(f"ERROR: Failed to write comparison report: {e}")
        return False


def backup_provider_mappings(
    conn,
    inference_provider: str,
    logger: Optional[logging.Logger] = None
) -> Optional[List[Tuple]]:
    """
    Backup all mappings for a specific provider.

    Args:
        conn: Database connection
        inference_provider: Provider to backup (e.g., "Groq")
        logger: Optional logger

    Returns:
        List of tuples (inference_provider, provider_slug, aa_slug, created_at, updated_at)
        or None on error
    """
    log = logger.info if logger else print

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT inference_provider, provider_slug, aa_slug, created_at, updated_at
                FROM ims."10_model_aa_mapping"
                WHERE inference_provider = %s
                """,
                (inference_provider,)
            )
            return cur.fetchall()
    except Exception as e:
        log(f"❌ ERROR: Failed to backup mappings: {e}")
        return None


def delete_provider_mappings(
    conn,
    inference_provider: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Delete all mappings for a specific provider.

    Args:
        conn: Database connection
        inference_provider: Provider to delete (e.g., "Groq")
        logger: Optional logger

    Returns:
        True if successful, False otherwise
    """
    log = logger.info if logger else print

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM ims."10_model_aa_mapping"
                WHERE inference_provider = %s
                """,
                (inference_provider,)
            )
            deleted_count = cur.rowcount
            conn.commit()
            log(f"Deleted {deleted_count} mappings for {inference_provider}")
            return True
    except Exception as e:
        conn.rollback()
        log(f"❌ ERROR: Failed to delete mappings: {e}")
        return False


def restore_provider_mappings(
    conn,
    backup_mappings: List[Tuple],
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Restore mappings from backup.

    Args:
        conn: Database connection
        backup_mappings: List of tuples from backup
        logger: Optional logger

    Returns:
        True if successful, False otherwise
    """
    log = logger.info if logger else print

    if not backup_mappings:
        log("No backup mappings to restore")
        return True

    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO ims."10_model_aa_mapping"
                (inference_provider, provider_slug, aa_slug, created_at, updated_at)
                VALUES %s
                """,
                backup_mappings
            )
            conn.commit()
            log(f"✅ Restored {len(backup_mappings)} mappings from backup")
            return True
    except Exception as e:
        conn.rollback()
        log(f"❌ ERROR: Failed to restore mappings: {e}")
        return False


def refresh_model_aa_mapping(
    conn,
    inference_provider: Optional[str] = None,
    output_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Main entry point: Refresh ims.10_model_aa_mapping table from working_version.

    This function:
    1. Fetches models from working_version (optionally filtered by provider)
    2. Fetches AA performance slugs from ims.20_aa_performance_metrics
    3. Matches provider models to AA slugs using smart matching
    4. Upserts mappings with ON CONFLICT handling
    5. Provides enhanced reporting for unmatched models
    6. Writes comparison report to slugs_comparison.txt

    Args:
        conn: Database connection (must be open)
        inference_provider: Optional provider filter (e.g., "Groq")
        output_dir: Optional directory for slugs_comparison.txt (default: current dir)
        logger: Optional logger for structured output

    Returns:
        True if successful, False on critical error
    """
    log = logger.info if logger else print

    try:
        log("")
        log("=" * 70)
        if inference_provider:
            log(f"REFRESHING MODEL-AA MAPPINGS FOR: {inference_provider}")
        else:
            log("REFRESHING MODEL-AA MAPPINGS FOR: ALL PROVIDERS")
        log("=" * 70)
        log(f"Started: {datetime.now().isoformat()}")
        log("")

        # Step 1: Fetch models from working_version
        log("📁 Fetching models from working_version...")
        models = fetch_working_version_models(conn, inference_provider)
        if not models:
            log("⚠️  No models found in working_version")
            return False
        log(f"✅ Found {len(models)} unique models")

        # Step 2: Fetch AA performance slugs
        log("📁 Fetching AA performance metric slugs...")
        aa_slugs = fetch_aa_performance_slugs(conn)
        if not aa_slugs:
            log("⚠️  No AA performance slugs found")
            return False
        log(f"✅ Found {len(aa_slugs)} AA performance slugs")

        # Step 3: Create mappings with enhanced reporting
        mappings, unmatched_by_provider = create_mappings(models, aa_slugs, logger)

        # Step 4: Complete refresh with backup/delete/insert pattern
        # (similar to working_version refresh)
        if inference_provider:
            log(f"🔄 Performing complete refresh for {inference_provider}...")

            # Step 4a: Backup existing mappings
            log(f"💾 Backing up existing mappings for {inference_provider}...")
            backup_mappings = backup_provider_mappings(conn, inference_provider, logger)
            if backup_mappings is None:
                log("⚠️  Backup failed, but continuing with refresh...")
            else:
                log(f"✅ Backed up {len(backup_mappings)} existing mappings")

            # Step 4b: Delete existing mappings for this provider
            log(f"🗑️  Deleting existing mappings for {inference_provider}...")
            if not delete_provider_mappings(conn, inference_provider, logger):
                log(f"❌ Failed to delete existing mappings, attempting rollback...")
                if backup_mappings and restore_provider_mappings(conn, backup_mappings, logger):
                    log("✅ Rollback successful - restored original mappings")
                else:
                    log("❌ Rollback failed - manual intervention may be required")
                return False
            log(f"✅ Deleted existing mappings for {inference_provider}")

        # Step 4c: Insert new mappings
        if not upsert_mappings(conn, mappings, logger):
            # Rollback on failure
            if inference_provider and backup_mappings:
                log(f"❌ Insert failed, attempting rollback...")
                if restore_provider_mappings(conn, backup_mappings, logger):
                    log("✅ Rollback successful - restored original mappings")
                else:
                    log("❌ Rollback failed - manual intervention may be required")
            return False

        # Step 5: Write comparison report to file
        if output_dir:
            from pathlib import Path
            output_file = Path(output_dir) / "slugs_comparison.txt"
            log(f"📄 Writing comparison report to: {output_file}")
            if write_comparison_report(unmatched_by_provider, str(output_file)):
                log(f"✅ Comparison report saved: {output_file}")
            else:
                log(f"⚠️  Failed to write comparison report (non-critical)")

        log("")
        log("=" * 70)
        log("✅ MODEL-AA MAPPING REFRESH COMPLETED")
        log("=" * 70)
        log(f"Completed: {datetime.now().isoformat()}")
        log("")

        return True

    except Exception as e:
        log(f"❌ ERROR: Unexpected error during mapping refresh: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    """
    Standalone execution for testing or manual runs.
    Requires PIPELINE_SUPABASE_URL environment variable.
    """
    import os

    DATABASE_URL = os.environ.get('PIPELINE_SUPABASE_URL')

    if not DATABASE_URL:
        print("ERROR: PIPELINE_SUPABASE_URL environment variable not set")
        sys.exit(1)

    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connected to database")

        success = refresh_model_aa_mapping(conn)

        conn.close()
        print("Database connection closed")

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)
