#!/usr/bin/env python3
"""
Model-to-Artificial-Analysis links (justask."21_router-model-benchmark-map")
===========================================================================

Builds one row per model in 11_free-models-live, saying how it links to an
Artificial Analysis (AA) entry in 20_router-benchmark-scores:

    status                  aa_slug   meaning
    linked                  set       matched to a scored AA entry
    linked_effort_unknown   set       matched, but AA scores several effort levels
                                      (low / medium / high ...) and we cannot tell which
                                      one the free API runs; linked to AA's plain slug
    aa_unscored             set       AA lists the model but has no intelligence score
    not_chat_model          empty     embedding, voice, image, transcription, music ...
    no_match                empty     no AA entry found

Rows have source 'auto' (made here) or 'manual' (set by hand). A refresh deletes and
rebuilds 'auto' rows only; a model with a 'manual' row is never touched.

Matching is strict: our slug and the AA slug, both in the same format (lowercase,
hyphens, no date or "-it"/"-preview"-style ending), must be identical, optionally after a
single known maker prefix on AA's side (e.g. "nvidia-"). No "contains" or "ends with".

Run by:
- the publish step of each provider (deploy workflows), for that provider;
- the daily AA refresh workflow, for all providers.
"""

import os
import re
import sys
import logging
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("Error: psycopg2 package not found. Install with: pip install psycopg2-binary")
    sys.exit(1)

MAP_TABLE = 'justask."21_router-model-benchmark-map"'
LIVE_TABLE = 'justask."11_free-models-live"'
SCORES_TABLE = 'justask."20_router-benchmark-scores"'

LINKED = 'linked'
LINKED_EFFORT_UNKNOWN = 'linked_effort_unknown'
AA_UNSCORED = 'aa_unscored'
NOT_CHAT_MODEL = 'not_chat_model'
NO_MATCH = 'no_match'
STATUSES = (LINKED, LINKED_EFFORT_UNKNOWN, AA_UNSCORED, NOT_CHAT_MODEL, NO_MATCH)
SCORED_STATUSES = (LINKED, LINKED_EFFORT_UNKNOWN)  # what the ranking uses

