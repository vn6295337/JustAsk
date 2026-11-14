-- Applied 2026-11-13 via the Supabase Management API.
-- justask."21_router-model-benchmark-map": one row per live model with a status, and manual rows.
-- The status default 'linked' keeps the previous mapping code working until the new code is merged;
-- the new code always sets status explicitly.
begin;
alter table justask."21_router-model-benchmark-map"
  alter column aa_slug drop not null,
  add column source text not null default 'auto',
  add column status text not null default 'linked',
  add column note   text;
alter table justask."21_router-model-benchmark-map"
  add constraint router_model_benchmark_map_source_check
    check (source in ('auto', 'manual')),
  add constraint router_model_benchmark_map_status_check
    check (status in ('linked', 'linked_effort_unknown', 'aa_unscored', 'not_chat_model', 'no_match')),
  add constraint router_model_benchmark_map_aa_slug_check
    check (status in ('not_chat_model', 'no_match') or aa_slug is not null);
comment on column justask."21_router-model-benchmark-map".provider_slug is 'Original provider_slug from 11_free-models-live (not normalized).';
comment on column justask."21_router-model-benchmark-map".aa_slug is 'AA entry in 20_router-benchmark-scores; empty for not_chat_model and no_match.';
comment on column justask."21_router-model-benchmark-map".source is 'auto: rebuilt by the registry; manual: set by hand, never overwritten.';
comment on column justask."21_router-model-benchmark-map".status is 'linked | linked_effort_unknown (AA scores several effort levels; linked to the plain slug) | aa_unscored | not_chat_model | no_match. The ranking uses linked and linked_effort_unknown.';
comment on column justask."21_router-model-benchmark-map".note is 'Free text, for manual rows.';
comment on table justask."21_router-model-benchmark-map" is '[2 Router] One row per model in 11_free-models-live: its Artificial Analysis entry (aa_slug in 20) and a status. Auto rows rebuilt by the registry publish step (one provider) and after the daily AA refresh (all providers); manual rows never overwritten. Read by the ranking script (23).';
notify pgrst, 'reload schema';
commit;
