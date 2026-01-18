/**
 * IDS Agent Collector - 通用低耦合 HTTP 日誌收集器
 *
 * 使用方式：
 *   const agentCollector = require('./agent-collector');
 *   app.use(agentCollector.middleware());
 *   agentCollector.start();
 *
 * 環境變數：
 *   AGENT_ID          - Agent 識別碼 (預設: 自動生成)
 *   AGENT_SERVER_URL  - Agent Service URL (預設: https://localhost:5000)
 *   AGENT_HEARTBEAT   - 心跳間隔 ms (預設: 30000)
 *   AGENT_BATCH_SIZE  - 批次發送數量 (預設: 50)
 *   AGENT_SEND_INTERVAL - 發送間隔 ms (預設: 5000)
 */

const https = require('https');
const http = require('http');
const os = require('os');
const { URL } = require('url');

// ============ 設定 ============
const CONFIG = {
  AGENT_ID: process.env.AGENT_ID || `agent-${os.hostname()}-${process.pid}`,
  SERVER_URL: process.env.AGENT_SERVER_URL || 'https://localhost:5000',
  HEARTBEAT_INTERVAL: parseInt(process.env.AGENT_HEARTBEAT) || 30000,
  BATCH_SIZE: parseInt(process.env.AGENT_BATCH_SIZE) || 50,
  SEND_INTERVAL: parseInt(process.env.AGENT_SEND_INTERVAL) || 5000,
  REJECT_UNAUTHORIZED: process.env.NODE_ENV === 'production' // 正式環境驗證憑證
};

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

/**
 * 發送 HTTP 請求 (支援 http/https)
 */
function sendRequest(url, data) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const isHttps = parsedUrl.protocol === 'https:';
    const lib = isHttps ? https : http;

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (isHttps ? 443 : 80),
      path: parsedUrl.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Agent-ID': CONFIG.AGENT_ID
      },
      rejectUnauthorized: CONFIG.REJECT_UNAUTHORIZED
    };

    const req = lib.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ statusCode: res.statusCode, body });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.write(JSON.stringify(data));
    req.end();
  });
}

/**
 * 取得客戶端 IP
 */
function getClientIP(req) {
  return req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
         req.headers['x-real-ip'] ||
         req.connection?.remoteAddress ||
         req.socket?.remoteAddress ||
         'unknown';
}

/**
 * 格式化 log entry
 */
function formatLogEntry(req, res, duration) {
  return {
    timestamp: Date.now(),
    method: req.method,
    url: req.originalUrl || req.url,
    path: req.path || req.url.split('?')[0],
    statusCode: res.statusCode,
    duration: duration,
    ip: getClientIP(req),
    userAgent: req.headers['user-agent'] || 'unknown',
    contentLength: res.get?.('content-length') || res.getHeader?.('content-length') || 0,
    referer: req.headers['referer'] || req.headers['referrer'] || null,
    query: req.query || {},
    // 可選：請求 body (注意敏感資料)
    // body: req.body
  };
}

// ============ 核心功能 ============

/**
 * Express/Connect Middleware
 * 攔截所有 HTTP 請求並記錄
 */
function middleware(options = {}) {
  const {
    skip = () => false,  // 跳過某些路徑
    onLog = null         // 自訂 log 處理
  } = options;

  return (req, res, next) => {
    // 跳過不需要記錄的路徑
    if (skip(req)) {
      return next();
    }

    const startTime = Date.now();

    // 攔截 response 完成事件
    res.on('finish', () => {
      const duration = Date.now() - startTime;
      const logEntry = formatLogEntry(req, res, duration);

      // 自訂處理
      if (onLog) {
        onLog(logEntry);
      }

      // 加入佇列
      state.logQueue.push(logEntry);
      state.stats.totalRequests++;

      // 佇列過大時立即發送
      if (state.logQueue.length >= CONFIG.BATCH_SIZE * 2) {
        sendLogs();
      }
    });

    next();
  };
}

/**
 * 發送心跳
 */
