const winston = require('winston');

/**
 * 🔍 TixMaster Logger Configuration
 *
 * 結構化日誌系統，符合任務要求：
 * - Level (Info/Error/Warning)
 * - Timestamp
 * - UserID（如有登入）
 * - Request ID（Correlation ID）
 */

// 定義日誌格式 - JSON 格式
const logFormat = winston.format.combine(
    winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss'
    }),
    winston.format.errors({ stack: true }),
    winston.format.json()
);

// 建立 logger 實例
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: logFormat,
    defaultMeta: {
        service: 'tixmaster-api',
        environment: process.env.NODE_ENV || 'development'
    },
    transports: [
        // 輸出到 console（開發環境）
        new winston.transports.Console({
            format: winston.format.combine(
                winston.format.colorize(),
                winston.format.printf(({ timestamp, level, message, ...metadata }) => {
                    let msg = `${timestamp} [${level}]: ${message}`;
                    if (Object.keys(metadata).length > 0) {
                        msg += ` ${JSON.stringify(metadata)}`;
                    }
                    return msg;
                })
            )
        }),

        // 輸出到檔案 - 所有日誌
        new winston.transports.File({
            filename: 'logs/combined.log',
            format: logFormat
        }),

        // 輸出到檔案 - 只有錯誤
        new winston.transports.File({
            filename: 'logs/error.log',
            level: 'error',
            format: logFormat
        })
    ]
});

/**
 * 建立帶有 request context 的 logger
 * @param {Object} req - Express request object
 * @returns {Object} Logger with request context
 */
logger.createRequestLogger = (req) => {
    const requestId = req.id || req.headers['x-request-id'] || generateRequestId();
    const userId = req.user ? req.user.userId : 'anonymous';

    return logger.child({
        requestId,
        userId,
        method: req.method,
        path: req.path,
        ip: req.ip || req.connection.remoteAddress
    });
};

/**
 * 生成 Request ID（Correlation ID）
 * @returns {string} Unique request ID
 */
function generateRequestId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Express middleware - 為每個請求添加 request ID 和日誌
 */
logger.middleware = (req, res, next) => {
    // 生成或使用現有的 request ID
    req.id = req.headers['x-request-id'] || generateRequestId();

    // 記錄請求開始
    const startTime = Date.now();

    const requestLogger = logger.createRequestLogger(req);

    requestLogger.info('Incoming request', {
        method: req.method,
        url: req.url,
        userAgent: req.get('user-agent'),
        query: req.query
    });

    // 記錄回應
    res.on('finish', () => {
        const duration = Date.now() - startTime;
        const logLevel = res.statusCode >= 500 ? 'error' :
                        res.statusCode >= 400 ? 'warn' : 'info';

        requestLogger.log(logLevel, 'Request completed', {
            statusCode: res.statusCode,
            duration: `${duration}ms`
        });
    });

    // 將 logger 附加到 request，讓後續可以使用
    req.logger = requestLogger;

    next();
};

// 開發環境下顯示更詳細的日誌
if (process.env.NODE_ENV !== 'production') {
    logger.debug('Logger initialized in development mode');
}

module.exports = logger;
