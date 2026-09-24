// GLM FPS Game - desktop auto-updater (pure Node, no Electron APIs)
// Checks the game's version.json manifest (same one the Android APK uses),
// downloads only changed files, verifies SHA-256 + size of each, and swaps
// them in atomically. version.json is written LAST so a crash mid-update
// always leaves the previous fully-playable version on disk.
'use strict';

const https = require('https');
const http = require('http');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const DEFAULT_BASE = 'https://aydinbarzegary1393-pixel.github.io/glm-game';

function base() {
  return (process.env.GLM_UPDATE_BASE || DEFAULT_BASE).replace(/\/+$/, '');
}

function joinUrl(baseStr, rel) {
  return baseStr + '/' + rel.split(path.sep === '\\' ? '\\' : '/').map(encodeURIComponent).join('/');
}

function fetchBuffer(url, timeoutMs) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const done = (err, data) => {
      if (settled) return;
      settled = true;
      if (err) reject(err); else resolve(data);
    };
    let req;
    try {
      req = (url.startsWith('http:') ? http : https).get(url, (res) => {
        if (res.statusCode !== 200) {
          res.resume();
          return done(new Error('HTTP ' + res.statusCode + ' for ' + url));
        }
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => done(null, Buffer.concat(chunks)));
        res.on('error', done);
      });
    } catch (e) { return done(e); }
    req.setTimeout(timeoutMs, () => req.destroy(new Error('timeout after ' + timeoutMs + 'ms: ' + url)));
    req.on('error', done);
  });
}

function parseVer(v) {
  if (typeof v !== 'string') return null;
  const m = v.trim().replace(/^v/i, '').match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!m) return null;
  return [Number(m[1]), Number(m[2]), Number(m[3])];
}

function isNewer(remote, local) {
  const r = parseVer(remote);
  if (!r) return false;
  const l = local == null ? null : parseVer(local);
  if (!l) return true;
  for (let i = 0; i < 3; i++) {
    if (r[i] !== l[i]) return r[i] > l[i];
  }
  return false;
}

