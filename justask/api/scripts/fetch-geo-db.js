/**
 * Download the DB-IP Lite country database (CC BY 4.0, https://db-ip.com)
 * used by the region block. Runs on `npm install` (postinstall), so every
 * Render build fetches the current month's file.
 *
 * Exits non-zero if no database can be fetched and none exists, so a build
 * without the file fails instead of deploying a server that cannot start.
 * Set SKIP_GEO_FETCH=1 to skip (offline local installs).
 */
import fs from 'fs';
import path from 'path';
import zlib from 'zlib';
import { fileURLToPath } from 'url';
import maxmind from 'maxmind';

const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(here, '../geo');
const outFile = path.join(outDir, 'dbip-country-lite.mmdb');

const monthTag = (d) => `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;

const candidates = () => {
  const now = new Date();
  const prev = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1));
  return [monthTag(now), monthTag(prev)].map(
    (m) => `https://download.db-ip.com/free/dbip-country-lite-${m}.mmdb.gz`
  );
};

const verify = async (file) => {
  const reader = await maxmind.open(file);
  // Sanity check with a well-known address (Google Public DNS, US)
  const rec = reader.get('8.8.8.8');
  if (!rec?.country?.iso_code) throw new Error('verification lookup returned no country');
};

const main = async () => {
  if (process.env.SKIP_GEO_FETCH === '1') {
    console.log('[geo] SKIP_GEO_FETCH=1, skipping download');
    return;
  }
  fs.mkdirSync(outDir, { recursive: true });

  for (const url of candidates()) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const gz = Buffer.from(await res.arrayBuffer());
      const tmp = `${outFile}.tmp`;
      fs.writeFileSync(tmp, zlib.gunzipSync(gz));
      await verify(tmp);
      fs.renameSync(tmp, outFile);
      console.log(`[geo] Saved ${path.relative(process.cwd(), outFile)} from ${url}`);
      return;
    } catch (e) {
      console.warn(`[geo] ${url} failed: ${e.message}`);
    }
  }

  if (fs.existsSync(outFile)) {
    await verify(outFile);
    console.warn('[geo] Download failed; keeping the existing database');
    return;
  }
  console.error('[geo] FATAL: no geo database available');
  process.exit(1);
};

main().catch((e) => {
  console.error('[geo] FATAL:', e.message);
  process.exit(1);
});
