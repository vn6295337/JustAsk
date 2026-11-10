-- Applied 2026-11-10 via the Supabase Management API.
-- Point the analytics functions at the new table names.
begin;
CREATE OR REPLACE FUNCTION public.collect_daily_analytics()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_temp'
AS $function$
  DECLARE
    v_total_models INTEGER;
    v_inference_providers JSONB;
    v_model_providers JSONB;
  BEGIN
    -- Count total models
    SELECT COUNT(*)
    INTO v_total_models
    FROM justask."11_free-models-live";

    -- Calculate inference provider counts
    SELECT jsonb_object_agg(
      COALESCE(inference_provider, 'Unknown'),
      count
    )
    INTO v_inference_providers
    FROM (
      SELECT
        inference_provider,
        COUNT(*) as count
      FROM justask."11_free-models-live"
      GROUP BY inference_provider
    ) subq;

    -- Calculate model provider counts
    SELECT jsonb_object_agg(
      COALESCE(model_provider, 'Unknown'),
      count
    )
    INTO v_model_providers
    FROM (
      SELECT
        model_provider,
        COUNT(*) as count
      FROM justask."11_free-models-live"
      GROUP BY model_provider
    ) subq;

    -- Save snapshot using existing RPC function
    PERFORM public.insert_analytics_snapshot(
      v_total_models,
      v_inference_providers,
      v_model_providers
    );

    RAISE NOTICE 'Analytics snapshot collected: % models', v_total_models;
  END;
  $function$

;
CREATE OR REPLACE FUNCTION public.insert_analytics_snapshot(p_total_models integer, p_inference_provider_counts jsonb, p_model_provider_counts jsonb)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_temp'
AS $function$
  DECLARE
    today_date DATE;
    existing_id INTEGER;
  BEGIN
    today_date := CURRENT_DATE;

    SELECT id INTO existing_id
    FROM justask."30_analytics-daily-model-counts"
    WHERE DATE(timestamp) = today_date
    LIMIT 1;

    IF existing_id IS NOT NULL THEN
      UPDATE justask."30_analytics-daily-model-counts"
      SET
        timestamp = now(),
        total_models = p_total_models,
        inference_provider_counts = p_inference_provider_counts,
        model_provider_counts = p_model_provider_counts
      WHERE id = existing_id;
      RETURN true;
    ELSE
      INSERT INTO justask."30_analytics-daily-model-counts" (
        total_models,
        inference_provider_counts,
        model_provider_counts
      ) VALUES (
        p_total_models,
        p_inference_provider_counts,
        p_model_provider_counts
      );
      RETURN true;
    END IF;
  END;
  $function$

;
commit;
