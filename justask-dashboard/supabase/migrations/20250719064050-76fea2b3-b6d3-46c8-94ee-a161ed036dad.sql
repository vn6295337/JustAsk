-- Create table for caching model validation data
CREATE TABLE public.model_validations (
  id TEXT PRIMARY KEY,
  data JSONB NOT NULL,
  source TEXT NOT NULL,
  fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.model_validations ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access (for caching fallback)
CREATE POLICY "Public read access for model validations" 
ON public.model_validations 
FOR SELECT 
USING (true);

-- Create policy to allow public insert/update (for caching)
CREATE POLICY "Public write access for model validations" 
ON public.model_validations 
FOR ALL
USING (true)
WITH CHECK (true);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_model_validations_updated_at
BEFORE UPDATE ON public.model_validations
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();