-- NOT APPLIED. Apply only after the router reading 11 is live on Render and /select-model is verified.
-- Option A: 10_free-models-staging is incoming only. Public roles lose read access; only pipeline_writer
-- (CI) and service_role keep it. tests/integration/test_rls_policies.py Test 3 expects this.
begin;
revoke select on justask."10_free-models-staging" from anon, authenticated;
drop policy "Allow public read access" on justask."10_free-models-staging";
notify pgrst, 'reload schema';
commit;
