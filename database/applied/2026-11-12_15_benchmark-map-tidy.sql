-- Applied 2026-11-12 via the Supabase Management API.
-- Tidy justask."21_router-model-benchmark-map": current description, names that match the table,
-- no unused authenticated permission. (Timestamp type change: separate, pending a decision.)
begin;
-- A1. Description (the router is no longer called since #17)
comment on table justask."21_router-model-benchmark-map" is '[2 Router] Links each model (inference_provider + provider_slug) to its Artificial Analysis entry (aa_slug in 20). Rebuilt for a provider by the registry publish step (CI), from 11_free-models-live. Read by the ranking script (23).';

-- A2. Names left over from when the table was ims.model_aa_mapping
alter table justask."21_router-model-benchmark-map" rename constraint model_aa_mapping_pkey to router_model_benchmark_map_pkey;
alter table justask."21_router-model-benchmark-map" rename constraint unique_provider_model to router_model_benchmark_map_provider_slug_key;
alter index justask.idx_ims_model_aa_mapping_slug        rename to router_model_benchmark_map_aa_slug_idx;
alter index justask.idx_model_aa_mapping_provider_slug   rename to router_model_benchmark_map_provider_slug_idx;
alter sequence justask.model_aa_mapping_id_seq           rename to router_model_benchmark_map_id_seq;

-- A3. No one logs in as authenticated
revoke select on justask."21_router-model-benchmark-map" from authenticated;

notify pgrst, 'reload schema';
commit;
