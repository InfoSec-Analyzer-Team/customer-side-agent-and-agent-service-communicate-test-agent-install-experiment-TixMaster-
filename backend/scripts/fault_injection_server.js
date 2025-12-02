require('dotenv').config();
const express = require('express');
const logger = require('../config/logger');
const { Client } = require('pg');

const app = express();
const PORT = process.env.FAULT_PORT ? Number(process.env.FAULT_PORT) : 3999;
const ENABLED = (process.env.ENABLE_FAULT_ENDPOINTS || 'false').toLowerCase() === 'true';
const os = require('os');

// 全域狀態（供特定故障持續化使用）
const leakStore = [];
const leakController = { timer: null, stepMb: 0, intervalMs: 0 };
const rateState = new Map(); // key -> { count, resetAt }

// 簡單守門：未啟用時回 403
app.use((req, res, next) => {
  if (!ENABLED) {
    return res.status(403).json({
      error: 'Fault injection disabled',
      hint: 'Set ENABLE_FAULT_ENDPOINTS=true to enable',
    });
  }
  next();
});

// 基礎健康檢查
app.get('/health', (req, res) => {
  res.json({ status: 'OK', name: 'fault-injection-server', port: PORT });
});

// 1) 高延遲: 依 delayMs 延遲後回應 200
// GET /api/fault/latency?delayMs=3000
app.get('/api/fault/latency', async (req, res) => {
  const maxMs = 60_000; // 上限 60s，避免誤用
  const delayMs = Math.min(Math.max(parseInt(req.query.delayMs || '2000', 10) || 2000, 0), maxMs);
  logger.info('[fault] latency', { delayMs });
  setTimeout(() => {
    res.status(200).json({ ok: true, type: 'latency', delayMs });
  }, delayMs);
});

// 2) 逾時: 保持連線不回應，或超長延遲
// GET /api/fault/timeout?timeoutMs=15000&never=true
app.get('/api/fault/timeout', async (req, res) => {
  const maxMs = 10 * 60_000; // 上限 10 分鐘
  const timeoutMs = Math.min(Math.max(parseInt(req.query.timeoutMs || '15000', 10) || 15000, 0), maxMs);
  const never = String(req.query.never || 'false').toLowerCase() === 'true';
  logger.warn('[fault] timeout', { timeoutMs, never });

  if (never) {
    // 故意不回應（由客戶端逾時機制處理）
    return; // 不呼叫 res.*
  }

  setTimeout(() => {
    // 逾時視角：大多數客戶端會在這之前就已經超時
    try {
      if (!res.headersSent) {
        res.status(200).json({ ok: true, type: 'timeout_hold', heldMs: timeoutMs });
      }
    } catch (e) {
      logger.error('[fault] timeout respond error', { error: e.message });
    }
  }, timeoutMs + 1000);
});

// 3) 依賴故障: 模擬/真實
// GET /api/fault/dependency?type=db&mode=simulate
// type=db|http|dns (僅 db 提供簡單 real 模式)
// mode=simulate|real
app.get('/api/fault/dependency', async (req, res) => {
  const type = String(req.query.type || 'db');
  const mode = String(req.query.mode || 'simulate');
  logger.error('[fault] dependency failure requested', { type, mode });

  if (mode === 'simulate') {
    // 直接回 503 模擬依賴故障
    return res.status(503).json({ ok: false, type, mode, error: `${type} dependency unavailable (simulated)` });
  }

  // real 模式（目前支援 db）：用錯誤查詢觸發 DB 錯誤
  if (type === 'db') {
    const databaseUrl = process.env.DATABASE_URL;
    if (!databaseUrl) {
      return res.status(503).json({ ok: false, type, mode, error: 'DATABASE_URL not set' });
    }

    const client = new Client({ connectionString: databaseUrl, ssl: process.env.PGSSL === 'true' ? { rejectUnauthorized: false } : undefined });
    try {
      await client.connect();
      // 故意錯誤的 SQL
      await client.query('SELECT * FROM definitely_missing_table_to_fail');
      await client.end();
      return res.status(200).json({ ok: true, type, mode, note: 'Unexpectedly succeeded' });
    } catch (err) {
      try { await client.end(); } catch (_) {}
      logger.error('[fault] db dependency error (real)', { error: err.message });
      return res.status(503).json({ ok: false, type, mode, error: err.message });
    }
  }

  // 其他型別暫以模擬為主
  return res.status(503).json({ ok: false, type, mode, error: `${type} dependency failure (not implemented, simulated)` });
});

