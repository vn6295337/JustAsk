# Database Security (Supabase RLS)

## Overview

Row Level Security (RLS) protects database tables:
- `ai_models_main` - Public read, pipeline write
- `working_version` - Pipeline access only (private)

## Roles

| Role | Purpose | Access |
|------|---------|--------|
| `anon` | Frontend/public | Read `ai_models_main` only |
| `pipeline_writer` | Pipeline scripts | Full access to both tables |

## SQL Setup

```sql
-- Enable RLS
ALTER TABLE ai_models_main ENABLE ROW LEVEL SECURITY;
ALTER TABLE working_version ENABLE ROW LEVEL SECURITY;

-- Public read for ai_models_main
CREATE POLICY "Public read" ON ai_models_main
  FOR SELECT TO anon USING (true);

-- Create pipeline_writer role
CREATE ROLE pipeline_writer LOGIN PASSWORD 'YOUR_SECURE_PASSWORD';
GRANT USAGE ON SCHEMA public TO pipeline_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_models_main TO pipeline_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON working_version TO pipeline_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pipeline_writer;

-- Full access policies for pipeline_writer
CREATE POLICY "Pipeline full access main" ON ai_models_main
  FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);

CREATE POLICY "Pipeline full access working" ON working_version
  FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);
```

## Environment Variables

Pipeline scripts require:
```bash
PIPELINE_SUPABASE_URL=postgresql://pipeline_writer:PASSWORD@db.PROJECT.supabase.co:5432/postgres
```

Add to:
- `.env.local` for local development
- GitHub Actions secrets for CI/CD

## Rate Limits Table (Optional)

If using `ims.30_rate_limits`:
```sql
GRANT USAGE ON SCHEMA ims TO pipeline_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ims."30_rate_limits" TO pipeline_writer;
GRANT USAGE, SELECT ON SEQUENCE ims.rate_limits_id_seq TO pipeline_writer;
```

## Verification

```sql
-- Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables 
WHERE tablename IN ('ai_models_main', 'working_version');

-- Check policies
SELECT * FROM pg_policies 
WHERE tablename IN ('ai_models_main', 'working_version');

-- Check role exists
SELECT rolname FROM pg_roles WHERE rolname = 'pipeline_writer';
```
