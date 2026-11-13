/**
 * Populate Model Selection Score Table
 *
 * Script to populate justask."23_router-model-ranking" with consolidated data
 * from 11_free-models-live, model_aa_mapping, aa_performance_metrics, and rate_limits
 *
 * Only includes models that exist in justask."21_router-model-benchmark-map" (i.e., have AA metrics)
 *
 * Usage: node populate_model_selection_score.js [--no-prune]
 * Requires SUPABASE_SERVICE_KEY. Run manually; do not add to CI.
 * By default rows not in the new set are deleted (use --no-prune to keep them).
 *
 * Scoring mirrors the runtime (src/services/modelSelector.js, intelligenceIndex.js).
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];

const PRUNE = !process.argv.includes('--no-prune');

let supabase = null;

// Scoring weights (decided 2026-11-11). Speed was removed: it was a fixed guess
// per provider, not a measurement. Its 25% was shared out proportionally.
export const SELECTION_WEIGHTS = {
  intelligenceIndex: 0.47,
  freeLimitRoom: 0.33,
  geography: 0.13,
  license: 0.07
};

// Room score for a model whose daily request limit (rpd) is not published
export const UNKNOWN_LIMIT_ROOM_SCORE = 0.5;

// Table 21 statuses whose AA entry has an intelligence score (see justask-registry model_aa_mapping.py)
export const SCORED_LINK_STATUSES = ['linked', 'linked_effort_unknown'];

const LATENCY_SCORES = {
  groq: 1.0,
  gemini: 0.8,
  google: 0.8,
  openrouter: 0.6
};

const GEOGRAPHY_SCORES = {
  'United States': 1.0,
  'default': 0.9
};

const OPEN_SOURCE_LICENSES = [
  'MIT', 'Apache-2.0', 'GPL-3.0', 'BSD-3-Clause',
  'Llama-2', 'Llama-3', 'Llama-3.1', 'Llama-3.2', 'Llama-3.3', 'Llama-4',
  'Gemma', 'CC0-1.0', 'CC-BY-4.0', 'CC-BY-SA-4.0'
];

/**
 * Calculate geography score based on country
 */
function calculateGeographyScore(country) {
  return GEOGRAPHY_SCORES[country] || GEOGRAPHY_SCORES['default'];
}

/**
 * Calculate license score based on license name
 */
function calculateLicenseScore(licenseName) {
  // Mirrors runtime getLicenseScore: exact open-source match, gemini = proprietary, else custom
  if (!licenseName) return 0.9;

  const normalized = licenseName.trim();
  if (OPEN_SOURCE_LICENSES.includes(normalized)) return 1.0;
  if (normalized.toLowerCase().includes('gemini')) return 0.8;
  return 0.9;
}

/**
 * Calculate latency score based on provider
 */
function calculateLatencyScore(provider) {
  return LATENCY_SCORES[String(provider || '').toLowerCase()] || 0.5;
}

/**
 * Calculate headroom (0-1)
 */
function calculateHeadroom(limit, usage) {
  if (!limit || limit === 0) return 1.0; // Unlimited
  return Math.max(0, (limit - usage) / limit);
}

/**
 * Calculate overall headroom (minimum across all four metrics, as at runtime)
 */
function calculateOverallHeadroom(...headrooms) {
  return Math.min(...headrooms);
}

/**
 * Free-limit room score (0-1): the model's published daily request limit
 * relative to the largest daily limit among the ranked models.
 * Unknown limit -> UNKNOWN_LIMIT_ROOM_SCORE (not "unlimited").
 */
export function calculateFreeLimitRoom(rpdLimit, maxRpd) {
  if (!rpdLimit || rpdLimit <= 0 || !maxRpd || maxRpd <= 0) return UNKNOWN_LIMIT_ROOM_SCORE;
  return Math.min(1, rpdLimit / maxRpd);
}

/**
 * Calculate final selection score
 */
export function calculateSelectionScore(intelligenceIndex, freeLimitRoom, geographyScore, licenseScore) {
  // Normalize intelligence index to 0-1 scale (assume max is 100).
  // Missing index uses the runtime's moderate fallback (0.6), not 0.
  const normalizedIntelligence = intelligenceIndex != null ? intelligenceIndex / 100 : 0.6;

  return (
    normalizedIntelligence * SELECTION_WEIGHTS.intelligenceIndex +
    freeLimitRoom * SELECTION_WEIGHTS.freeLimitRoom +
    geographyScore * SELECTION_WEIGHTS.geography +
    licenseScore * SELECTION_WEIGHTS.license
  );
}

