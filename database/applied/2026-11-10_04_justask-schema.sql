-- Applied 2026-11-10 via the Supabase Management API.
-- Move all 18 tables into schema justask with numbered names; leave compatibility views under the old names.
begin;
create schema justask;
grant usage on schema justask to anon, authenticated, service_role, pipeline_writer;
alter table "public"."working_version" set schema justask;
alter table justask."working_version" rename to "10_free-models-staging";
comment on table justask."10_free-models-staging" is '[1 Free models] Model list before publishing. Written by registry refresh step (CI). Read by router.';
create view "public"."working_version" with (security_invoker = true) as select * from justask."10_free-models-staging";
comment on view "public"."working_version" is 'Compatibility view for justask.10_free-models-staging. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '10_free-models-staging' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'working_version', g.grantee);
  end loop; end $$;
alter table "public"."ai_models_main" set schema justask;
alter table justask."ai_models_main" rename to "11_free-models-live";
comment on table justask."11_free-models-live" is '[1 Free models] Published model list. Written by registry deploy step (CI). Read by dashboard and nightly analytics job.';
create view "public"."ai_models_main" with (security_invoker = true) as select * from justask."11_free-models-live";
comment on view "public"."ai_models_main" is 'Compatibility view for justask.11_free-models-live. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '11_free-models-live' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'ai_models_main', g.grantee);
  end loop; end $$;
alter table "ims"."20_aa_performance_metrics" set schema justask;
alter table justask."20_aa_performance_metrics" rename to "20_router-benchmark-scores";
comment on table justask."20_router-benchmark-scores" is '[2 Router] Model quality scores from Artificial Analysis. Written by nightly benchmark refresh (CI). Read by router and ranking script.';
create view "ims"."20_aa_performance_metrics" with (security_invoker = true) as select * from justask."20_router-benchmark-scores";
comment on view "ims"."20_aa_performance_metrics" is 'Compatibility view for justask.20_router-benchmark-scores. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '20_router-benchmark-scores' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'ims', '20_aa_performance_metrics', g.grantee);
  end loop; end $$;
alter table "ims"."10_model_aa_mapping" set schema justask;
alter table justask."10_model_aa_mapping" rename to "21_router-model-benchmark-map";
comment on table justask."21_router-model-benchmark-map" is '[2 Router] Links each model to its Artificial Analysis entry. Written by registry deploy step (CI). Read by router and ranking script.';
create view "ims"."10_model_aa_mapping" with (security_invoker = true) as select * from justask."21_router-model-benchmark-map";
comment on view "ims"."10_model_aa_mapping" is 'Compatibility view for justask.21_router-model-benchmark-map. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '21_router-model-benchmark-map' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'ims', '10_model_aa_mapping', g.grantee);
  end loop; end $$;
alter table "ims"."30_rate_limits" set schema justask;
alter table justask."30_rate_limits" rename to "22_router-provider-rate-limits";
comment on table justask."22_router-provider-rate-limits" is '[2 Router] Provider rate limits. Written by registry refresh step (CI) and populate_rate_limits.js. Read by router and ranking script.';
create view "ims"."30_rate_limits" with (security_invoker = true) as select * from justask."22_router-provider-rate-limits";
comment on view "ims"."30_rate_limits" is 'Compatibility view for justask.22_router-provider-rate-limits. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '22_router-provider-rate-limits' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'ims', '30_rate_limits', g.grantee);
  end loop; end $$;
alter table "ims"."40_model_selection_score" set schema justask;
alter table justask."40_model_selection_score" rename to "23_router-model-ranking";
comment on table justask."23_router-model-ranking" is '[2 Router] Final model ranking. Written by populate_model_selection_score.js (manual). Read by router /best-models.';
create view "ims"."40_model_selection_score" with (security_invoker = true) as select * from justask."23_router-model-ranking";
comment on view "ims"."40_model_selection_score" is 'Compatibility view for justask.23_router-model-ranking. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '23_router-model-ranking' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'ims', '40_model_selection_score', g.grantee);
  end loop; end $$;
alter table "public"."analytics_history" set schema justask;
alter table justask."analytics_history" rename to "30_analytics-daily-model-counts";
comment on table justask."30_analytics-daily-model-counts" is '[3 Analytics] Daily model-count snapshots. Written by nightly database job. Read by dashboard.';
create view "public"."analytics_history" with (security_invoker = true) as select * from justask."30_analytics-daily-model-counts";
comment on view "public"."analytics_history" is 'Compatibility view for justask.30_analytics-daily-model-counts. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '30_analytics-daily-model-counts' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'analytics_history', g.grantee);
  end loop; end $$;
alter table "public"."key_metadata" set schema justask;
alter table justask."key_metadata" rename to "40_api-keys-status";
comment on table justask."40_api-keys-status" is '[4 API key management, not in use since Sep 2025] Provider key status, expiry and rotation settings.';
create view "public"."key_metadata" with (security_invoker = true) as select * from justask."40_api-keys-status";
comment on view "public"."key_metadata" is 'Compatibility view for justask.40_api-keys-status. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '40_api-keys-status' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'key_metadata', g.grantee);
  end loop; end $$;
alter table "public"."usage_metrics" set schema justask;
alter table justask."usage_metrics" rename to "41_api-keys-usage";
comment on table justask."41_api-keys-usage" is '[4 API key management, not in use since Sep 2025] Usage counts per key and period.';
create view "public"."usage_metrics" with (security_invoker = true) as select * from justask."41_api-keys-usage";
comment on view "public"."usage_metrics" is 'Compatibility view for justask.41_api-keys-usage. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '41_api-keys-usage' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'usage_metrics', g.grantee);
  end loop; end $$;
