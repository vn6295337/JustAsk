-- Applied 2026-11-12 via the Supabase Management API (session time zone UTC).
-- justask."21_router-model-benchmark-map": created_at / updated_at become "timestamp with time zone".
-- Existing values were written as UTC clock times (datetime.utcnow()), so they are read as UTC.
begin;
alter table justask."21_router-model-benchmark-map"
  alter column created_at type timestamptz using created_at at time zone 'UTC',
  alter column updated_at type timestamptz using updated_at at time zone 'UTC';
alter table justask."21_router-model-benchmark-map"
  alter column created_at set default now(),
  alter column updated_at set default now();
notify pgrst, 'reload schema';
commit;
