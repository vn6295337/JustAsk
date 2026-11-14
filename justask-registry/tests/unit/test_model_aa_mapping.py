"""Unit tests for model -> Artificial Analysis link statuses (table 21). No database needed."""

from src.utils.model_aa_mapping import (
    AA_UNSCORED, LINKED, LINKED_EFFORT_UNKNOWN, NO_MATCH, NOT_CHAT_MODEL,
    build_rows, classify, coverage, normalize_slug,
)

AA = {
    'gemini-3-5-flash-lite': 11.7,
    'gemini-3-8-flash': 30.8, 'gemini-3-8-flash-low': 22.5, 'gemini-3-8-flash-medium': 30.1,
    'gemini-4-argon': 50.4,
    'gemma-4-31b': 4.4,
    'gpt-oss-120b': 3.8,
    'nvidia-nemotron-3-nano-30b-a3b': None,   # listed by AA, not scored
    'gemma-3-27b': None,
    'gemini-3-1-flash-lite-preview': 6.2,
}


def test_normalize():
    assert normalize_slug('gemini-3.5-flash') == 'gemini-3-5-flash'
    assert normalize_slug('gemma-4-31b-it-20260402') == 'gemma-4-31b'
    assert normalize_slug('qwen3-next-80b-a3b-instruct-2509') == 'qwen3-next-80b-a3b'
    assert normalize_slug('qwen3-coder-480b-a35b-07-25') == 'qwen3-coder-480b-a35b'
    assert normalize_slug('GLM_4.5 Air') == 'glm-4-5-air'


def test_exact_match_is_linked():
    assert classify('gemini-4-argon', 'Text', AA) == (LINKED, 'gemini-4-argon')
    assert classify('gemma-4-31b-it-20260402', 'Text', AA) == (LINKED, 'gemma-4-31b')


def test_no_contains_match_flash_is_not_flash_lite():
    # The old rules linked Gemini 3.5 Flash to Flash-Lite ("contains"); now it is no_match.
    assert classify('gemini-3.5-flash', 'Unknown', AA) == (NO_MATCH, None)


def test_both_sides_normalized():
    assert classify('gemini-3.1-flash-lite', 'Unknown', AA) == (LINKED, 'gemini-3-1-flash-lite-preview')


def test_effort_variants_flagged():
    assert classify('gemini-3.8-flash', 'Unknown', AA) == (LINKED_EFFORT_UNKNOWN, 'gemini-3-8-flash')


def test_maker_prefix_and_unscored():
    assert classify('nemotron-3-nano-30b-a3b', 'Text', AA) == (AA_UNSCORED, 'nvidia-nemotron-3-nano-30b-a3b')
    assert classify('gemma-3-27b-it', 'Text', AA) == (AA_UNSCORED, 'gemma-3-27b')


def test_not_chat_models():
    for slug, out in [('gemini-embedding-001', 'Text Embeddings'), ('gemini-3.8-flash-tts', 'Unknown'),
                      ('whisper-large-v3', 'Text'), ('lyria-3.5', 'Unknown'),
                      ('gemini-3.1-flash-image', 'Unknown'), ('gemini-3.8-live', 'Unknown'),
                      ('some-model', 'Image')]:
        assert classify(slug, out, AA) == (NOT_CHAT_MODEL, None), slug


def test_unknown_modalities_still_chat():
    assert classify('gpt-oss-120b', 'Unknown', AA) == (LINKED, 'gpt-oss-120b')
    assert classify('gpt-oss-120b', None, AA) == (LINKED, 'gpt-oss-120b')


def test_build_rows_skips_manual_and_coverage():
    models = [('Groq', 'gpt-oss-120b', 'Text'), ('Groq', 'gpt-oss-20b', 'Text'),
              ('Groq', 'whisper-large-v3', 'Text'), ('Google', 'gemini-4-argon', 'Text')]
    rows = build_rows(models, AA, manual_keys={('Google', 'gemini-4-argon')})
    assert [(r['provider_slug'], r['status']) for r in rows] == [
        ('gpt-oss-120b', LINKED), ('gpt-oss-20b', NO_MATCH), ('whisper-large-v3', NOT_CHAT_MODEL)]
    assert coverage(rows) == (1, 2)
