-- Applied 2026-11-12 via the Supabase Management API.
-- Tidy justask."10_free-models-staging": current description, names that match the table, no no-op policy.
begin;
-- 1. Description
comment on table justask."10_free-models-staging" is '[1 Free models] Draft model list (incoming only). Written daily by the registry pipeline refresh step (CI). Read only by the registry compare step (daily) and publish step (manual). Same columns as 11_free-models-live.';

-- 2. Names left over from old copies of the table (working_version_duplicate_duplicate_*)
alter table justask."10_free-models-staging" rename constraint working_version_duplicate_duplicate_pkey to free_models_staging_pkey;
alter index justask.working_version_duplicate_duplicate_created_at_idx          rename to free_models_staging_created_at_idx;
alter index justask.working_version_duplicate_duplicate_human_readable_name_idx rename to free_models_staging_human_readable_name_idx;
alter index justask.working_version_duplicate_duplicate_inference_provider_idx  rename to free_models_staging_inference_provider_idx;
alter index justask.working_version_duplicate_duplicate_model_provider_idx      rename to free_models_staging_model_provider_idx;
alter index justask.idx_working_version_provider_slug                           rename to free_models_staging_provider_slug_idx;
alter sequence justask.working_version_duplicate_duplicate_id_seq               rename to free_models_staging_id_seq;

-- 4. No-op policy: pipeline_writer has BYPASSRLS, so this policy never applied. Access is controlled by grants.
drop policy "Pipeline full access working" on justask."10_free-models-staging";

notify pgrst, 'reload schema';
commit;
