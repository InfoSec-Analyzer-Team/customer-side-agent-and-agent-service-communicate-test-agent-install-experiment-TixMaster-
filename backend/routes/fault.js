const express = require('express');
const router = express.Router();
const logger = require('../config/logger');
const { Client } = require('pg');
const dns = require('dns');

const ENABLED = (process.env.ENABLE_FAULT_ENDPOINTS || 'false').toLowerCase() === 'true';

// 守門：未啟用則回 403
router.use((req, res, next) => {
  if (!ENABLED) {
    return res.status(403).json({ error: 'Fault injection disabled', hint: 'Set ENABLE_FAULT_ENDPOINTS=true to enable' });
  }
  next();
});

// 健康檢查（掛在 /api/fault/health）
router.get('/health', (req, res) => {
  res.json({ status: 'OK', name: 'fault-endpoints', integrated: true });
});

// 高延遲
router.get('/latency', (req, res) => {
  const maxMs = 60_000;
  const delayMs = Math.min(Math.max(parseInt(String(req.query.delayMs || '2000'), 10) || 2000, 0), maxMs);
  logger.info('[fault] latency', { delayMs });
  setTimeout(() => res.status(200).json({ ok: true, type: 'latency', delayMs }), delayMs);
});

// 逾時（保持連線不回應或長延遲）
router.get('/timeout', (req, res) => {
  const maxMs = 10 * 60_000;
  const timeoutMs = Math.min(Math.max(parseInt(String(req.query.timeoutMs || '15000'), 10) || 15000, 0), maxMs);
  const never = String(req.query.never || 'false').toLowerCase() === 'true';
  logger.warn('[fault] timeout', { timeoutMs, never });
  if (never) return; // 故意不回覆
  setTimeout(() => {
    try { if (!res.headersSent) res.status(200).json({ ok: true, type: 'timeout_hold', heldMs: timeoutMs }); }
    catch (e) { logger.error('[fault] timeout respond error', { error: e.message }); }
  }, timeoutMs + 1000);
});

// 依賴故障（simulate/real）
router.get('/dependency', async (req, res) => {
  const type = String(req.query.type || 'db');
  const mode = String(req.query.mode || 'simulate');
  logger.error('[fault] dependency failure requested', { type, mode });
  if (mode === 'simulate') {
    return res.status(503).json({ ok: false, type, mode, error: `${type} dependency unavailable (simulated)` });
  }
  if (type === 'db') {
    const databaseUrl = process.env.DATABASE_URL;
    if (!databaseUrl) return res.status(503).json({ ok: false, type, mode, error: 'DATABASE_URL not set' });
    const client = new Client({ connectionString: databaseUrl, ssl: process.env.PGSSL === 'true' ? { rejectUnauthorized: false } : undefined });
    try {
      await client.connect();
      await client.query('SELECT * FROM definitely_missing_table_to_fail');
      await client.end();
      return res.status(200).json({ ok: true, type, mode, note: 'Unexpectedly succeeded' });
    } catch (err) {
      try { await client.end(); } catch (_) {}
      logger.error('[fault] db dependency error (real)', { error: err.message });
      return res.status(503).json({ ok: false, type, mode, error: err.message });
    }
  }
  return res.status(503).json({ ok: false, type, mode, error: `${type} dependency failure (not implemented, simulated)` });
});

// 隨機錯誤
router.get('/random', (req, res) => {
  const errorRate = Math.min(Math.max(parseFloat(String(req.query.errorRate || '0.3')), 0), 1);
  const willFail = Math.random() < errorRate;
  logger.warn('[fault] random', { errorRate, willFail });
  if (willFail) return res.status(500).json({ ok: false, type: 'random', errorRate });
  return res.status(200).json({ ok: true, type: 'random', errorRate });
});

// CPU 尖峰
router.get('/cpu-spike', (req, res) => {
  const maxMs = 60_000;
  const durationMs = Math.min(Math.max(parseInt(String(req.query.durationMs || '5000'), 10) || 5000, 0), maxMs);
  logger.warn('[fault] cpu-spike start', { durationMs });
  const start = Date.now();
  while (Date.now() - start < durationMs) { Math.sqrt(Math.random() * 1000); }
  logger.warn('[fault] cpu-spike end');
  res.status(200).json({ ok: true, type: 'cpu-spike', durationMs });
});

// 記憶體壓力
router.get('/memory-pressure', (req, res) => {
  const maxMb = 1024;
  const mb = Math.min(Math.max(parseInt(String(req.query.mb || '200'), 10) || 200, 1), maxMb);
  const maxMs = 60_000;
  const durationMs = Math.min(Math.max(parseInt(String(req.query.durationMs || '10000'), 10) || 10000, 0), maxMs);
  logger.warn('[fault] memory-pressure start', { mb, durationMs });
  try {
    const arr = Buffer.alloc(mb * 1024 * 1024, 1);
    setTimeout(() => { logger.warn('[fault] memory-pressure end'); }, durationMs);
    res.status(200).json({ ok: true, type: 'memory-pressure', mb, durationMs });
  } catch (e) {
    logger.error('[fault] memory-pressure error', { error: e.message });
    res.status(500).json({ ok: false, type: 'memory-pressure', error: e.message });
  }
});

// 外部 HTTP 依賴失敗
router.get('/http-dependency', (req, res) => {
  const status = Math.min(Math.max(parseInt(String(req.query.status || '500'), 10) || 500, 100), 599);
  const delayMs = Math.min(Math.max(parseInt(String(req.query.delayMs || '0'), 10) || 0, 0), 60_000);
  logger.error('[fault] http-dependency', { status, delayMs });
  setTimeout(() => res.status(status).json({ ok: false, type: 'http-dependency', status }), delayMs);
});

// DNS 故障
router.get('/dns-failure', (req, res) => {
  const hostname = String(req.query.hostname || 'invalid.local');
  logger.error('[fault] dns-failure', { hostname });
  dns.lookup(hostname, (err) => {
    if (err) return res.status(503).json({ ok: false, type: 'dns-failure', hostname, error: err.code || err.message });
    return res.status(200).json({ ok: true, type: 'dns-failure', hostname, note: 'resolved unexpectedly' });
  });
});

module.exports = router;