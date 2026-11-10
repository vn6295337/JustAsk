// Supabase client. Requires VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY (see .env.example).
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { Database } from './types';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) {
  throw new Error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY environment variable');
}

// Import the supabase client like this:
// import { supabase } from "@/integrations/supabase/client";

// Public read-only usage: no auth session needed.
export const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
  },
});

// JustAsk tables live in the "justask" schema (names: docs/database-map.md).
// Generated types cover "public" only, so this client is untyped.
export const justaskDb = (supabase as unknown as SupabaseClient).schema('justask');