alter table "public"."provider_rate_limits" set schema justask;
alter table justask."provider_rate_limits" rename to "42_api-keys-usage-limits";
comment on table justask."42_api-keys-usage-limits" is '[4 API key management, not in use since Sep 2025] Provider usage limits and warning thresholds.';
create view "public"."provider_rate_limits" with (security_invoker = true) as select * from justask."42_api-keys-usage-limits";
comment on view "public"."provider_rate_limits" is 'Compatibility view for justask.42_api-keys-usage-limits. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '42_api-keys-usage-limits' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'provider_rate_limits', g.grantee);
  end loop; end $$;
alter table "public"."notifications" set schema justask;
alter table justask."notifications" rename to "43_api-keys-alerts";
comment on table justask."43_api-keys-alerts" is '[4 API key management, not in use since Sep 2025] Usage, expiry and abuse alerts.';
create view "public"."notifications" with (security_invoker = true) as select * from justask."43_api-keys-alerts";
comment on view "public"."notifications" is 'Compatibility view for justask.43_api-keys-alerts. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '43_api-keys-alerts' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'notifications', g.grantee);
  end loop; end $$;
alter table "public"."audit_logs" set schema justask;
alter table justask."audit_logs" rename to "44_api-keys-audit-log";
comment on table justask."44_api-keys-audit-log" is '[4 API key management, not in use since Sep 2025] Record of key access and rotation.';
create view "public"."audit_logs" with (security_invoker = true) as select * from justask."44_api-keys-audit-log";
comment on view "public"."audit_logs" is 'Compatibility view for justask.44_api-keys-audit-log. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '44_api-keys-audit-log' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'audit_logs', g.grantee);
  end loop; end $$;
alter table "public"."provider_metadata" set schema justask;
alter table justask."provider_metadata" rename to "50_catalog-providers";
comment on table justask."50_catalog-providers" is '[5 Detailed catalog, never filled in] Provider details and API configuration.';
create view "public"."provider_metadata" with (security_invoker = true) as select * from justask."50_catalog-providers";
comment on view "public"."provider_metadata" is 'Compatibility view for justask.50_catalog-providers. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '50_catalog-providers' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'provider_metadata', g.grantee);
  end loop; end $$;
alter table "public"."model_availability" set schema justask;
alter table justask."model_availability" rename to "51_catalog-model-availability";
comment on table justask."51_catalog-model-availability" is '[5 Detailed catalog, never filled in] Which providers serve each model.';
create view "public"."model_availability" with (security_invoker = true) as select * from justask."51_catalog-model-availability";
comment on view "public"."model_availability" is 'Compatibility view for justask.51_catalog-model-availability. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '51_catalog-model-availability' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'model_availability', g.grantee);
  end loop; end $$;
alter table "public"."pricing_data" set schema justask;
alter table justask."pricing_data" rename to "52_catalog-model-pricing";
comment on table justask."52_catalog-model-pricing" is '[5 Detailed catalog, never filled in] Per-provider model pricing.';
create view "public"."pricing_data" with (security_invoker = true) as select * from justask."52_catalog-model-pricing";
comment on view "public"."pricing_data" is 'Compatibility view for justask.52_catalog-model-pricing. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '52_catalog-model-pricing' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'pricing_data', g.grantee);
  end loop; end $$;
alter table "public"."quality_metrics" set schema justask;
alter table justask."quality_metrics" rename to "53_catalog-model-quality";
comment on table justask."53_catalog-model-quality" is '[5 Detailed catalog, never filled in] Model quality scores from Artificial Analysis.';
create view "public"."quality_metrics" with (security_invoker = true) as select * from justask."53_catalog-model-quality";
comment on view "public"."quality_metrics" is 'Compatibility view for justask.53_catalog-model-quality. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '53_catalog-model-quality' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'quality_metrics', g.grantee);
  end loop; end $$;
alter table "public"."models" set schema justask;
alter table justask."models" rename to "60_mvp-model-benchmark-map";
comment on table justask."60_mvp-model-benchmark-map" is '[6 MVP model map, not in use] Text models mapped to Artificial Analysis. 21_router-model-benchmark-map serves this role now.';
create view "public"."models" with (security_invoker = true) as select * from justask."60_mvp-model-benchmark-map";
comment on view "public"."models" is 'Compatibility view for justask.60_mvp-model-benchmark-map. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '60_mvp-model-benchmark-map' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'public', 'models', g.grantee);
  end loop; end $$;
alter table "asa"."analysis_cache" set schema justask;
alter table justask."analysis_cache" rename to "70_external-stock-analysis-cache";
comment on table justask."70_external-stock-analysis-cache" is '[7 External app, not JustAsk] Stock ticker and company analysis cache. The app logs in as postgres.';
create view "asa"."analysis_cache" with (security_invoker = true) as select * from justask."70_external-stock-analysis-cache";
comment on view "asa"."analysis_cache" is 'Compatibility view for justask.70_external-stock-analysis-cache. Drop after all code uses the new name.';
do $$ declare g record; begin
  for g in select grantee, string_agg(privilege_type, ', ') as privs from information_schema.role_table_grants
           where table_schema = 'justask' and table_name = '70_external-stock-analysis-cache' and grantee not in ('postgres','supabase_admin') group by grantee loop
    execute format('grant %s on %I.%I to %I', g.privs, 'asa', 'analysis_cache', g.grantee);
  end loop; end $$;
notify pgrst, 'reload schema';
commit;
