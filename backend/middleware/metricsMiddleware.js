/**
 * 📊 Metrics Middleware
 *
 * 這個中間件會自動追蹤所有 HTTP 請求的 metrics
 * - 請求開始時：增加活躍請求數
 * - 請求結束時：記錄請求數、延遲、錯誤率
 */

const { metrics } = require('../config/metrics');
const logger = require('../config/logger');

/**
 * Metrics 追蹤中間件
 *
 * 使用方式：
 * app.use(metricsMiddleware);
 */
function metricsMiddleware(req, res, next) {
    // 記錄請求開始時間
    const startTime = Date.now();

    // 增加活躍請求數
    metrics.activeRequests.inc();

    // 當回應完成時執行
    res.on('finish', () => {
        // 計算請求處理時間（毫秒）
        const duration = Date.now() - startTime;

        // 取得請求的路由路徑（移除查詢參數）
        // 例如：/api/users/123 -> /api/users/:id
        const route = getRoutePattern(req);

        // 準備 labels
        const labels = {
            method: req.method,
            route: route,
            status_code: res.statusCode
        };

        // 記錄請求總數
        metrics.httpRequestsTotal.inc(labels);

        // 記錄請求延遲
        metrics.httpRequestDuration.observe(labels, duration);

        // 減少活躍請求數
        metrics.activeRequests.dec();

        // 如果是錯誤回應（4xx 或 5xx），記錄錯誤
        if (res.statusCode >= 400) {
            metrics.httpErrorsTotal.inc(labels);
        }

        // 記錄到 logger（僅錯誤）
        if (res.statusCode >= 500) {
            logger.error('HTTP request failed', {
                ...labels,
                duration,
                url: req.url
            });
        } else if (res.statusCode >= 400) {
            logger.warn('HTTP request client error', {
                ...labels,
                duration,
                url: req.url
            });
        }
    });

    next();
}

/**
 * 取得路由模式
 *
 * 將動態路由參數轉換為模式，避免 metrics 爆炸
 * 例如：
 * - /api/users/123 -> /api/users/:id
 * - /api/events/456 -> /api/events/:id
 *
 * 這樣可以避免每個不同的 ID 都產生一個新的 metric
 */
function getRoutePattern(req) {
    // 如果 Express 有設定 route，使用它
    if (req.route && req.route.path) {
        // 組合 baseUrl 和 route path
        const baseUrl = req.baseUrl || '';
        return baseUrl + req.route.path;
    }

    // 否則，嘗試將數字 ID 替換為 :id
    let path = req.path || req.url;

    // 移除查詢參數
    path = path.split('?')[0];

    // 將數字替換為 :id
    // 例如：/api/users/123 -> /api/users/:id
    path = path.replace(/\/\d+/g, '/:id');

    // 將 UUID 替換為 :id
    // 例如：/api/orders/550e8400-e29b-41d4-a716-446655440000 -> /api/orders/:id
    path = path.replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, '/:id');

    return path || 'unknown';
}

module.exports = metricsMiddleware;
