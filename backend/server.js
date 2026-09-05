require('dotenv').config();
const express = require('express');
const cors = require('cors');
const session = require('express-session');  // NEW - Session 管理
require('dotenv').config();
const passport = require('./config/passport');  // NEW - Passport 設定
const logger = require('./config/logger');  // NEW - Logger 配置

const errorHandler = require('./middleware/errorHandler');
const featureFlagsMiddleware = require('./middleware/featureFlags');
const metricsMiddleware = require('./middleware/metricsMiddleware');  // NEW - Metrics tracking
const { register } = require('./config/metrics');  // NEW - Prometheus registry
const path = require('path');
const fs = require('fs');

// Import routes
const usersRouter = require('./routes/users');
const eventsRouter = require('./routes/events');
const ticketsRouter = require('./routes/tickets');
const ordersRouter = require('./routes/orders');
const featureFlagsRouter = require('./routes/featureFlags');
const analyticsRouter = require('./routes/analytics');
// OAuth routes - 只在有 Auth0 設定時載入
const auth0Enabled = process.env.AUTH0_DOMAIN &&
                     process.env.AUTH0_CLIENT_ID &&
                     process.env.AUTH0_CLIENT_SECRET;
const oauthRouter = auth0Enabled ? require('./routes/oauth') : null;
// Fault injection router (integrated into main API)
const faultRouter = require('./routes/fault');

const app = express();
const PORT = process.env.PORT || 3000;

/**
 * 📌 Middleware 設定
 * 中介軟體的順序很重要！
 */

// CORS - 允許跨域請求
// CORS - 允許跨域請求，並允許帶上 credentials（cookie）
const corsOptions = {
    origin: process.env.FRONTEND_URL || true,
    credentials: true
};
app.use(cors(corsOptions));

// Body Parser - 解析請求內容
app.use(express.json());  // 解析 JSON
app.use(express.urlencoded({ extended: true }));  // 解析表單資料

/**
 * 🔐 Session 設定
 * 
 * Session 用來追蹤使用者的登入狀態
 * 即使我們用 JWT，Passport 還是需要 session 來運作
 * 
 * 運作原理：
 * 1. 使用者登入成功後，session 儲存使用者 ID
 * 2. Express 給使用者一個 session cookie
 * 3. 使用者之後的請求會帶著這個 cookie
 * 4. Express 用 cookie 找到對應的 session
 * 5. Passport 從 session 中取得使用者 ID
 * 6. 呼叫 deserializeUser 取得完整使用者資料
 */
app.use(session({
    // Session 的加密密鑰（請用環境變數！）
    secret: process.env.SESSION_SECRET || 'tixmaster-session-secret-change-this',

    // 不要在每次請求都重新儲存 session（效能優化）
    resave: false,

    // 不要為未登入的使用者建立 session
    saveUninitialized: false,

        // Cookie 設定
        cookie: {
            // Cookie 有效期限（7 天）
            maxAge: 7 * 24 * 60 * 60 * 1000,

            // HttpOnly: 防止 JavaScript 存取 cookie（防 XSS 攻擊）
            httpOnly: true,

            // Secure: 只在 HTTPS 使用（生產環境應該設為 true）
            secure: process.env.NODE_ENV === 'production',

            // sameSite: 在 OAuth callback 時，瀏覽器是否會帶上 cookie
            // 在 production（跨站重導回）情況下使用 'none' 並搭配 secure=true
            sameSite: process.env.NODE_ENV === 'production' ? 'none' : 'lax'
        }
}));

    // 當部署在 proxy（如 Railway）時，需要信任 proxy 以正確處理 secure cookie
    app.set('trust proxy', 1);

/**
 * 🔑 Passport 初始化
 *
 * 必須在 session 之後初始化！
 */
app.use(passport.initialize());  // 初始化 Passport
app.use(passport.session());     // 讓 Passport 使用 session

/**
 * 📝 Logger Middleware
 *
 * 為每個請求添加日誌記錄與 correlation ID
 * 必須在所有路由之前使用
 */
app.use(logger.middleware);