app.listen(PORT, () => {
  logger.info(`🧪 Fault Injection Server running on http://localhost:${PORT}`);
  if (!ENABLED) {
    logger.warn('Fault injection is DISABLED. Set ENABLE_FAULT_ENDPOINTS=true to enable responses.');
  }
  logger.info('Endpoints:');
  logger.info(`- GET /health`);
  logger.info(`- GET /api/fault/latency?delayMs=3000`);
  logger.info(`- GET /api/fault/timeout?timeoutMs=15000&never=true`);
  logger.info(`- GET /api/fault/dependency?type=db&mode=simulate|real`);
  logger.info(`- GET /api/fault/random?errorRate=0.3`);
  logger.info(`- GET /api/fault/cpu-spike?durationMs=5000`);
  logger.info(`- GET /api/fault/memory-pressure?mb=200&durationMs=10000`);
  logger.info(`- GET /api/fault/http-dependency?status=500&delayMs=1000`);
  logger.info(`- GET /api/fault/dns-failure?hostname=invalid.local`);
  logger.info(`- GET /api/fault/crash?code=1&confirm=YES`);
  logger.info(`- GET /api/fault/delay-jitter?meanMs=1000&jitterMs=500`);
  logger.info(`- GET /api/fault/partial-response?bytes=256&delayMs=0`);
  logger.info(`- GET /api/fault/dropped-connection?delayMs=0`);
  logger.info(`- GET /api/fault/rate-limit?limit=10&periodSec=60&status=429`);
  logger.info(`- GET /api/fault/memory-leak?mode=start&stepMb=5&intervalMs=1000`);
  logger.info(`- GET /api/fault/memory-leak?mode=stop`);
  logger.info(`- GET /api/fault/memory-leak?mode=status`);
  logger.info(`- GET /api/fault/disk-io?sizeMb=50`);
  logger.info(`- GET /api/fault/log-spam?lines=1000&intervalMs=5&level=info`);
});

// 4) 隨機錯誤: 依 errorRate 機率回 500
// GET /api/fault/random?errorRate=0.3
app.get('/api/fault/random', (req, res) => {
  const errorRate = Math.min(Math.max(parseFloat(String(req.query.errorRate || '0.3')), 0), 1);
  const r = Math.random();
  const willFail = r < errorRate;
  logger.warn('[fault] random', { errorRate, r, willFail });
  if (willFail) {
    return res.status(500).json({ ok: false, type: 'random', errorRate });
  }
  return res.status(200).json({ ok: true, type: 'random', errorRate });
});

// 5) CPU 尖峰: 進行忙迴圈一段時間
// GET /api/fault/cpu-spike?durationMs=5000
app.get('/api/fault/cpu-spike', (req, res) => {
  const maxMs = 60_000;
  const durationMs = Math.min(Math.max(parseInt(String(req.query.durationMs || '5000'), 10) || 5000, 0), maxMs);
  logger.warn('[fault] cpu-spike start', { durationMs });
  const start = Date.now();
  while (Date.now() - start < durationMs) {
    // busy work
    Math.sqrt(Math.random() * 1000);
  }
  logger.warn('[fault] cpu-spike end');
  res.status(200).json({ ok: true, type: 'cpu-spike', durationMs });
});

