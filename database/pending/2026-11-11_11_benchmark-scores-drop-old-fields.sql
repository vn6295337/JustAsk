-- NOT APPLIED. Apply only after the new refresh_aa_performance_metrics.py (which no longer writes these
-- columns) is merged to main AND the router code that selected math_index is merged. Otherwise the nightly
-- refresh fails (it rolls back and keeps old data) and the router's /best-model query errors.
-- Step 2 of 2 of aligning justask."20_router-benchmark-scores" with the Artificial Analysis Free API.
begin;
alter table justask."20_router-benchmark-scores"
  drop column creator_slug,                        -- Pro only
  drop column math_index,                          -- not in the API on any tier
  drop column mmlu_pro,                            -- not in the API on any tier
  drop column livecodebench,                       -- not in the API on any tier
  drop column math_500,                            -- not in the API on any tier
  drop column aime,                                -- not in the API on any tier
  drop column aime_25,                             -- not in the API on any tier
  drop column gpqa,                                -- Pro only (now gpqa_diamond)
  drop column hle,                                 -- Pro only
  drop column scicode,                             -- Pro only
  drop column ifbench,                             -- Pro only
  drop column lcr,                                 -- Pro only (now aa_lcr)
  drop column terminalbench_hard,                  -- Pro only (now terminalbench_v2_1 / v4_0)
  drop column tau2,                                -- Pro only (now tau2_telecom / tau_banking)
  drop column price_1m_blended,                    -- computed by us, not an AA field
  drop column median_output_tokens_per_second,     -- AA "performance": null from 2026-12-10; replaced by mean_* (performance_v3)
  drop column median_time_to_first_token_seconds,  -- same
  drop column median_time_to_first_answer_token;   -- same
notify pgrst, 'reload schema';
commit;
