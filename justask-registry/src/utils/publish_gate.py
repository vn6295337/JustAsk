"""
Publish gate for staging (10_free-models-staging) -> live (11_free-models-live).

Option A rule: table 10 is incoming only, table 11 is outgoing only. The deploy step
(the only path from 10 to 11) must refuse to publish a provider's rows when:
- the two tables' columns differ (name + type),
- the provider has no staged rows,
- the staged count drops more than MAX_DROP_PCT below the live count (unless overridden),
- a required field is empty,
- the same (inference_provider, provider_slug) appears twice.

Any failure to run a check blocks the publish (fail closed).
"""

import os
from collections import Counter
from typing import Any, Dict, List, Optional

REQUIRED_FIELDS = ('inference_provider', 'provider_slug', 'human_readable_name', 'rate_limits')
DEFAULT_MAX_DROP_PCT = 20.0


def _env_flag(name: str) -> bool:
    return os.getenv(name, '').strip().lower() in ('1', 'true', 'yes')


def max_drop_pct() -> float:
    """Allowed drop (percent) versus the live count; env PUBLISH_MAX_DROP_PCT, default 20."""
    try:
        return float(os.getenv('PUBLISH_MAX_DROP_PCT', DEFAULT_MAX_DROP_PCT))
    except ValueError:
        return DEFAULT_MAX_DROP_PCT


def allow_large_drop() -> bool:
    """Override for an intended large drop; env PUBLISH_ALLOW_LARGE_DROP=true."""
    return _env_flag('PUBLISH_ALLOW_LARGE_DROP')


def check_rows(
    rows: List[Dict[str, Any]],
    live_count: int,
    max_drop: Optional[float] = None,
    allow_drop: Optional[bool] = None,
) -> List[str]:
    """Return a list of reasons to block publishing these staged rows (empty = OK)."""
    max_drop = max_drop_pct() if max_drop is None else max_drop
    allow_drop = allow_large_drop() if allow_drop is None else allow_drop
    failures: List[str] = []

    if not rows:
        return ['no staged rows for this provider']

    if live_count and live_count > 0:
        drop_pct = (live_count - len(rows)) / live_count * 100
        if drop_pct > max_drop:
            msg = (f'model count drops {live_count} -> {len(rows)} ({drop_pct:.0f}%), '
                   f'more than the {max_drop:.0f}% limit')
            if not allow_drop:
                failures.append(msg)

    for field in REQUIRED_FIELDS:
        empty = [r.get('human_readable_name') or f"id={r.get('id')}"
                 for r in rows if not str(r.get(field) or '').strip()]
        if empty:
            failures.append(f'{len(empty)} row(s) with empty {field}: {", ".join(map(str, empty[:5]))}')

    keys = Counter((r.get('inference_provider'), r.get('provider_slug')) for r in rows
                   if str(r.get('provider_slug') or '').strip())
    dups = [f'{p}/{s}' for (p, s), n in keys.items() if n > 1]
    if dups:
        failures.append(f'duplicate provider_slug: {", ".join(dups[:5])}')

    return failures


def large_drop_overridden(rows: List[Dict[str, Any]], live_count: int,
                          max_drop: Optional[float] = None,
                          allow_drop: Optional[bool] = None) -> bool:
    """True when a drop above the limit is being published only because of the override."""
    max_drop = max_drop_pct() if max_drop is None else max_drop
    allow_drop = allow_large_drop() if allow_drop is None else allow_drop
    if not allow_drop or not rows or not live_count:
        return False
    return (live_count - len(rows)) / live_count * 100 > max_drop


def column_signature(conn, table_name: str) -> Dict[str, str]:
    """{column name: SQL type} for a table, e.g. 'justask."10_free-models-staging"'."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.attname, format_type(a.atttypid, a.atttypmod)
              FROM pg_attribute a
             WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped
            """,
            (table_name,),
        )
        return {name: typ for name, typ in cur.fetchall()}


def check_column_parity(conn, staging_table: str, live_table: str) -> List[str]:
    """Return reasons to block if the two tables' columns (name + type) differ. Fails closed."""
    try:
        staging = column_signature(conn, staging_table)
        live = column_signature(conn, live_table)
    except Exception as e:  # noqa: BLE001 - any error blocks the publish
        try:
            conn.rollback()
        except Exception:
            pass
        return [f'could not read table columns: {e}']
    if not staging or not live:
        return ['could not read table columns (empty result)']
    failures = []
    only_staging = sorted(set(staging) - set(live))
    only_live = sorted(set(live) - set(staging))
    if only_staging:
        failures.append(f'columns only in staging: {", ".join(only_staging)}')
    if only_live:
        failures.append(f'columns only in live: {", ".join(only_live)}')
    type_diff = sorted(c for c in set(staging) & set(live) if staging[c] != live[c])
    if type_diff:
        failures.append('column types differ: ' + ', '.join(
            f'{c} ({staging[c]} vs {live[c]})' for c in type_diff))
    return failures


def write_publish_summary(provider: str, live_before: int, staged: int, published: bool,
                          failures: List[str], overridden: bool = False) -> None:
    """Append a publish record to the GitHub Actions step summary, if running in Actions."""
    path = os.getenv('GITHUB_STEP_SUMMARY')
    if not path:
        return
    run = os.getenv('GITHUB_RUN_ID', 'local')
    actor = os.getenv('GITHUB_ACTOR', 'unknown')
    status = 'PUBLISHED' if published else 'BLOCKED'
    lines = [
        f'### {provider}: {status}',
        '',
        '| Live before | Staged | Run | Actor | Large-drop override |',
        '|---|---|---|---|---|',
        f'| {live_before} | {staged} | {run} | {actor} | {"USED" if overridden else "no"} |',
        '',
    ]
    lines += [f'- {f}' for f in failures]
    try:
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n\n')
    except OSError:
        pass
