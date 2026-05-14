/**
 * IDS Agent Collector - 通用低耦合 HTTP 日誌收集器
 *
 * 使用方式：
 *   const agentCollector = require('./agent-collector');
 *   app.use(agentCollector.middleware());
 *   agentCollector.start();
 *
 * 環境變數：
 *   AGENT_ID            - Agent 識別碼 (預設: 自動生成)
 *   AGENT_GATEWAY_URL   - Gateway URL (預設: http://localhost:80)
 *   AGENT_TENANT_ID     - 租戶識別碼 (預設: tixmaster-001)
 *   AGENT_HEARTBEAT     - 心跳間隔 ms (預設: 30000)
 *   AGENT_BATCH_SIZE    - 批次發送數量 (預設: 50)
 *   AGENT_SEND_INTERVAL - 發送間隔 ms (預設: 5000)
 */

const https = require('https');
const http = require('http');
const os = require('os');
const { URL } = require('url');

// ============ 設定 ============
const CONFIG = {
  AGENT_ID: process.env.AGENT_ID || `agent-${os.hostname()}-${process.pid}`,
  GATEWAY_URL: process.env.AGENT_GATEWAY_URL || 'http://localhost:80',
  TENANT_ID: process.env.AGENT_TENANT_ID || 'tixmaster-001',
  HEARTBEAT_INTERVAL: parseInt(process.env.AGENT_HEARTBEAT) || 30000,
  BATCH_SIZE: parseInt(process.env.AGENT_BATCH_SIZE) || 50,
  SEND_INTERVAL: parseInt(process.env.AGENT_SEND_INTERVAL) || 5000,
  REJECT_UNAUTHORIZED: process.env.NODE_ENV === 'production'
};

const BATCH_URL = CONFIG.GATEWAY_URL.replace(/\/$/, '') + '/api/v1/ingest/batch';

// ============ 狀態 ============
const state = {
  logQueue: [],
  isRunning: false,
  heartbeatTimer: null,
  sendTimer: null,
  stats: {
    totalRequests: 0,
    totalSent: 0,
    totalFailed: 0,
    startTime: null
  }
};

// ============ 工具函數 ============

