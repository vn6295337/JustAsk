-- Create table for storing historical analytics data
CREATE TABLE public.analytics_history (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  total_models INTEGER NOT NULL,
  inference_provider_counts JSONB NOT NULL,
  model_provider_counts JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create index on timestamp for efficient time-range queries
CREATE INDEX idx_analytics_history_timestamp ON public.analytics_history(timestamp);

-- Enable Row Level Security
ALTER TABLE public.analytics_history ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access
CREATE POLICY "Public read access for analytics history" 
ON public.analytics_history 
FOR SELECT 
USING (true);

-- Create policy to allow public insert (for data collection)
CREATE POLICY "Public insert access for analytics history" 
ON public.analytics_history 
FOR INSERT
WITH CHECK (true);

-- Function to insert analytics snapshot (keeps only latest record per day)
CREATE OR REPLACE FUNCTION public.insert_analytics_snapshot(
  p_total_models INTEGER,
  p_inference_provider_counts JSONB,
  p_model_provider_counts JSONB
) RETURNS BOOLEAN AS $$
DECLARE
  today_date DATE;
  existing_id INTEGER;
BEGIN
  -- Get today's date in UTC
  today_date := CURRENT_DATE;

  -- Check if a record for today already exists
  SELECT id INTO existing_id
  FROM public.analytics_history
  WHERE DATE(timestamp) = today_date
  LIMIT 1;

  IF existing_id IS NOT NULL THEN
    -- Update existing record for today with latest data
    UPDATE public.analytics_history
    SET
      timestamp = now(),
      total_models = p_total_models,
      inference_provider_counts = p_inference_provider_counts,
      model_provider_counts = p_model_provider_counts
    WHERE id = existing_id;
    RETURN true;
  ELSE
    -- Insert new record for today
    INSERT INTO public.analytics_history (
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
$$ LANGUAGE plpgsql SECURITY DEFINER;