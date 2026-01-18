const https = require('https');
const axios = require('axios');

// 設定忽略自簽憑證警告（僅限實驗）
const agent = new https.Agent({
  rejectUnauthorized: false
});

const CONFIG = {
  AGENT_ID: 'test-agent-001',
  SERVER_URL: 'https://localhost:5000',
  HEARTBEAT_INTERVAL: 30000, // 30 秒
  LOG_BATCH_SIZE: 10,
  LOG_SEND_INTERVAL: 5000 // 5 秒發一次日誌
};

const logQueue = [];

// 發送心跳
async function sendHeartbeat() {
  try {
    const response = await axios.post(
      `${CONFIG.SERVER_URL}/api/heartbeat`,
      {
        agent_id: CONFIG.AGENT_ID,
        timestamp: Date.now(),
        status: 'online'
      },
      { httpsAgent: agent }
    );
    
    console.log(`💓 心跳已發送: ${response.data.message}`);
  } catch (error) {
    console.error(`❌ 心跳失敗: ${error.message}`);
  }
}

// 發送日誌
async function sendLogs() {
  if (logQueue.length === 0) return;

  const logsToSend = logQueue.splice(0, CONFIG.LOG_BATCH_SIZE);

  try {
    const response = await axios.post(
      `${CONFIG.SERVER_URL}/api/logs`,
      {
        agent_id: CONFIG.AGENT_ID,
        logs: logsToSend
      },
      { httpsAgent: agent }
    );

    console.log(`📤 已發送 ${response.data.received} 條日誌`);
  } catch (error) {
    console.error(`❌ 日誌發送失敗: ${error.message}`);
    // 失敗的日誌重新放回佇列
    logQueue.unshift(...logsToSend);
  }
}

// 模擬產生日誌
function generateLog() {
  const levels = ['INFO', 'WARN', 'ERROR', 'DEBUG'];
  const messages = [
    'User login attempt',
    'Database query executed',
    'API request received',
    'File upload completed',
    'Suspicious activity detected'
  ];

  logQueue.push({
    level: levels[Math.floor(Math.random() * levels.length)],
    message: messages[Math.floor(Math.random() * messages.length)],
    timestamp: Date.now(),
    source: 'web-server'
  });
}

// 啟動 Agent
async function startAgent() {
  console.log(`\n🤖 Customer Agent 啟動中...`);
  console.log(`   Agent ID: ${CONFIG.AGENT_ID}`);
  console.log(`   Server: ${CONFIG.SERVER_URL}\n`);

  // 立即發送第一次心跳
  await sendHeartbeat();

  // 定期發送心跳
  setInterval(sendHeartbeat, CONFIG.HEARTBEAT_INTERVAL);

  // 定期發送日誌
  setInterval(sendLogs, CONFIG.LOG_SEND_INTERVAL);

  // 模擬日誌產生
  setInterval(generateLog, 1000); // 每秒產生一條日誌

  console.log('✓ Agent 已啟動，開始監控...\n');
}

// 優雅關閉
process.on('SIGINT', async () => {
  console.log('\n\n🛑 Agent 正在關閉...');
  
  // 發送最後一次心跳（標記為 offline）
  await axios.post(
    `${CONFIG.SERVER_URL}/api/heartbeat`,
    {
      agent_id: CONFIG.AGENT_ID,
      timestamp: Date.now(),
      status: 'offline'
    },
    { httpsAgent: agent }
  ).catch(() => {});

  process.exit(0);
});

startAgent();