function sendRequest(url, data) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const isHttps = parsedUrl.protocol === 'https:';
    const lib = isHttps ? https : http;
    const body = JSON.stringify(data);

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (isHttps ? 443 : 80),
      path: parsedUrl.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'X-Agent-ID': CONFIG.AGENT_ID
      },
      rejectUnauthorized: CONFIG.REJECT_UNAUTHORIZED
    };

    const req = lib.request(options, (res) => {
      let responseBody = '';
      res.on('data', chunk => responseBody += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ statusCode: res.statusCode, body: responseBody });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${responseBody}`));
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.write(body);
    req.end();
  });
}

function getClientIP(req) {
  return req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
         req.headers['x-real-ip'] ||
         req.connection?.remoteAddress ||
         req.socket?.remoteAddress ||
         'unknown';
}

const _MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function toRawPayload(log) {
  const d = new Date(log.timestamp);
  const pad = n => String(n).padStart(2, '0');
  const dateStr = `${pad(d.getUTCDate())}/${_MONTHS[d.getUTCMonth()]}/${d.getUTCFullYear()}:` +
                  `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} +0000`;
  const referer = log.referer || '-';
  const ua = log.userAgent || '-';
  const size = log.contentLength || 0;
  return `${log.ip} - - [${dateStr}] "${log.method} ${log.url} HTTP/1.1" ${log.statusCode} ${size} "${referer}" "${ua}"`;
}

function logEntryToEvent(log) {
  return {
    tenant_id: CONFIG.TENANT_ID,
    timestamp: new Date(log.timestamp).toISOString(),
    source_ip: log.ip,
    event_type: 'web_access',
    user_agent: log.userAgent || null,
    payload: {
      method: log.method,
      url: log.url,
      status: log.statusCode,
      size: parseInt(log.contentLength) || 0,
      duration_ms: log.duration,
      referer: log.referer || null,
      query: log.query || {}
    },
    raw_payload: toRawPayload(log)
  };
}

function formatLogEntry(req, res, duration) {
  return {
    timestamp: Date.now(),
    method: req.method,
    url: req.originalUrl || req.url,
    path: req.path || req.url.split('?')[0],
    statusCode: res.statusCode,
    duration,
    ip: getClientIP(req),
    userAgent: req.headers['user-agent'] || 'unknown',
    contentLength: res.get?.('content-length') || res.getHeader?.('content-length') || 0,
    referer: req.headers['referer'] || req.headers['referrer'] || null,
    query: req.query || {}
  };
}

// ============ 核心功能 ============

function middleware(options = {}) {
  const { skip = () => false, onLog = null } = options;

  return (req, res, next) => {
    if (skip(req)) return next();

    const startTime = Date.now();

    res.on('finish', () => {
      const duration = Date.now() - startTime;
      const logEntry = formatLogEntry(req, res, duration);

      if (onLog) onLog(logEntry);

      state.logQueue.push(logEntry);
      state.stats.totalRequests++;

      if (state.logQueue.length >= CONFIG.BATCH_SIZE * 2) {
        sendLogs();
      }
    });

    next();
  };
}

async function sendHeartbeat() {
  const payload = {
    events: [{
      tenant_id: CONFIG.TENANT_ID,
      timestamp: new Date().toISOString(),
      event_type: 'heartbeat',
      payload: {
        agent_id: CONFIG.AGENT_ID,
        hostname: os.hostname(),
        platform: os.platform(),
        uptime: process.uptime(),
        queue_length: state.logQueue.length,
        stats: { ...state.stats }
      }
    }]
  };

  try {
    await sendRequest(BATCH_URL, payload);
    console.log(`[Agent] 💓 心跳已發送 (${CONFIG.AGENT_ID})`);
  } catch (error) {
    console.error(`[Agent] ❌ 心跳失敗: ${error.message}`);
  }
}

async function sendLogs() {
  if (state.logQueue.length === 0) return;

  const logsToSend = state.logQueue.splice(0, CONFIG.BATCH_SIZE);

  try {
    const payload = { events: logsToSend.map(logEntryToEvent) };
    await sendRequest(BATCH_URL, payload);
    state.stats.totalSent += logsToSend.length;
    console.log(`[Agent] 📤 已發送 ${logsToSend.length} 條日誌`);
  } catch (error) {
    console.error(`[Agent] ❌ 日誌發送失敗: ${error.message}`);
    state.logQueue.unshift(...logsToSend);
    state.stats.totalFailed += logsToSend.length;
  }
}

function start() {
  if (state.isRunning) {
    console.warn('[Agent] 已經在運行中');
    return;
  }

  state.isRunning = true;
  state.stats.startTime = Date.now();

  console.log(`\n[Agent] 🚀 IDS Agent Collector 啟動`);
  console.log(`[Agent]    ID: ${CONFIG.AGENT_ID}`);
  console.log(`[Agent]    Gateway: ${BATCH_URL}`);
  console.log(`[Agent]    Tenant: ${CONFIG.TENANT_ID}`);
  console.log(`[Agent]    心跳間隔: ${CONFIG.HEARTBEAT_INTERVAL}ms`);
  console.log(`[Agent]    批次大小: ${CONFIG.BATCH_SIZE}`);
  console.log(`[Agent]    發送間隔: ${CONFIG.SEND_INTERVAL}ms\n`);

  sendHeartbeat();
  state.heartbeatTimer = setInterval(sendHeartbeat, CONFIG.HEARTBEAT_INTERVAL);
  state.sendTimer = setInterval(sendLogs, CONFIG.SEND_INTERVAL);
}

async function stop() {
  if (!state.isRunning) return;

  console.log('\n[Agent] 🛑 正在停止...');

  if (state.heartbeatTimer) clearInterval(state.heartbeatTimer);
  if (state.sendTimer) clearInterval(state.sendTimer);

  while (state.logQueue.length > 0) {
    await sendLogs();
  }

  try {
    await sendRequest(BATCH_URL, {
      events: [{
        tenant_id: CONFIG.TENANT_ID,
        timestamp: new Date().toISOString(),
        event_type: 'heartbeat',
        payload: { agent_id: CONFIG.AGENT_ID, status: 'offline' }
      }]
    });
    console.log('[Agent] 👋 已標記為離線');
  } catch (e) { /* ignore */ }

  state.isRunning = false;
  console.log('[Agent] ✓ 已停止\n');
}

function getStatus() {
  return {
    agentId: CONFIG.AGENT_ID,
    gatewayUrl: BATCH_URL,
    tenantId: CONFIG.TENANT_ID,
    isRunning: state.isRunning,
    queueLength: state.logQueue.length,
    stats: { ...state.stats }
  };
}

process.on('SIGINT', async () => { await stop(); process.exit(0); });
process.on('SIGTERM', async () => { await stop(); process.exit(0); });

module.exports = {
  middleware,
  start,
  stop,
  getStatus,
  CONFIG,
  addLog: (logEntry) => {
    state.logQueue.push({ ...logEntry, timestamp: Date.now() });
    state.stats.totalRequests++;
  }
};