async function sendHeartbeat() {
  try {
    const payload = {
      agent_id: CONFIG.AGENT_ID,
      timestamp: Date.now(),
      status: 'online',
      hostname: os.hostname(),
      platform: os.platform(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      stats: { ...state.stats }
    };

    await sendRequest(`${CONFIG.SERVER_URL}/api/heartbeat`, payload);
    console.log(`[Agent] 💓 心跳已發送 (${CONFIG.AGENT_ID})`);
  } catch (error) {
    console.error(`[Agent] ❌ 心跳失敗: ${error.message}`);
  }
}

/**
 * 批次發送日誌
 */
async function sendLogs() {
  if (state.logQueue.length === 0) return;

  const logsToSend = state.logQueue.splice(0, CONFIG.BATCH_SIZE);

  try {
    const payload = {
      agent_id: CONFIG.AGENT_ID,
      logs: logsToSend,
      batch_size: logsToSend.length,
      timestamp: Date.now()
    };

    await sendRequest(`${CONFIG.SERVER_URL}/api/logs`, payload);
    state.stats.totalSent += logsToSend.length;
    console.log(`[Agent] 📤 已發送 ${logsToSend.length} 條日誌`);
  } catch (error) {
    console.error(`[Agent] ❌ 日誌發送失敗: ${error.message}`);
    // 失敗的日誌放回佇列前端
    state.logQueue.unshift(...logsToSend);
    state.stats.totalFailed += logsToSend.length;
  }
}

/**
 * 啟動 Agent
 */
function start() {
  if (state.isRunning) {
    console.warn('[Agent] 已經在運行中');
    return;
  }

  state.isRunning = true;
  state.stats.startTime = Date.now();

  console.log(`\n[Agent] 🚀 IDS Agent Collector 啟動`);
  console.log(`[Agent]    ID: ${CONFIG.AGENT_ID}`);
  console.log(`[Agent]    Server: ${CONFIG.SERVER_URL}`);
  console.log(`[Agent]    心跳間隔: ${CONFIG.HEARTBEAT_INTERVAL}ms`);
  console.log(`[Agent]    批次大小: ${CONFIG.BATCH_SIZE}`);
  console.log(`[Agent]    發送間隔: ${CONFIG.SEND_INTERVAL}ms\n`);

  // 立即發送第一次心跳
  sendHeartbeat();

  // 定期心跳
  state.heartbeatTimer = setInterval(sendHeartbeat, CONFIG.HEARTBEAT_INTERVAL);

  // 定期發送日誌
  state.sendTimer = setInterval(sendLogs, CONFIG.SEND_INTERVAL);
}

/**
 * 停止 Agent
 */
async function stop() {
  if (!state.isRunning) return;

  console.log('\n[Agent] 🛑 正在停止...');

  // 清除定時器
  if (state.heartbeatTimer) clearInterval(state.heartbeatTimer);
  if (state.sendTimer) clearInterval(state.sendTimer);

  // 發送剩餘日誌
  while (state.logQueue.length > 0) {
    await sendLogs();
  }

  // 發送離線心跳
  try {
    await sendRequest(`${CONFIG.SERVER_URL}/api/heartbeat`, {
      agent_id: CONFIG.AGENT_ID,
      timestamp: Date.now(),
      status: 'offline'
    });
    console.log('[Agent] 👋 已標記為離線');
  } catch (e) {
    // ignore
  }

  state.isRunning = false;
  console.log('[Agent] ✓ 已停止\n');
}

/**
 * 取得目前狀態
 */
function getStatus() {
  return {
    agentId: CONFIG.AGENT_ID,
    serverUrl: CONFIG.SERVER_URL,
    isRunning: state.isRunning,
    queueLength: state.logQueue.length,
    stats: { ...state.stats }
  };
}

// ============ 優雅關閉 ============
process.on('SIGINT', async () => {
  await stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await stop();
  process.exit(0);
});

// ============ 匯出 ============
module.exports = {
  middleware,
  start,
  stop,
  getStatus,
  CONFIG,
  // 進階：手動加入 log
  addLog: (logEntry) => {
    state.logQueue.push({ ...logEntry, timestamp: Date.now() });
    state.stats.totalRequests++;
  }
};