// 6) 記憶體壓力: 分配指定記憶體後保留一段時間
// GET /api/fault/memory-pressure?mb=200&durationMs=10000
app.get('/api/fault/memory-pressure', async (req, res) => {
  const maxMb = 1024; // 1GB 上限
  const mb = Math.min(Math.max(parseInt(String(req.query.mb || '200'), 10) || 200, 1), maxMb);
  const maxMs = 60_000;
  const durationMs = Math.min(Math.max(parseInt(String(req.query.durationMs || '10000'), 10) || 10000, 0), maxMs);
  logger.warn('[fault] memory-pressure start', { mb, durationMs });
  try {
    const arr = Buffer.alloc(mb * 1024 * 1024, 1); // allocate
    setTimeout(() => {
      // 釋放（讓 GC 接管）
      // eslint-disable-next-line no-unused-vars
      // arr = null; // 不能重新賦值 const；依作用域離開釋放
      logger.warn('[fault] memory-pressure end');
    }, durationMs);
    res.status(200).json({ ok: true, type: 'memory-pressure', mb, durationMs });
  } catch (e) {
    logger.error('[fault] memory-pressure error', { error: e.message });
    res.status(500).json({ ok: false, type: 'memory-pressure', error: e.message });
  }
});

// 7) 外部 HTTP 依賴失敗: 回傳指定狀態碼並可延遲
// GET /api/fault/http-dependency?status=500&delayMs=1000
app.get('/api/fault/http-dependency', (req, res) => {
  const status = Math.min(Math.max(parseInt(String(req.query.status || '500'), 10) || 500, 100), 599);
  const delayMs = Math.min(Math.max(parseInt(String(req.query.delayMs || '0'), 10) || 0, 0), 60_000);
  logger.error('[fault] http-dependency', { status, delayMs });
  setTimeout(() => {
    res.status(status).json({ ok: false, type: 'http-dependency', status });
  }, delayMs);
});

// 8) DNS 故障模擬: 嘗試解析錯誤主機名並回傳 503
// GET /api/fault/dns-failure?hostname=invalid.local
const dns = require('dns');
app.get('/api/fault/dns-failure', (req, res) => {
  const hostname = String(req.query.hostname || 'invalid.local');
  logger.error('[fault] dns-failure', { hostname });
  dns.lookup(hostname, (err) => {
    if (err) {
      return res.status(503).json({ ok: false, type: 'dns-failure', hostname, error: err.code || err.message });
    }
    // 若意外成功，仍回 200 表示可解析
    return res.status(200).json({ ok: true, type: 'dns-failure', hostname, note: 'resolved unexpectedly' });
  });
});

// 9) Crash: 強制中止 Process（高風險，需 confirm=YES）
// GET /api/fault/crash?code=1&confirm=YES
app.get('/api/fault/crash', (req, res) => {
  const code = Math.min(Math.max(parseInt(String(req.query.code || '1'), 10) || 1, 0), 255);
  const confirm = String(req.query.confirm || 'NO');
  if (confirm !== 'YES') {
    return res.status(400).json({ ok: false, type: 'crash', error: 'confirm=YES required' });
  }
  logger.error('[fault] crash requested - exiting process', { code });
  res.status(202).json({ ok: true, type: 'crash', exiting: true, code });
  setTimeout(() => process.exit(code), 300);
});

// 10) 延遲抖動: 於 mean ± jitter 範圍內隨機延遲
// GET /api/fault/delay-jitter?meanMs=1000&jitterMs=500
app.get('/api/fault/delay-jitter', (req, res) => {
  const maxMs = 120_000;
  const meanMs = Math.min(Math.max(parseInt(String(req.query.meanMs || '1000'), 10) || 1000, 0), maxMs);
  const jitterMs = Math.min(Math.max(parseInt(String(req.query.jitterMs || '500'), 10) || 500, 0), maxMs);
  const delta = Math.floor((Math.random() * 2 - 1) * jitterMs);
  const delay = Math.min(Math.max(meanMs + delta, 0), maxMs);
  logger.warn('[fault] delay-jitter', { meanMs, jitterMs, delay });
  setTimeout(() => {
    res.status(200).json({ ok: true, type: 'delay-jitter', delay });
  }, delay);
});

