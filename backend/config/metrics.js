/**
 * 📊 Prometheus Metrics 配置
 *
 * 這個檔案設定了所有的 Prometheus metrics，包括：
 * - Counter: 計數器（只會增加）
 * - Gauge: 量表（可以增加或減少）
 * - Histogram: 直方圖（記錄分佈情況）
 */

const client = require('prom-client');

// 建立一個 Registry 來管理所有 metrics
const register = new client.Registry();

// 添加預設的 metrics（CPU、記憶體等）
client.collectDefaultMetrics({ register });

/**
 * 📈 HTTP 請求總數 (Counter)
 *
 * 記錄所有 HTTP 請求的總數
 * Labels: method (GET/POST/etc), route (/api/users), status_code (200/404/500)
 */
const httpRequestsTotal = new client.Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status_code'],
    registers: [register]
});

/**
 * ⏱️ HTTP 請求延遲 (Histogram)
 *
 * 記錄 HTTP 請求的回應時間分佈
 * Buckets: 設定不同的時間區間（毫秒）
 * Labels: method, route, status_code
 */
const httpRequestDuration = new client.Histogram({
    name: 'http_request_duration_ms',
    help: 'Duration of HTTP requests in milliseconds',
    labelNames: ['method', 'route', 'status_code'],
    buckets: [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000], // 毫秒
    registers: [register]
});

/**
 * 🔄 活躍請求數 (Gauge)
 *
 * 記錄當前正在處理的請求數量
 * 這個數字會增加（開始請求）和減少（完成請求）
 */
const activeRequests = new client.Gauge({
    name: 'http_requests_active',
    help: 'Number of active HTTP requests',
    registers: [register]
});

/**
 * ❌ HTTP 錯誤總數 (Counter)
 *
 * 記錄 HTTP 錯誤的總數（4xx 和 5xx）
 * Labels: method, route, status_code
 */
const httpErrorsTotal = new client.Counter({
    name: 'http_errors_total',
    help: 'Total number of HTTP errors (4xx and 5xx)',
    labelNames: ['method', 'route', 'status_code'],
    registers: [register]
});

/**
 * 📊 資料庫查詢總數 (Counter)
 *
 * 記錄資料庫查詢的總數
 * Labels: operation (SELECT/INSERT/UPDATE/DELETE)
 */
const dbQueriesTotal = new client.Counter({
    name: 'db_queries_total',
    help: 'Total number of database queries',
    labelNames: ['operation'],
    registers: [register]
});

/**
 * ⏱️ 資料庫查詢延遲 (Histogram)
 *
 * 記錄資料庫查詢的執行時間分佈
 * Labels: operation
 */
const dbQueryDuration = new client.Histogram({
    name: 'db_query_duration_ms',
    help: 'Duration of database queries in milliseconds',
    labelNames: ['operation'],
    buckets: [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
    registers: [register]
});

/**
 * 🎫 訂單總數 (Counter)
 *
 * 記錄建立的訂單總數
 * Labels: event_id, payment_method
 */
const ordersTotal = new client.Counter({
    name: 'orders_total',
    help: 'Total number of orders created',
    labelNames: ['event_id', 'payment_method'],
    registers: [register]
});

module.exports = {
    register,
    metrics: {
        httpRequestsTotal,
        httpRequestDuration,
        activeRequests,
        httpErrorsTotal,
        dbQueriesTotal,
        dbQueryDuration,
        ordersTotal
    }
};
