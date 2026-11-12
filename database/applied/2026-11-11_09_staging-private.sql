-- Applied 2026-11-12 via the Supabase Management API, after the router on Render was redeployed reading 11.
-- Verified: anon gets "permission denied" on 10 and still reads 11 (58 rows); router /best-model works.
-- Option A: 10_free-models-staging is incoming only. Public roles lose read access; only pipeline_writer
-- (CI) and service_role keep it. tests/integration/test_rls_policies.py Test 3 expects this.
begin;
revoke select on justask."10_free-models-staging" from anon, authenticated;
drop policy "Allow public read access" on justask."10_free-models-staging";
notify pgrst, 'reload schema';
commit;