// 11) Partial response: 寫入部分資料後中斷連線
// GET /api/fault/partial-response?bytes=256&delayMs=0
app.get('/api/fault/partial-response', (req, res) => {
  const bytes = Math.min(Math.max(parseInt(String(req.query.bytes || '256'), 10) || 256, 1), 10 * 1024 * 1024);
  const delayMs = Math.min(Math.max(parseInt(String(req.query.delayMs || '0'), 10) || 0, 0), 60_000);
  logger.error('[fault] partial-response', { bytes, delayMs });
  res.set('Content-Type', 'application/octet-stream');
  setTimeout(() => {
    try {
      const chunk = Buffer.allocUnsafe(Math.min(bytes, 64 * 1024)).fill(0x41);
      let remaining = bytes;
      while (remaining > 0) {
        res.write(chunk.slice(0, Math.min(chunk.length, remaining)));
        remaining -= Math.min(chunk.length, remaining);
        if (remaining <= 0) break;
      }
    } catch (e) {
      // ignore
    }
    // 直接摧毀 socket，模擬中途斷線
    try { res.destroy(); } catch (_) {}
  }, delayMs);
});

// 12) Dropped connection: 不回應並在延遲後中斷 socket
// GET /api/fault/dropped-connection?delayMs=0
app.get('/api/fault/dropped-connection', (req, res) => {
  const delayMs = Math.min(Math.max(parseInt(String(req.query.delayMs || '0'), 10) || 0, 0), 60_000);
  logger.error('[fault] dropped-connection', { delayMs });
  setTimeout(() => {
    try { req.socket.destroy(); } catch (_) {}
  }, delayMs);
});

// 13) Rate limit: 在 period 內超過次數則回 429（或自訂狀態）
// GET /api/fault/rate-limit?limit=10&periodSec=60&status=429
app.get('/api/fault/rate-limit', (req, res) => {
  const limit = Math.min(Math.max(parseInt(String(req.query.limit || '10'), 10) || 10, 1), 100000);
  const periodSec = Math.min(Math.max(parseInt(String(req.query.periodSec || '60'), 10) || 60, 1), 3600);
  const status = Math.min(Math.max(parseInt(String(req.query.status || '429'), 10) || 429, 100), 599);
  const key = 'global';
  let state = rateState.get(key);
  const now = Date.now();
  if (!state || now >= state.resetAt) {
    state = { count: 0, resetAt: now + periodSec * 1000 };
    rateState.set(key, state);
  }
  state.count += 1;
  const remaining = Math.max(0, limit - state.count);
  res.set('X-RateLimit-Limit', String(limit));
  res.set('X-RateLimit-Remaining', String(Math.max(0, remaining)));
  res.set('X-RateLimit-Reset', String(Math.floor(state.resetAt / 1000)));
  if (state.count > limit) {
    logger.warn('[fault] rate-limit exceeded', { count: state.count, limit });
    return res.status(status).json({ ok: false, type: 'rate-limit', limit, periodSec });
  }
  return res.status(200).json({ ok: true, type: 'rate-limit', count: state.count, limit, periodSec });
});

