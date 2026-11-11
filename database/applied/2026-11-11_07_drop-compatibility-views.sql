-- Applied 2026-11-11 via the Supabase Management API.
-- All code uses the new names (router, dashboard, CI verified), so the compatibility views and the empty ims schema go.
-- Also: API exposed schemas set to 'public, justask'; extra search path 'public, extensions'.
begin;
drop view ims."10_model_aa_mapping", ims."20_aa_performance_metrics", ims."30_rate_limits", ims."40_model_selection_score";
drop schema ims;
drop view public.working_version, public.ai_models_main, public.analytics_history,
  public.key_metadata, public.usage_metrics, public.provider_rate_limits, public.notifications, public.audit_logs,
  public.provider_metadata, public.model_availability, public.pricing_data, public.quality_metrics, public.models;
notify pgrst, 'reload schema';
commit;