/**
 * 📊 Metrics Middleware
 *
 * 自動追蹤所有 HTTP 請求的 metrics
 * 必須在 logger 之後、路由之前使用
 */
app.use(metricsMiddleware);

/**
 * 🚩 Feature Flags Middleware
 *
 * 如果沒有設定 DATABASE_URL 或明確要求跳過 DB（SKIP_DB=true），
 * 我們會替換 middleware 為一個不依賴 DB 的簡易實作，避免在 CI 或本機沒有 DB 時啟動失敗。
 */
const skipDb = process.env.SKIP_DB === 'true' || !process.env.DATABASE_URL;
if (skipDb) {
    logger.warn('[FeatureFlags] DATABASE_URL not set or SKIP_DB=true — using dummy feature flags');
    // stub attachFeatureFlags
    featureFlagsMiddleware.attachFeatureFlags = (req, res, next) => {
        req.featureFlags = {
            isEnabled: () => false,
            getAll: () => ({})
        };
        next();
    };
    // stub initialize to a no-op
    featureFlagsMiddleware.initialize = async () => {
        logger.info('[FeatureFlags] initialize skipped (no DATABASE_URL)');
    };
}

app.use(featureFlagsMiddleware.attachFeatureFlags);

/**
 * 🏥 Health check endpoint
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'OK',
        message: 'TixMaster API is running',
        oauth: 'enabled'  // 標記 OAuth 已啟用
    });
});

/**
 * 📊 Metrics endpoint (Prometheus format)
 *
 * 這個端點提供 Prometheus 格式的 metrics
 * Prometheus 會定期抓取這個端點來收集數據
 */
app.get('/metrics', async (req, res) => {
    try {
        res.set('Content-Type', register.contentType);
        res.end(await register.metrics());
    } catch (error) {
        logger.error('Error generating metrics', { error: error.message });
        res.status(500).end(error.message);
    }
});

/**
 * 🌐 路由註冊
 *
 * 注意：OAuth 路由使用 /auth，不是 /api/auth
 * 這樣 Google 的重導向 URL 才會正確
 */

// OAuth 認證路由（只在有 Auth0 設定時啟用）
if (oauthRouter) {
    app.use('/auth', oauthRouter);
}

// 原有的 API 路由
app.use('/api/users', usersRouter);
app.use('/api/events', eventsRouter);
app.use('/api/tickets', ticketsRouter);
app.use('/api/orders', ordersRouter);
app.use('/api/feature-flags', featureFlagsRouter);
app.use('/api/analytics', analyticsRouter);
// Fault endpoints mounted under main API (guarded by ENABLE_FAULT_ENDPOINTS)
app.use('/api/fault', faultRouter);

/**
 * 💥 Crash API - 用於測試監控系統
 *
 * 這個端點會故意讓伺服器當機，用來測試：
 * - 日誌系統是否正確記錄錯誤
 * - 監控系統是否能偵測到伺服器掛掉
 * - 警報系統是否會觸發
 */
app.post('/api/crash', (req, res) => {
    logger.error('💥 CRASH API called - Server will crash intentionally', {
        endpoint: '/api/crash',
        method: 'POST',
        timestamp: new Date().toISOString()
    });

    // 延遲 100ms 讓 log 能寫入
    setTimeout(() => {
        process.exit(1);  // 強制退出程式
    }, 100);

    // 回應訊息（可能來不及送出）
    res.status(200).json({
        message: 'Server crashing...',
        note: 'This is intentional for monitoring testing'
    });
});

/**
 * 🐢 Slow API - 用於測試高延遲監控
 *
 * 這個端點會故意延遲回應，用來測試：
 * - 監控系統是否能偵測到高延遲
 * - HighLatency 警報是否會觸發
 */
app.get('/api/slow', (req, res) => {
    const delay = parseInt(req.query.delay) || 6000; // 預設延遲 6 秒 (超過警報閾值 5 秒)
    
    logger.warn(`🐢 SLOW API called - Delaying response for ${delay}ms`, {
        endpoint: '/api/slow',
        method: 'GET',
        delay: delay
    });

    setTimeout(() => {
        res.json({
            message: 'Sorry for the delay!',
            delay: delay
        });
    }, delay);
});

