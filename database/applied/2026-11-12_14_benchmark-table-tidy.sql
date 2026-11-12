-- Applied 2026-11-12 via the Supabase Management API.
-- Tidy justask."20_router-benchmark-scores": current description, names that match the table,
-- no no-op policy, no unused authenticated permission, no duplicate index.
begin;
-- 1. Description (the router is no longer called since #17)
comment on table justask."20_router-benchmark-scores" is '[2 Router] Model scores, prices and speed from the Artificial Analysis Free API (/api/v2/language/models/free), one column per Free-tier field. Written daily by the benchmark refresh (CI), whole table replaced. Read by the ranking script (23) and the registry AA mapping (21).';

-- 2. Names left over from when the table was aa_performance_metrics
alter table justask."20_router-benchmark-scores" rename constraint aa_performance_metrics_pkey            to router_benchmark_scores_pkey;
alter table justask."20_router-benchmark-scores" rename constraint aa_performance_metrics_aa_model_id_key to router_benchmark_scores_aa_model_id_key;
alter table justask."20_router-benchmark-scores" rename constraint aa_performance_metrics_slug_key        to router_benchmark_scores_aa_slug_key;
alter index justask.idx_aa_metrics_intelligence rename to router_benchmark_scores_intelligence_index_idx;
alter trigger update_aa_performance_metrics_updated_at on justask."20_router-benchmark-scores" rename to router_benchmark_scores_set_updated_at;

-- 3. No-op policy: service_role bypasses RLS. Read access for anon comes from "Allow public read access".
drop policy "Allow service role full access" on justask."20_router-benchmark-scores";

-- 4. No one logs in as authenticated
revoke select on justask."20_router-benchmark-scores" from authenticated;

-- 5. Duplicate index: same column (aa_slug) as the unique key router_benchmark_scores_aa_slug_key
drop index justask.idx_aa_metrics_slug;

notify pgrst, 'reload schema';
commit;
