-- Applied 2026-11-10 via the Supabase Management API.
-- Instant SWOT Agent cache left off (owner's choice), so its compatibility view and the empty asa schema go.
begin;
drop view asa.analysis_cache;
drop schema asa;
comment on table justask."70_external-stock-analysis-cache" is '[7 External app, not JustAsk] Stock analysis cache for Instant SWOT Agent (src/utils/analysis_cache.py). Caching is off since 2026-11-10: the app no longer has database access and runs without a cache.';
commit;