/**
 * 📄 靜態檔案服務
 *
 * 原本程式使用相對路徑 express.static('../')，在不同平台或
 * Docker 工作目錄下可能找不到靜態檔案，導致回傳 404 JSON
 * ("Endpoint not found").這裡改為使用絕對路徑並加上容錯處理：
 * - 以 backend 的 __dirname 向上尋找 repo root
 * - 若找不到靜態資料夾或 index.html，會在 logs 顯示警告
 */
// Try to locate a static directory that contains index.html. Different
// deployment environments (Railway/Render/Docker) may place the repo at
// different working directories, so probe several likely candidates.
// Prefer a dedicated frontend folder if present. This makes the repo
// layout explicit and easier to maintain. Non-destructive: server will
// still probe other legacy locations.
const candidates = [
    path.join(__dirname, '..', 'frontend'),      // repo root/frontend (preferred)
    path.join(__dirname, '..', 'frontend', 'public'),
    path.join(__dirname, '..'),                   // repo root relative to backend
    path.join(__dirname, '..', 'public'),        // repo root / public
    path.join(__dirname, 'public'),              // backend/public
    path.join(process.cwd(), '..'),              // parent of current cwd
    path.join(process.cwd(), '.'),               // current working dir
    path.resolve('/workspace'),                  // some CI use /workspace
    path.resolve('/')                            // fallback to root
];

let chosenStatic = null;
for (const c of candidates) {
    try {
        const idx = path.join(c, 'index.html');
        if (fs.existsSync(idx)) {
            chosenStatic = c;
            logger.info(`[static] Found index.html in ${c}`);
            break;
        }
    } catch (e) {
        // ignore inaccessible paths
    }
}

if (chosenStatic) {
    logger.info(`[static] Serving static files from ${chosenStatic}`);
    app.use(express.static(chosenStatic));
} else {
    logger.warn('[static] Warning: could not locate index.html in any candidate paths.');
    logger.warn('[static] Candidates checked:', { candidates: candidates.join(', ') });
}

// Fallback: for non-API and non-auth routes, serve index.html if present in chosenStatic
app.use((req, res, next) => {
    if (req.path.startsWith('/api') || req.path.startsWith('/auth')) return next();

    if (chosenStatic) {
        const indexFile = path.join(chosenStatic, 'index.html');
        if (fs.existsSync(indexFile)) {
            return res.sendFile(indexFile);
        }
    }

    // No index.html found — continue to next handler which will return JSON 404
    return next();
});

/**
 * ❌ 404 處理
 */
app.use((req, res) => {
    res.status(404).json({ error: 'Endpoint not found' });
});

/**
 * 🚨 錯誤處理（必須放最後！）
 */
app.use(errorHandler);

/**
 * 🚀 啟動伺服器
 */
app.listen(PORT, async () => {
    logger.info(`🚀 TixMaster API server running on http://localhost:${PORT}`);
    logger.info(`📊 Health check: http://localhost:${PORT}/health`);
    logger.info(`📈 Metrics (Prometheus): http://localhost:${PORT}/metrics`);
    logger.info(`🔐 OAuth routes:`);
    logger.info(`   - Google login: http://localhost:${PORT}/auth/google`);
    logger.info(`   - Callback: http://localhost:${PORT}/auth/google/callback`);
    logger.info(`🚩 Feature flags: http://localhost:${PORT}/api/feature-flags`);
    logger.info(`💥 Crash API: http://localhost:${PORT}/api/crash (POST)`);
    logger.info(`🐢 Slow API: http://localhost:${PORT}/api/slow (GET)`);

    // Initialize feature flags
    try {
        await featureFlagsMiddleware.initialize();
        logger.info(`✅ Feature flags initialized`);
    } catch (error) {
        logger.error(`❌ Failed to initialize feature flags:`, { error: error.message, stack: error.stack });
    }
});

module.exports = app;
