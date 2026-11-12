-- Applied 2026-11-12 via the Supabase Management API.
-- Show times in IST: default session time zone for the whole database. Stored timestamptz values are
-- exact moments and do not change; only how they are shown. Applies to new connections.
alter database postgres set timezone to 'Asia/Kolkata';
