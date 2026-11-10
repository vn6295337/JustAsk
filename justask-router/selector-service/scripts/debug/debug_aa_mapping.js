#!/usr/bin/env node
/**
 * Debug AA mapping mismatches
 */

import 'dotenv/config';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

async function debugMapping() {
  // Get model-aa mapping
  const { data: mappings } = await supabase
    .schema('justask')
    .from('21_router-model-benchmark-map')
    .select('*');

  // Get all AA performance metrics
  const { data: metrics } = await supabase
    .schema('justask')
    .from('20_router-benchmark-scores')
    .select('aa_slug, intelligence_index, name');

  const metricsMap = {};
  metrics.forEach(m => {
    metricsMap[m.aa_slug] = m;
  });

  console.log(`\n📊 Mapping Table Analysis:`);
  console.log(`   Total mappings in justask."21_router-model-benchmark-map": ${mappings.length}`);
  console.log(`   Total metrics in justask."20_router-benchmark-scores": ${metrics.length}`);
  console.log();

  // Check which mappings have corresponding metrics
  const withMetrics = [];
  const withoutMetrics = [];

  mappings.forEach(mapping => {
    if (metricsMap[mapping.aa_slug]) {
      withMetrics.push({
        ...mapping,
        aa_name: metricsMap[mapping.aa_slug].name,
        intelligence_index: metricsMap[mapping.aa_slug].intelligence_index
      });
    } else {
      withoutMetrics.push(mapping);
    }
  });

  console.log(`✅ Mappings WITH corresponding AA metrics (${withMetrics.length}):`);
  console.log('='.repeat(80));
  withMetrics.forEach((m, idx) => {
    console.log(`${idx + 1}. ${m.inference_provider}:${m.provider_slug} → ${m.aa_slug}`);
    console.log(`   AA Name: ${m.aa_name}`);
    console.log(`   Intelligence: ${m.intelligence_index}`);
    console.log();
  });

  console.log(`\n❌ Mappings WITHOUT corresponding AA metrics (${withoutMetrics.length}):`);
  console.log('='.repeat(80));
  withoutMetrics.forEach((m, idx) => {
    console.log(`${idx + 1}. ${m.inference_provider}:${m.provider_slug} → ${m.aa_slug}`);
    console.log(`   Mapping exists but aa_slug "${m.aa_slug}" not found in metrics table`);

    // Check if similar slug exists in metrics
    const similar = metrics.filter(metric =>
      metric.aa_slug.includes(m.aa_slug.substring(0, 10)) ||
      m.aa_slug.includes(metric.aa_slug.substring(0, 10))
    ).slice(0, 3);

    if (similar.length > 0) {
      console.log(`   Similar slugs in metrics table:`);
      similar.forEach(s => console.log(`     - ${s.aa_slug} (${s.name})`));
    }
    console.log();
  });

  // Show when mapping was last updated
  if (mappings.length > 0 && mappings[0].updated_at) {
    console.log(`\n📅 Mapping table last updated: ${mappings[0].updated_at}`);
  }
}

debugMapping();