function sha256Buf(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

function sha256File(file) {
  try {
    const h = crypto.createHash('sha256');
    const fd = fs.openSync(file, 'r');
    try {
      const buf = Buffer.alloc(1024 * 1024);
      let n;
      while ((n = fs.readSync(fd, buf, 0, buf.length, null)) > 0) h.update(buf.subarray(0, n));
    } finally {
      fs.closeSync(fd);
    }
    return h.digest('hex');
  } catch (e) {
    return null; // missing / unreadable -> will re-download
  }
}

// returns a safe relative path or null (blocks traversal / absolute paths)
function normalizeSafe(p) {
  if (typeof p !== 'string' || p.length === 0) return null;
  const norm = path.normalize(p);
  if (path.isAbsolute(norm) || norm.startsWith('..') || norm.split(path.sep).includes('..')) return null;
  return norm;
}

function readLocalVersion(gameDir) {
  try {
    const j = JSON.parse(fs.readFileSync(path.join(gameDir, 'version.json'), 'utf8'));
    return j && typeof j.version === 'string' ? j.version : null;
  } catch (e) {
    return null;
  }
}

function atomicWrite(destFile, buf) {
  const tmp = destFile + '.tmp' + process.pid;
  const fd = fs.openSync(tmp, 'w');
  try {
    fs.writeSync(fd, buf);
    fs.fsyncSync(fd);
  } finally {
    fs.closeSync(fd);
  }
  fs.renameSync(tmp, destFile);
}

function rmrf(p) {
  try { fs.rmSync(p, { recursive: true, force: true }); } catch (e) { /* best effort */ }
}

/**
 * Check for a newer release and sync the game directory to it.
 * opts:
 *   gameDir      - writable dir that holds fps-game.html + assets + version.json
 *   onProgress   - cb({phase:'check'|'download'|'done', downloaded, total, bytes, path})
 *   timeoutMs    - manifest fetch timeout (default 7000)
 *   fileTimeoutMs- per-file download timeout (default 30000)
 * Returns a result object, never throws:
 *   { status:'updated'|'current'|'offline'|'error', version, downloaded, skipped, bytes, error }
 */
async function checkAndUpdate(opts) {
  const o = opts || {};
  const gameDir = o.gameDir;
  const onProgress = o.onProgress || function () {};
  const timeoutMs = o.timeoutMs || 7000;
  const fileTimeoutMs = o.fileTimeoutMs || 30000;
  const baseUrl = (o.base || base()).replace(/\/+$/, '');
  const staging = path.join(gameDir, '.update-tmp');

  fs.mkdirSync(gameDir, { recursive: true });
  const localVersion = readLocalVersion(gameDir);

  // --- 1. fetch manifest -------------------------------------------------
  let manifest;
  try {
    const raw = await fetchBuffer(joinUrl(baseUrl, 'version.json'), timeoutMs);
    manifest = JSON.parse(raw.toString('utf8'));
    if (!manifest || typeof manifest.version !== 'string' || !Array.isArray(manifest.files)) {
      return { status: 'error', version: localVersion, error: 'invalid manifest shape' };
    }
  } catch (e) {
    onProgress({ phase: 'offline' });
    return { status: 'offline', version: localVersion, error: String((e && e.message) || e) };
  }
  onProgress({ phase: 'check', remoteVersion: manifest.version, localVersion: localVersion });

  // --- 2. already up to date? -------------------------------------------
  if (!isNewer(manifest.version, localVersion)) {
    onProgress({ phase: 'done', updated: false, version: localVersion || manifest.version });
    return { status: 'current', version: localVersion || manifest.version, downloaded: 0, skipped: 0 };
  }

  // --- 3. download changed files ----------------------------------------
  rmrf(staging);
  fs.mkdirSync(staging, { recursive: true });
  const files = manifest.files;
  let downloaded = 0, skipped = 0, bytes = 0;
  try {
    for (const f of files) {
      const rel = normalizeSafe(f && f.path);
      if (!rel) throw new Error('unsafe path in manifest: ' + JSON.stringify(f && f.path));
      const dest = path.join(gameDir, rel);
      const want = typeof f.sha256 === 'string' ? f.sha256.toLowerCase() : null;
      if (want && sha256File(dest) === want) {
        skipped++;
        onProgress({ phase: 'download', downloaded, skipped, total: files.length, bytes, path: rel, cached: true });
        continue;
      }
      const buf = await fetchBuffer(joinUrl(baseUrl, rel), fileTimeoutMs);
      if (want && sha256Buf(buf) !== want) throw new Error('sha256 mismatch: ' + rel);
      if (f.size != null && Number(f.size) !== buf.length) throw new Error('size mismatch: ' + rel);
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      atomicWrite(dest, buf);
      downloaded++;
      bytes += buf.length;
      onProgress({ phase: 'download', downloaded, skipped, total: files.length, bytes, path: rel });
    }

    // --- 4. sanity: entry must exist after update -----------------------
    if (manifest.entry) {
      const rel = normalizeSafe(manifest.entry);
      if (!rel || !fs.existsSync(path.join(gameDir, rel))) {
        throw new Error('entry missing after update: ' + manifest.entry);
      }
    }

    // --- 5. version.json written LAST (atomicity marker) ----------------
    atomicWrite(
      path.join(gameDir, 'version.json'),
      Buffer.from(JSON.stringify({
        version: manifest.version,
        generated: manifest.generated || null,
        entry: manifest.entry || 'fps-game.html',
      }, null, 2) + '\n')
    );
  } catch (e) {
    rmrf(staging);
    onProgress({ phase: 'error', error: String((e && e.message) || e) });
    return { status: 'error', version: localVersion, downloaded, skipped, error: String((e && e.message) || e) };
  }
  rmrf(staging);
  onProgress({ phase: 'done', updated: true, version: manifest.version });
  return { status: 'updated', version: manifest.version, downloaded, skipped, bytes };
}

module.exports = { checkAndUpdate, isNewer, parseVer, normalizeSafe, sha256Buf, sha256File, fetchBuffer, readLocalVersion };