// 14) Memory leak: 週期性佔用記憶體並保留於全域（start/stop/status）
// GET /api/fault/memory-leak?mode=start&stepMb=5&intervalMs=1000
// GET /api/fault/memory-leak?mode=stop
// GET /api/fault/memory-leak?mode=status
app.get('/api/fault/memory-leak', (req, res) => {
  const mode = String(req.query.mode || 'status');
  if (mode === 'start') {
    const maxMb = 2048;
    const stepMb = Math.min(Math.max(parseInt(String(req.query.stepMb || '5'), 10) || 5, 1), maxMb);
    const intervalMs = Math.min(Math.max(parseInt(String(req.query.intervalMs || '1000'), 10) || 1000, 100), 60_000);
    if (leakController.timer) {
      return res.status(200).json({ ok: true, type: 'memory-leak', status: 'already-running', stepMb: leakController.stepMb, intervalMs: leakController.intervalMs, chunks: leakStore.length });
    }
    leakController.stepMb = stepMb;
    leakController.intervalMs = intervalMs;
    leakController.timer = setInterval(() => {
      try {
        const buf = Buffer.alloc(stepMb * 1024 * 1024, 1);
        leakStore.push(buf);
        logger.warn('[fault] memory-leak tick', { stepMb, totalChunks: leakStore.length });
      } catch (e) {
        logger.error('[fault] memory-leak alloc error', { error: e.message });
      }
    }, intervalMs);
    return res.status(200).json({ ok: true, type: 'memory-leak', status: 'started', stepMb, intervalMs });
  }
  if (mode === 'stop') {
    if (leakController.timer) {
      clearInterval(leakController.timer);
      leakController.timer = null;
    }
    // 釋放參考，交由 GC 回收
    while (leakStore.length) leakStore.pop();
    return res.status(200).json({ ok: true, type: 'memory-leak', status: 'stopped', chunks: leakStore.length });
  }
  // status
  return res.status(200).json({ ok: true, type: 'memory-leak', status: leakController.timer ? 'running' : 'idle', stepMb: leakController.stepMb, intervalMs: leakController.intervalMs, chunks: leakStore.length });
});

// 15) Disk I/O: 寫入指定大小的暫存檔（以模擬磁碟壓力）
// GET /api/fault/disk-io?sizeMb=50
app.get('/api/fault/disk-io', async (req, res) => {
  const maxMb = 1024; // 1GB 上限，避免誤用
  const sizeMb = Math.min(Math.max(parseInt(String(req.query.sizeMb || '50'), 10) || 50, 1), maxMb);
  const tmpDir = os.tmpdir();
  const filePath = require('path').join(tmpDir, `fault-io-${Date.now()}-${sizeMb}mb.tmp`);
  logger.warn('[fault] disk-io start', { sizeMb, filePath });
  try {
    // 以 chunk 方式寫入，避免一次性分配超大 Buffer
    const fd = require('fs').openSync(filePath, 'w');
    const chunkSize = 1024 * 1024; // 1MB
    const chunk = Buffer.alloc(chunkSize, 0x5A);
    let remaining = sizeMb;
    while (remaining > 0) {
      require('fs').writeSync(fd, chunk);
      remaining -= 1;
    }
    require('fs').closeSync(fd);
    res.status(200).json({ ok: true, type: 'disk-io', sizeMb, filePath });
  } catch (e) {
    logger.error('[fault] disk-io error', { error: e.message });
    res.status(500).json({ ok: false, type: 'disk-io', error: e.message });
  }
});

// 16) Log spam: 快速產生大量日誌
// GET /api/fault/log-spam?lines=1000&intervalMs=5&level=info
app.get('/api/fault/log-spam', async (req, res) => {
  const lines = Math.min(Math.max(parseInt(String(req.query.lines || '1000'), 10) || 1000, 1), 1_000_000);
  const intervalMs = Math.min(Math.max(parseInt(String(req.query.intervalMs || '5'), 10) || 5, 0), 1000);
  const level = String(req.query.level || 'info');
  logger.warn('[fault] log-spam requested', { lines, intervalMs, level });
  let i = 0;
  const lv = ['error','warn','info','debug'].includes(level) ? level : 'info';
  const timer = setInterval(() => {
    i += 1;
    try { logger[lv](`[fault][spam] line=${i}/${lines}`); } catch (_) { logger.info(`[fault][spam] line=${i}/${lines}`); }
    if (i >= lines) {
      clearInterval(timer);
    }
  }, intervalMs);
  res.status(200).json({ ok: true, type: 'log-spam', lines, intervalMs, level: lv });
});