async function populateModelSelectionScore() {
  dotenv.config();
  // Writes require the service role key (anon is read-only). Manual, human-run script only.
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_KEY) {
    console.error('SUPABASE_URL and SUPABASE_SERVICE_KEY must be set (see .env.example). Aborting.');
    process.exit(1);
  }
  supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

  console.log('🚀 Starting model selection score population...\n');

  try {
    // Step 1: Fetch models with a scored AA link from justask."21_router-model-benchmark-map"
    // (status linked or linked_effort_unknown; provider_slug is table 11's original slug)
    console.log('📊 Fetching linked models from justask."21_router-model-benchmark-map"...');
    const { data: mappings, error: mappingsError } = await supabase
      .schema('justask')
      .from('21_router-model-benchmark-map')
      .select('provider_slug, aa_slug, inference_provider, status')
      .in('status', SCORED_LINK_STATUSES);

    if (mappingsError) {
      throw new Error(`Failed to fetch mappings: ${mappingsError.message}`);
    }

    console.log(`✅ Found ${mappings.length} mapped models\n`);

    // Step 2: Fetch 11_free-models-live data
    console.log('📊 Fetching model details from 11_free-models-live...');
    const { data: workingModels, error: workingError } = await supabase
      .schema('justask').from('11_free-models-live')
      .select('provider_slug, human_readable_name, model_provider, inference_provider, model_provider_country, license_name');

    if (workingError) {
      throw new Error(`Failed to fetch 11_free-models-live: ${workingError.message}`);
    }

    // Lookup by provider + original slug (the same slug can exist at two providers)
    const workingMap = {};
    workingModels.forEach(m => {
      workingMap[`${m.inference_provider}:${m.provider_slug}`] = m;
    });

    console.log(`✅ Fetched ${workingModels.length} models from 11_free-models-live\n`);

    // Step 3: Fetch aa_performance_metrics
    console.log('📊 Fetching performance metrics from justask."20_router-benchmark-scores"...');
    const { data: metrics, error: metricsError } = await supabase
      .schema('justask')
      .from('20_router-benchmark-scores')
      .select('aa_slug, intelligence_index');

    if (metricsError) {
      throw new Error(`Failed to fetch metrics: ${metricsError.message}`);
    }

    // Create lookup map
    const metricsMap = {};
    metrics.forEach(m => {
      metricsMap[m.aa_slug] = m;
    });

    console.log(`✅ Fetched ${metrics.length} performance metrics\n`);

    // Step 4: Fetch rate_limits
    console.log('📊 Fetching rate limits from justask."22_router-provider-rate-limits"...');
    const { data: rateLimits, error: rateLimitsError } = await supabase
      .schema('justask')
      .from('22_router-provider-rate-limits')
      .select('human_readable_name, rpm, rpd, tpm, tpd');

    if (rateLimitsError) {
      throw new Error(`Failed to fetch rate limits: ${rateLimitsError.message}`);
    }

    // Create lookup map
    const rateLimitsMap = {};
    rateLimits.forEach(r => {
      rateLimitsMap[r.human_readable_name] = r;
    });

    console.log(`✅ Fetched ${rateLimits.length} rate limit entries\n`);

    // Step 5: Build consolidated records
    console.log('🔨 Building consolidated records with scores...');
    const records = [];
    let skippedCount = 0;
    const skippedModels = [];
    const matchStats = {
      directMatch: 0,
      normalizedMatch: 0,
      noMatch: 0
    };

    for (const mapping of mappings) {
      const providerSlug = mapping.provider_slug;
      const workingData = workingMap[`${mapping.inference_provider}:${providerSlug}`];
      const metricsData = metricsMap[mapping.aa_slug];

      // Skip if missing critical data
      if (!workingData) {
        console.warn(`⚠️  Skipping ${mapping.inference_provider}:${providerSlug}: Not found in 11_free-models-live`);
        skippedCount++;
        skippedModels.push({
          provider: mapping.inference_provider,
          slug: providerSlug,
          aa_slug: mapping.aa_slug
        });
        matchStats.noMatch++;
        continue;
      }

      // Track match type for monitoring
      if (workingData.provider_slug === providerSlug) {
        matchStats.directMatch++;
      } else {
        matchStats.normalizedMatch++;
      }

      const modelName = workingData.human_readable_name;
      const rateLimitData = rateLimitsMap[modelName];

      // Calculate scores (latency_score is stored for reference only; not in the score)
      const intelligenceIndex = metricsData?.intelligence_index ?? null;
      const latencyScore = calculateLatencyScore(mapping.inference_provider);
      const geographyScore = calculateGeographyScore(workingData.model_provider_country);
      const licenseScore = calculateLicenseScore(workingData.license_name);

      // Rate limit headrooms (start at 1.0 = full capacity)
      const rpmLimit = rateLimitData?.rpm || null;
      const rpdLimit = rateLimitData?.rpd || null;
      const tpmLimit = rateLimitData?.tpm || null;
      const tpdLimit = rateLimitData?.tpd || null;

      const rpmUsage = 0;
      const rpdUsage = 0;
      const tpmUsage = 0;
      const tpdUsage = 0;

      const rpmHeadroom = calculateHeadroom(rpmLimit, rpmUsage);
      const rpdHeadroom = calculateHeadroom(rpdLimit, rpdUsage);
      const tpmHeadroom = calculateHeadroom(tpmLimit, tpmUsage);
      const tpdHeadroom = calculateHeadroom(tpdLimit, tpdUsage);

      // Usage is always 0 here, so these headrooms are 1.0 and do not rank anything.
      // overall_headroom is replaced below by the free-limit room score.
      const overallHeadroom = calculateOverallHeadroom(rpmHeadroom, rpdHeadroom, tpmHeadroom, tpdHeadroom);

      records.push({
        model_name: modelName,
        model_provider: workingData.model_provider,
        inference_provider: mapping.inference_provider,
        provider_slug: mapping.provider_slug,
        aa_slug: mapping.aa_slug,
        intelligence_index: intelligenceIndex,
        rpm_limit: rpmLimit,
        rpm_usage: rpmUsage,
        rpm_headroom: rpmHeadroom,
        rpd_limit: rpdLimit,
        rpd_usage: rpdUsage,
        rpd_headroom: rpdHeadroom,
        tpm_limit: tpmLimit,
        tpm_usage: tpmUsage,
        tpm_headroom: tpmHeadroom,
        tpd_limit: tpdLimit,
        tpd_usage: tpdUsage,
        tpd_headroom: tpdHeadroom,
        overall_headroom: overallHeadroom,
        latency_score: latencyScore,
        geography_score: geographyScore,
        license_score: licenseScore,
        selection_score: null // set below, once the largest daily limit is known
      });
    }

    // Step 5.1: Free-limit room and final scores
    const maxRpd = Math.max(0, ...records.map(r => r.rpd_limit || 0));
    console.log(`📏 Largest published daily limit among ranked models: ${maxRpd || 'none'} requests/day`);
    for (const r of records) {
      r.overall_headroom = calculateFreeLimitRoom(r.rpd_limit, maxRpd);
      r.selection_score = calculateSelectionScore(
        r.intelligence_index,
        r.overall_headroom,
        r.geography_score,
        r.license_score
      );
    }
    const unknownLimits = records.filter(r => !r.rpd_limit).length;
    console.log(`   ${unknownLimits} of ${records.length} models have no published daily limit (room score ${UNKNOWN_LIMIT_ROOM_SCORE})\n`);

    console.log(`✅ Built ${records.length} records (skipped ${skippedCount})\n`);

    // Step 5.5: Display match statistics (monitoring)
    console.log('📊 Match Statistics:');
    console.log('─'.repeat(120));
    console.log(`Direct matches:      ${matchStats.directMatch} (provider_slug exact match)`);
    console.log(`Normalized matches:  ${matchStats.normalizedMatch} (required normalization)`);
    console.log(`Failed matches:      ${matchStats.noMatch} (not found in 11_free-models-live)`);
    console.log(`Total processed:     ${mappings.length}`);
    console.log(`Success rate:        ${((matchStats.directMatch + matchStats.normalizedMatch) / mappings.length * 100).toFixed(1)}%\n`);

    // Display skipped models for debugging
    if (skippedModels.length > 0) {
      console.log('⚠️  Skipped Models (require investigation):');
      console.log('─'.repeat(120));
      skippedModels.forEach(m => {
        console.log(`   ${m.provider}:${m.slug} (aa_slug: ${m.aa_slug})`);
        // Suggest possible original slug
        const denormalized = m.slug.replace(/-(\d)/g, '.$1'); // Try converting hyphens back to periods for version numbers
        console.log(`      → Try checking 11_free-models-live for: ${denormalized}`);
      });
      console.log();
    }

    // Step 5.6: Deduplicate records by model_name (keep highest selection score)
    console.log('🔍 Deduplicating records by model_name...');
    const deduplicatedMap = {};
    for (const record of records) {
      const existing = deduplicatedMap[record.model_name];
      if (!existing || record.selection_score > existing.selection_score) {
        deduplicatedMap[record.model_name] = record;
      }
    }
    const uniqueRecords = Object.values(deduplicatedMap);
    const duplicatesRemoved = records.length - uniqueRecords.length;
    console.log(`✅ Removed ${duplicatesRemoved} duplicates, ${uniqueRecords.length} unique records remain\n`);

    // Step 6: Upsert into justask."23_router-model-ranking"
    console.log(`💾 Upserting ${uniqueRecords.length} records into justask."23_router-model-ranking"...`);
    const { data: inserted, error: upsertError } = await supabase
      .schema('justask')
      .from('23_router-model-ranking')
      .upsert(uniqueRecords, {
        onConflict: 'model_name',
        ignoreDuplicates: false
      })
      .select();

    if (upsertError) {
      throw new Error(`Failed to upsert data: ${upsertError.message}`);
    }

    console.log(`✅ Successfully populated ${inserted?.length || uniqueRecords.length} records\n`);

    // Remove stale rows (models no longer mapped)
    if (PRUNE && uniqueRecords.length > 0) {
      const keep = new Set(uniqueRecords.map(r => r.model_name));
      const { data: existing, error: existingError } = await supabase
        .schema('justask')
        .from('23_router-model-ranking')
        .select('model_name');
      if (existingError) {
        throw new Error(`Failed to list existing rows: ${existingError.message}`);
      }
      const stale = (existing || []).map(r => r.model_name).filter(n => !keep.has(n));
      for (let i = 0; i < stale.length; i += 100) {
        const { error: delError } = await supabase
          .schema('justask')
          .from('23_router-model-ranking')
          .delete()
          .in('model_name', stale.slice(i, i + 100));
        if (delError) {
          throw new Error(`Failed to delete stale rows: ${delError.message}`);
        }
      }
      console.log(`🧹 Removed ${stale.length} stale rows\n`);
    }

    // Step 7: Display top 5 models by selection score
    console.log('🏆 Top 5 models by selection score:');
    console.log('─'.repeat(120));

    const topModels = uniqueRecords
      .sort((a, b) => b.selection_score - a.selection_score)
      .slice(0, 5);

    topModels.forEach((model, index) => {
      console.log(`${index + 1}. ${model.model_name} (${model.inference_provider})`);
      console.log(`   Intelligence: ${model.intelligence_index?.toFixed(1) || 'N/A'} | Selection Score: ${model.selection_score.toFixed(3)}`);
      console.log(`   Free-limit room: ${model.overall_headroom.toFixed(2)} (rpd ${model.rpd_limit ?? 'unknown'}) | Geography: ${model.geography_score.toFixed(2)} | License: ${model.license_score.toFixed(2)}`);
      console.log(`   RPM: ${model.rpm_limit || 'N/A'} | TPM: ${model.tpm_limit || 'N/A'}`);
      console.log();
    });

    // Step 8: Display statistics by provider
    console.log('📊 Statistics by inference provider:');
    console.log('─'.repeat(120));

    const providerStats = {};
    uniqueRecords.forEach(model => {
      const provider = model.inference_provider;
      if (!providerStats[provider]) {
        providerStats[provider] = {
          count: 0,
          avgSelectionScore: [],
          avgIntelligence: [],
          withRateLimits: 0
        };
      }
      providerStats[provider].count++;
      providerStats[provider].avgSelectionScore.push(model.selection_score);
      if (model.intelligence_index) {
        providerStats[provider].avgIntelligence.push(model.intelligence_index);
      }
      if (model.rpm_limit || model.tpm_limit) {
        providerStats[provider].withRateLimits++;
      }
    });

    Object.entries(providerStats).forEach(([provider, stats]) => {
      const avgScore = stats.avgSelectionScore.reduce((a, b) => a + b, 0) / stats.avgSelectionScore.length;
      const avgIntel = stats.avgIntelligence.length > 0
        ? stats.avgIntelligence.reduce((a, b) => a + b, 0) / stats.avgIntelligence.length
        : null;

      console.log(`${provider}:`);
      console.log(`  Total models: ${stats.count}`);
      console.log(`  Avg selection score: ${avgScore.toFixed(3)}`);
      console.log(`  Avg intelligence index: ${avgIntel ? avgIntel.toFixed(1) : 'N/A'}`);
      console.log(`  Models with rate limits: ${stats.withRateLimits} (${Math.round(stats.withRateLimits / stats.count * 100)}%)`);
      console.log();
    });

    console.log('✅ Model selection score population complete!');

  } catch (error) {
    console.error('❌ Error populating model selection scores:');
    console.error(error.message);
    process.exit(1);
  }
}

// Run the population (not when imported by tests)
if (isMain) {
  populateModelSelectionScore();
}
