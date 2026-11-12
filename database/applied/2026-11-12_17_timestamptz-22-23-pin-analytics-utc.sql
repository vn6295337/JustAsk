-- Applied 2026-11-12 via the Supabase Management API (session time zone UTC).
-- Prepare for showing times in IST database-wide:
-- 1. Tables 22 and 23: created_at / updated_at become timestamptz. Existing values were written in UTC
--    sessions (now() / CURRENT_TIMESTAMP defaults), so they are read as UTC.
-- 2. The nightly analytics snapshot keeps counting by UTC day: pin its functions to UTC.
begin;
alter table justask."22_router-provider-rate-limits"
  alter column created_at type timestamptz using created_at at time zone 'UTC',
  alter column updated_at type timestamptz using updated_at at time zone 'UTC';
alter table justask."23_router-model-ranking"
  alter column created_at type timestamptz using created_at at time zone 'UTC',
  alter column updated_at type timestamptz using updated_at at time zone 'UTC';
alter function public.insert_analytics_snapshot(integer, jsonb, jsonb) set timezone = 'UTC';
alter function public.collect_daily_analytics() set timezone = 'UTC';
notify pgrst, 'reload schema';
commit;
