-- Applied 2026-11-10 via the Supabase Management API.
-- Let pipeline_writer write the two router tables it lacked, so CI no longer needs the postgres role. Password was reset separately (not recorded).
begin;
grant select, insert, update, delete on ims."10_model_aa_mapping" to pipeline_writer;
grant usage on sequence ims.model_aa_mapping_id_seq to pipeline_writer;
grant select, insert, delete on ims."20_aa_performance_metrics" to pipeline_writer;
commit;
