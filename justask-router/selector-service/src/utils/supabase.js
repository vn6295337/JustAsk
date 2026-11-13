/**
 * Supabase database utilities for querying 11_free-models-live table
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

// Initialize Supabase client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('SUPABASE_URL and SUPABASE_KEY must be set in environment variables');
}

const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * Fetch all models from 11_free-models-live table with AA performance metrics and rate limits
 * Uses 4-table lookup: 11_free-models-live → model_aa_mapping → aa_performance_metrics
 *                                      → rate_limits
 * @returns {Promise<Array>} Array of model objects
 */
export async function fetchLatestModels() {
  try {
    // Fetch all models from 11_free-models-live
    const { data: models, error: modelsError } = await supabase
      .schema('justask').from('11_free-models-live')
      .select('*')
      .order('updated_at', { ascending: false });

    if (modelsError) {
      throw new Error(`Supabase query error: ${modelsError.message}`);
    }

    // Fetch model provider_slug → AA slug mappings
    const { data: mappings, error: mappingsError } = await supabase
      .schema('justask')
      .from('21_router-model-benchmark-map')
      .select('provider_slug, aa_slug, inference_provider')
      .in('status', ['linked', 'linked_effort_unknown']);

    if (mappingsError) {
      throw new Error(`Supabase query error: ${mappingsError.message}`);
    }

    // Fetch all AA performance metrics
    const { data: metrics, error: metricsError } = await supabase
      .schema('justask')
      .from('20_router-benchmark-scores')
      .select('aa_slug, intelligence_index, coding_index, name');

    if (metricsError) {
      throw new Error(`Supabase query error: ${metricsError.message}`);
    }

    // Fetch all rate limits
    const { data: rateLimits, error: rateLimitsError } = await supabase
      .schema('justask')
      .from('22_router-provider-rate-limits')
      .select('human_readable_name, rpm, rpd, tpm, tpd, parseable');

    if (rateLimitsError) {
      throw new Error(`Supabase query error: ${rateLimitsError.message}`);
    }

    // Create lookup maps using provider_slug + inference_provider as composite key
    const mappingMap = {};
    (mappings || []).forEach(m => {
      const key = `${m.inference_provider}:${m.provider_slug}`;
      mappingMap[key] = m.aa_slug;
    });

    const metricsMap = {};
    (metrics || []).forEach(m => {
      metricsMap[m.aa_slug] = m;
    });

    const rateLimitsMap = {};
    (rateLimits || []).forEach(r => {
      rateLimitsMap[r.human_readable_name] = r;
    });

    // 4-table join: 11_free-models-live → model_aa_mapping → aa_performance_metrics
    //                               → rate_limits
    const modelsWithMetrics = (models || []).map(model => {
      // Table 21 stores table 11's original provider_slug
      const lookupKey = `${model.inference_provider}:${model.provider_slug}`;
      const aaSlug = mappingMap[lookupKey];
      const aaMetrics = aaSlug ? metricsMap[aaSlug] : null;
      const rateLimitsData = rateLimitsMap[model.human_readable_name] || null;

      return {
        ...model,
        aa_slug: aaSlug || null,
        aa_performance_metrics: aaMetrics || null,
        rate_limits_normalized: rateLimitsData
      };
    });

    return modelsWithMetrics;
  } catch (error) {
    console.error('Error fetching models from Supabase:', error);
    throw error;
  }
}

/**
 * Test Supabase connection
 * @returns {Promise<boolean>} True if connection successful
 */
export async function testConnection() {
  try {
    const { data, error } = await supabase
      .schema('justask').from('11_free-models-live')
      .select('id')
      .limit(1);

    if (error) {
      console.error('Supabase connection test failed:', error);
      return false;
    }

    return true;
  } catch (error) {
    console.error('Supabase connection test error:', error);
    return false;
  }
}

export default supabase;
