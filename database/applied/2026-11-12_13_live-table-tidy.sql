-- Applied 2026-11-12 via the Supabase Management API.
-- Tidy justask."11_free-models-live" and let the database enforce the publish rules.
begin;
-- 1. Description
comment on table justask."11_free-models-live" is '[1 Free models] Published model list (outgoing only). Written only by the registry publish step (manual), copied from 10_free-models-staging. Read by the registry compare step, the AA mapping refresh (21), the nightly analytics job (30), the dashboard and the ranking script. Same columns as 10_free-models-staging.';

-- 2. Names left over from old copies of the table (ai_models_main_working_version_*)
alter table justask."11_free-models-live" rename constraint ai_models_main_working_version_pkey to free_models_live_pkey;
alter index justask.ai_models_main_working_version_created_at_idx          rename to free_models_live_created_at_idx;
alter index justask.ai_models_main_working_version_human_readable_name_idx rename to free_models_live_human_readable_name_idx;
alter index justask.ai_models_main_working_version_inference_provider_idx  rename to free_models_live_inference_provider_idx;
alter index justask.ai_models_main_working_version_model_provider_idx      rename to free_models_live_model_provider_idx;
alter sequence justask.ai_models_main_working_version_id_seq               rename to free_models_live_id_seq;

-- 3. No-op policy: pipeline_writer has BYPASSRLS, so this policy never applied. Access is controlled by grants.
drop policy "Pipeline full access main" on justask."11_free-models-live";

-- 4. authenticated had SELECT but no policy, so it could not read anyway; no one logs in as authenticated.
revoke select on justask."11_free-models-live" from authenticated;

-- 5. Enforce the publish rules in the database too (the publish gate already checks them).
alter table justask."11_free-models-live" alter column provider_slug set not null;
alter table justask."11_free-models-live" alter column rate_limits   set not null;
alter table justask."11_free-models-live" add constraint free_models_live_provider_slug_key unique (inference_provider, provider_slug);

notify pgrst, 'reload schema';
commit;
