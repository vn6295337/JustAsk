-- Applied 2026-11-11 via the Supabase Management API.
-- Option A (staging = incoming only, live = outgoing only): give 11 the same columns as 10,
-- so readers of the model list never need the staging table. Backfill from 10 (1:1 on provider + name).
begin;
alter table justask."11_free-models-live" add column provider_slug text;
update justask."11_free-models-live" l
   set provider_slug = s.provider_slug
  from justask."10_free-models-staging" s
 where s.inference_provider = l.inference_provider
   and s.human_readable_name = l.human_readable_name;
do $$ begin
  if exists (select 1 from justask."11_free-models-live" where provider_slug is null or provider_slug = '') then
    raise exception 'backfill incomplete: 11 has rows without provider_slug';
  end if;
end $$;
notify pgrst, 'reload schema';
commit;
