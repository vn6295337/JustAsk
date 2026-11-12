"""Unit tests for the staging -> live publish gate (no database needed)."""

from src.utils.publish_gate import check_column_parity, check_rows, large_drop_overridden
from src.utils.rate_limit_parser import build_rate_limit_records


def rows(n, provider='Groq'):
    return [{
        'id': i,
        'inference_provider': provider,
        'provider_slug': f'model-{i}',
        'human_readable_name': f'Model {i}',
        'rate_limits': 'RPM: 30, TPM: 6K, RPD: 1K, TPD: 500K',
    } for i in range(n)]


def test_clean_rows_pass():
    assert check_rows(rows(6), live_count=6, max_drop=20, allow_drop=False) == []


def test_no_rows_blocks():
    assert check_rows([], live_count=6, max_drop=20, allow_drop=False) == ['no staged rows for this provider']


def test_growth_and_first_publish_pass():
    assert check_rows(rows(10), live_count=6, max_drop=20, allow_drop=False) == []
    assert check_rows(rows(3), live_count=0, max_drop=20, allow_drop=False) == []


def test_small_provider_drop_of_one_passes():
    # 6 -> 5 is a 17% drop: under the 20% limit
    assert check_rows(rows(5), live_count=6, max_drop=20, allow_drop=False) == []


def test_small_provider_drop_of_two_blocks():
    # 6 -> 4 is a 33% drop: over the 20% limit
    failures = check_rows(rows(4), live_count=6, max_drop=20, allow_drop=False)
    assert len(failures) == 1 and '6 -> 4' in failures[0]


def test_large_drop_blocks_and_override_allows():
    assert check_rows(rows(5), live_count=28, max_drop=20, allow_drop=False)
    assert check_rows(rows(5), live_count=28, max_drop=20, allow_drop=True) == []
    assert large_drop_overridden(rows(5), 28, max_drop=20, allow_drop=True) is True
    assert large_drop_overridden(rows(28), 28, max_drop=20, allow_drop=True) is False


def test_override_does_not_bypass_other_checks():
    bad = rows(5)
    bad[0]['provider_slug'] = ''
    failures = check_rows(bad, live_count=28, max_drop=20, allow_drop=True)
    assert any('empty provider_slug' in f for f in failures)


def test_empty_required_field_blocks():
    for field in ('inference_provider', 'provider_slug', 'human_readable_name', 'rate_limits'):
        r = rows(3)
        r[1][field] = '  '
        failures = check_rows(r, live_count=3, max_drop=20, allow_drop=False)
        assert any(f'empty {field}' in f for f in failures), field


def test_duplicate_slug_blocks():
    r = rows(3)
    r[2]['provider_slug'] = 'model-0'
    failures = check_rows(r, live_count=3, max_drop=20, allow_drop=False)
    assert any('duplicate provider_slug' in f and 'Groq/model-0' in f for f in failures)


class FakeCursor:
    def __init__(self, tables):
        self.tables, self.result = tables, None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params):
        table = params[0]
        if table not in self.tables:
            raise RuntimeError(f'relation {table} does not exist')
        self.result = list(self.tables[table].items())

    def fetchall(self):
        return self.result


class FakeConn:
    def __init__(self, tables):
        self.tables = tables

    def cursor(self):
        return FakeCursor(self.tables)

    def rollback(self):
        pass


COLS = {'id': 'bigint', 'provider_slug': 'text', 'human_readable_name': 'text'}


def test_parity_same_columns_pass():
    conn = FakeConn({'s': dict(COLS), 'l': dict(COLS)})
    assert check_column_parity(conn, 's', 'l') == []


def test_parity_missing_column_blocks():
    live = dict(COLS)
    del live['provider_slug']
    failures = check_column_parity(FakeConn({'s': dict(COLS), 'l': live}), 's', 'l')
    assert failures == ['columns only in staging: provider_slug']


def test_parity_type_difference_blocks():
    live = dict(COLS, id='integer')
    failures = check_column_parity(FakeConn({'s': dict(COLS), 'l': live}), 's', 'l')
    assert failures and 'id (bigint vs integer)' in failures[0]


def test_parity_query_error_fails_closed():
    failures = check_column_parity(FakeConn({'s': dict(COLS)}), 's', 'missing')
    assert failures and failures[0].startswith('could not read table columns')


def test_rate_limit_records_built_per_model():
    recs = build_rate_limit_records(rows(2), 'Groq')
    assert [r['human_readable_name'] for r in recs] == ['Model 0', 'Model 1']
    assert recs[0]['rpm'] == 30 and recs[0]['inference_provider'] == 'Groq'