# AA effort-level variants of one model: "<slug>-low", "<slug>-medium", ...
EFFORT_SUFFIXES = ('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'reasoning', 'non-reasoning')
# One-word maker prefixes AA puts in front of some slugs ("nvidia-nemotron-...")
MAKER_PREFIXES = ('nvidia', 'meta', 'google', 'mistral', 'deepseek', 'openai', 'microsoft',
                  'ibm', 'amazon', 'cohere', 'xai', 'alibaba', 'moonshotai', 'minimax')
# Slug words that mark a model that does not answer chat questions
NON_CHAT_WORDS = {'embedding', 'embeddings', 'tts', 'transcribe', 'whisper', 'image', 'imagen',
                  'veo', 'lyria', 'music', 'banana', 'aqa', 'guard', 'live'}
# Endings the providers add that AA leaves out
STRIP_SUFFIXES = ('-instruct', '-chat', '-it', '-turbo', '-preview', '-exp')
DATE_SUFFIX = re.compile(r'-(\d{8}|\d{4}|\d{2}-\d{2})$')


def normalize_slug(slug: str) -> str:
    """Bring a provider slug to AA's format: lowercase, hyphens, no date or common suffix.

    "gemini-3.5-flash" -> "gemini-3-5-flash"; "gemma-4-31b-it-20260402" -> "gemma-4-31b";
    "qwen3-next-80b-a3b-instruct-2509" -> "qwen3-next-80b-a3b".
    """
    if not slug:
        return ''
    s = re.sub(r'[.\s_]+', '-', slug.strip().lower())
    s = re.sub(r'-+', '-', s).strip('-')
    s = DATE_SUFFIX.sub('', s)
    for suffix in STRIP_SUFFIXES:
        if s.endswith(suffix):
            s = s[:-len(suffix)]
            break
    return s


def is_chat_model(provider_slug: str, output_modalities: Optional[str]) -> bool:
    """False for embedding, voice, image, transcription, music and similar models."""
    words = set(re.split(r'[-.\s_/]+', (provider_slug or '').lower()))
    if words & NON_CHAT_WORDS:
        return False
    out = (output_modalities or '').strip().lower()
    if 'embedding' in out:
        return False
    if out and out != 'unknown' and 'text' not in out:
        return False
    return True


def find_aa_slug(provider_slug: str, aa_slugs: Set[str]) -> Optional[str]:
    """Strict match: both slugs in the same format must be identical, optionally after one
    known maker prefix on AA's side ("nvidia-..."). An exact AA slug wins over a normalized one."""
    norm = normalize_slug(provider_slug)
    if not norm:
        return None
    candidates = [norm] + [f'{prefix}-{norm}' for prefix in MAKER_PREFIXES]
    for c in candidates:
        if c in aa_slugs:
            return c
    by_norm: Dict[str, str] = {}
    for aa in sorted(aa_slugs):
        by_norm.setdefault(normalize_slug(aa), aa)
    for c in candidates:
        if c in by_norm:
            return by_norm[c]
    return None


def has_effort_variants(aa_slug: str, aa_slugs: Set[str]) -> bool:
    return any(f'{aa_slug}-{suffix}' in aa_slugs for suffix in EFFORT_SUFFIXES)


def classify(provider_slug: str, output_modalities: Optional[str],
             aa_scores: Dict[str, Optional[float]]) -> Tuple[str, Optional[str]]:
    """Return (status, aa_slug) for one model. aa_scores: {aa_slug: intelligence_index or None}."""
    if not is_chat_model(provider_slug, output_modalities):
        return NOT_CHAT_MODEL, None
    aa_slugs = set(aa_scores)
    aa_slug = find_aa_slug(provider_slug, aa_slugs)
    if aa_slug is None:
        return NO_MATCH, None
    if aa_scores.get(aa_slug) is None:
        return AA_UNSCORED, aa_slug
    if has_effort_variants(aa_slug, aa_slugs):
        return LINKED_EFFORT_UNKNOWN, aa_slug
    return LINKED, aa_slug


def coverage(rows: Iterable[Dict[str, Any]]) -> Tuple[int, int]:
    """(chat models with a scored link, chat models)."""
    rows = list(rows)
    chat = [r for r in rows if r['status'] != NOT_CHAT_MODEL]
    return sum(1 for r in chat if r['status'] in SCORED_STATUSES), len(chat)


def _fetch_live_models(conn, inference_provider: Optional[str]) -> List[Tuple[str, str, Optional[str]]]:
    sql = (f"SELECT inference_provider, provider_slug, output_modalities FROM {LIVE_TABLE} "
           "WHERE provider_slug IS NOT NULL AND provider_slug <> ''")
    params: Tuple = ()
    if inference_provider:
        sql += " AND inference_provider = %s"
        params = (inference_provider,)
    with conn.cursor() as cur:
        cur.execute(sql + " ORDER BY inference_provider, provider_slug", params)
        return cur.fetchall()


def _fetch_aa_scores(conn) -> Dict[str, Optional[float]]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT aa_slug, intelligence_index FROM {SCORES_TABLE} WHERE aa_slug IS NOT NULL")
        return {slug: (float(score) if score is not None else None) for slug, score in cur.fetchall()}


def _fetch_manual_keys(conn, inference_provider: Optional[str]) -> Set[Tuple[str, str]]:
    sql = f"SELECT inference_provider, provider_slug FROM {MAP_TABLE} WHERE source = 'manual'"
    params: Tuple = ()
    if inference_provider:
        sql += " AND inference_provider = %s"
        params = (inference_provider,)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return set(cur.fetchall())


def build_rows(models: List[Tuple[str, str, Optional[str]]], aa_scores: Dict[str, Optional[float]],
               manual_keys: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """One 'auto' row per live model that has no manual row."""
    rows = []
    for provider, slug, output_modalities in models:
        if (provider, slug) in manual_keys:
            continue
        status, aa_slug = classify(slug, output_modalities, aa_scores)
        rows.append({'inference_provider': provider, 'provider_slug': slug,
                     'aa_slug': aa_slug, 'status': status})
    return rows


def _report(rows: List[Dict[str, Any]], manual_count: int, log) -> List[str]:
    lines = []
    by_provider: Dict[str, Counter] = {}
    for r in rows:
        by_provider.setdefault(r['inference_provider'], Counter())[r['status']] += 1
    for provider in sorted(by_provider):
        c = by_provider[provider]
        lines.append(f"{provider}: " + ", ".join(f"{s} {c[s]}" for s in STATUSES if c[s]))
    linked, chat = coverage(rows)
    pct = f"{linked / chat * 100:.0f}%" if chat else "n/a"
    lines.append(f"Coverage (auto rows): {linked} of {chat} chat models have a scored link ({pct})")
    if manual_count:
        lines.append(f"Manual rows kept unchanged: {manual_count}")
    for line in lines:
        log(f"   {line}")
    review = [r for r in rows if r['status'] in (LINKED_EFFORT_UNKNOWN, NO_MATCH)]
    if review:
        log("   To review:")
        for r in review:
            log(f"     {r['status']:<22} {r['inference_provider']}/{r['provider_slug']}"
                + (f" -> {r['aa_slug']}" if r['aa_slug'] else ""))
    return lines


def _write_step_summary(title: str, lines: List[str]) -> None:
    path = os.getenv('GITHUB_STEP_SUMMARY')
    if not path:
        return
    try:
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write(f"### {title}\n\n" + "\n".join(f"- {l}" for l in lines) + "\n\n")
    except OSError:
        pass


def refresh_model_aa_mapping(
    conn,
    inference_provider: Optional[str] = None,
    output_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Rebuild the 'auto' rows of table 21 for one provider (or all), in one transaction.

    Fails closed: if table 20 or table 11 is empty, nothing is changed.
    output_dir is accepted for backward compatibility and not used.
    """
    log = logger.info if logger else print
    scope = inference_provider or 'all providers'
    try:
        log(f"Refreshing model -> AA links ({MAP_TABLE}) for {scope}")
        models = _fetch_live_models(conn, inference_provider)
        if not models:
            log(f"No models in {LIVE_TABLE} for {scope}; nothing changed")
            return False
        aa_scores = _fetch_aa_scores(conn)
        if not aa_scores:
            log(f"No rows in {SCORES_TABLE}; nothing changed")
            return False
        manual_keys = _fetch_manual_keys(conn, inference_provider)
        rows = build_rows(models, aa_scores, manual_keys)

        with conn.cursor() as cur:
            if inference_provider:
                cur.execute(f"DELETE FROM {MAP_TABLE} WHERE source = 'auto' AND inference_provider = %s",
                            (inference_provider,))
            else:
                cur.execute(f"DELETE FROM {MAP_TABLE} WHERE source = 'auto'")
            if rows:
                execute_values(
                    cur,
                    f"INSERT INTO {MAP_TABLE} (inference_provider, provider_slug, aa_slug, source, status) "
                    "VALUES %s ON CONFLICT (inference_provider, provider_slug) DO NOTHING",
                    [(r['inference_provider'], r['provider_slug'], r['aa_slug'], 'auto', r['status'])
                     for r in rows],
                )
        conn.commit()

        log(f"Wrote {len(rows)} auto rows for {scope} ({len(models)} live models)")
        lines = _report(rows, len(manual_keys), log)
        _write_step_summary(f"Model -> AA links: {scope}", lines)
        return True
    except Exception as e:  # noqa: BLE001 - roll back and report any failure
        log(f"ERROR: link refresh failed, rolled back, table unchanged: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False


if __name__ == "__main__":
    # python -m src.utils.model_aa_mapping [provider]   (no provider = all providers)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.utils.db import get_pipeline_db_connection

    provider = sys.argv[1] if len(sys.argv) > 1 else None
    conn = get_pipeline_db_connection()
    if conn is None:
        print("ERROR: could not connect to database (PIPELINE_SUPABASE_URL)")
        sys.exit(1)
    try:
        ok = refresh_model_aa_mapping(conn, inference_provider=provider)
    finally:
        conn.close()
    sys.exit(0 if ok else 1)
