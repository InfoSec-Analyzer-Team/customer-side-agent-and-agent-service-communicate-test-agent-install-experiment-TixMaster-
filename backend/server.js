const express = require('express');
const cors = require('cors');
const session = require('express-session');  // NEW - Session 管理
require('dotenv').config();
const passport = require('./config/passport');  // NEW - Passport 設定

const errorHandler = require('./middleware/errorHandler');
const featureFlagsMiddleware = require('./middleware/featureFlags');

// Import routes
const usersRouter = require('./routes/users');
const eventsRouter = require('./routes/events');
const ticketsRouter = require('./routes/tickets');
const ordersRouter = require('./routes/orders');
const featureFlagsRouter = require('./routes/featureFlags');
const analyticsRouter = require('./routes/analytics');
const oauthRouter = require('./routes/oauth');  // NEW - OAuth routes

const app = express();
const PORT = process.env.PORT || 3000;

/**
 * 📌 Middleware 設定
 * 中介軟體的順序很重要！
 */

// CORS - 允許跨域請求
app.use(cors());

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
        secure: process.env.NODE_ENV === 'production'
    }
}));

/**
 * 🔑 Passport 初始化
 *
 * 必須在 session 之後初始化！
 */
app.use(passport.initialize());  // 初始化 Passport
app.use(passport.session());     // 讓 Passport 使用 session

/**
 * 🚩 Feature Flags Middleware
 *
 * 將 feature flags 附加到每個請求
 * 可在路由中使用 req.featureFlags.isEnabled('FLAG_KEY')
 */
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
 * 🌐 路由註冊
 * 
 * 注意：OAuth 路由使用 /auth，不是 /api/auth
 * 這樣 Google 的重導向 URL 才會正確
 */

// OAuth 認證路由（新增！）
app.use('/auth', oauthRouter);

// 原有的 API 路由
app.use('/api/users', usersRouter);
app.use('/api/events', eventsRouter);
app.use('/api/tickets', ticketsRouter);
app.use('/api/orders', ordersRouter);
app.use('/api/feature-flags', featureFlagsRouter);
app.use('/api/analytics', analyticsRouter);

/**
 * 📄 靜態檔案服務（選用）
 * 
 * 如果你想直接從後端服務前端 HTML 檔案
 * 取消下面這行的註解：
 */
app.use(express.static('../'));  // 提供根目錄的靜態檔案

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
    console.log(`🚀 TixMaster API server running on http://localhost:${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`🔐 OAuth routes:`);
    console.log(`   - Google login: http://localhost:${PORT}/auth/google`);
    console.log(`   - Callback: http://localhost:${PORT}/auth/google/callback`);
    console.log(`🚩 Feature flags: http://localhost:${PORT}/api/feature-flags`);

    // Initialize feature flags
    try {
        await featureFlagsMiddleware.initialize();
        console.log(`✅ Feature flags initialized`);
    } catch (error) {
        console.error(`❌ Failed to initialize feature flags:`, error);
    }
});

module.exports = app;
