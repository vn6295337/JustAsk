-- Applied 2026-11-11 via the Supabase Management API.
-- Align justask."20_router-benchmark-scores" with the Artificial Analysis Free API
-- (/api/v2/language/models/free). Step 1 of 2: add the Free-tier fields not stored yet.
-- Additive only: the current nightly refresh keeps working (new columns stay NULL until the new script runs).
-- Names: AA leaf names without the "artificial_analysis_" prefix.
begin;
alter table justask."20_router-benchmark-scores"
  add column intelligence_index_version         numeric,  -- response-level intelligence_index_version
  add column creator_id                         uuid,     -- model_creator.id
  add column agentic_index                      numeric,  -- evaluations.artificial_analysis_agentic_index (AA: always null)
  add column finance_and_accounting_index       numeric,  -- evaluations.artificial_analysis_finance_and_accounting_index
  add column strategy_and_ops_index             numeric,  -- evaluations.artificial_analysis_strategy_and_ops_index
  add column legal_index                        numeric,  -- evaluations.artificial_analysis_legal_index
  add column healthcare_and_medical_index       numeric,  -- evaluations.artificial_analysis_healthcare_and_medical_index
  add column engineering_index                  numeric,  -- evaluations.artificial_analysis_engineering_index
  add column economics_index                    numeric,  -- evaluations.artificial_analysis_economics_index
  add column intelligence_index_cost_total      numeric,  -- artificial_analysis_intelligence_index_cost.total_cost (USD)
  add column intelligence_index_cost_per_task   numeric,  -- artificial_analysis_intelligence_index_cost.cost_per_task.total_cost (USD)
  add column price_1m_cache_hit_tokens          numeric,  -- pricing.price_1m_cache_hit_tokens
  add column price_1m_cache_write_tokens        numeric,  -- pricing.price_1m_cache_write_tokens
  add column mean_output_tokens_per_second      numeric,  -- performance_v3.mean_output_tokens_per_second
  add column mean_time_to_first_token_seconds   numeric,  -- performance_v3.mean_time_to_first_token_seconds
  add column mean_time_to_first_answer_token_seconds numeric; -- performance_v3.mean_time_to_first_answer_token_seconds
comment on column justask."20_router-benchmark-scores".coding_index is 'evaluations.artificial_analysis_coding_index. AA no longer publishes it: always null. Kept to match the API.';
comment on column justask."20_router-benchmark-scores".agentic_index is 'evaluations.artificial_analysis_agentic_index. AA no longer publishes it: always null. Kept to match the API.';
comment on table justask."20_router-benchmark-scores" is '[2 Router] Model scores, prices and speed from the Artificial Analysis Free API (/api/v2/language/models/free), one column per Free-tier field. Written by nightly benchmark refresh (CI). Read by router, ranking script and registry mapping.';
notify pgrst, 'reload schema';
commit;
