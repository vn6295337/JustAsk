-- Applied 2026-11-10 via the Supabase Management API.
-- Only the nightly pg_cron job may run the analytics functions; pin their search_path.
begin;
revoke execute on function public.collect_daily_analytics() from public, anon, authenticated;
revoke execute on function public.insert_analytics_snapshot(integer, jsonb, jsonb) from public, anon, authenticated;
alter function public.collect_daily_analytics() set search_path = public, pg_temp;
alter function public.insert_analytics_snapshot(integer, jsonb, jsonb) set search_path = public, pg_temp;
alter function public.update_updated_at_column() set search_path = public, pg_temp;
commit;
