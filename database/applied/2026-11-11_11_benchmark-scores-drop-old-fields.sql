-- Applied 2026-11-12 via the Supabase Management API, after PR #12 was merged and the AA refresh
-- (run 43140060439) filled the new columns. All 18 dropped columns were empty in all 122 rows.
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
