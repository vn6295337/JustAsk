-- Applied 2026-11-10 via the Supabase Management API.
-- Remove all public-role (anon, authenticated) write access; read-only on the 7 active tables. Uses pre-rename names.
begin;
revoke all on all tables in schema public from anon, authenticated;
revoke all on all tables in schema ims    from anon, authenticated;

grant select on public.ai_models_main, public.working_version, public.analytics_history to anon, authenticated;
grant select on ims."10_model_aa_mapping", ims."20_aa_performance_metrics",
                ims."30_rate_limits", ims."40_model_selection_score" to anon, authenticated;

drop policy "Allow all access"                      on ims."10_model_aa_mapping";
drop policy "Allow anon insert for setup"           on ims."10_model_aa_mapping";
drop policy "Allow all access"                      on ims."20_aa_performance_metrics";
drop policy "Allow all access"                      on ims."30_rate_limits";
drop policy "Allow anon insert for setup"           on ims."30_rate_limits";
drop policy "Allow anon update for maintenance"     on ims."30_rate_limits";
drop policy "Allow anon insert for setup"           on ims."40_model_selection_score";
drop policy "Allow anon update for usage tracking"  on ims."40_model_selection_score";
drop policy "Public insert access for analytics history" on public.analytics_history;

alter default privileges for role postgres in schema public revoke all on tables from anon, authenticated;
alter default privileges for role postgres in schema ims    revoke all on tables from anon, authenticated;
commit;
