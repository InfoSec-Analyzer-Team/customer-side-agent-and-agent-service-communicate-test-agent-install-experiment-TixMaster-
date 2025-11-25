const express = require('express');
const router = express.Router();
const passport = require('../config/passport');
const jwt = require('jsonwebtoken');
const { ROLES } = require('../config/roles');

/**
 * 🚀 OAuth 路由檔案
 * 
 * 這個檔案處理三個主要功能：
 * 1. 啟動 Google OAuth 流程
 * 2. 處理 Google 回調
 * 3. 登出功能
 */

/**
 * 路由 1: GET /auth/google
 * 🎯 啟動 Google OAuth 流程
 * 
 * 當使用者點擊「Google 登入」按鈕時，會導向這個路由
 * Passport 會自動把使用者重導向到 Google 登入頁面
 * 
 * 流程：
 * 1. 使用者點擊「Google 登入」
 * 2. 前端導向 http://localhost:3000/auth/google
 * 3. Passport 重導向到 Google 登入頁面（附帶 client_id, redirect_uri 等參數）
 * 4. 使用者在 Google 頁面登入並授權
 */
// 開始 Auth0 登入流程
router.get('/login',
    passport.authenticate('auth0', {
        scope: ['openid', 'profile', 'email'],
        session: false
    })
);

// 開始 Auth0 Signup（註冊）流程 - 會在 Auth0 下啟用 signup 畫面
router.get('/signup',
    passport.authenticate('auth0', {
        scope: ['openid', 'profile', 'email'],
        session: false,
        authParams: { screen_hint: 'signup' }
    })
);

/**
 * 路由 2: GET /auth/google/callback
 * 🔄 處理 Google 授權回調
 * 
 * Google 授權成功後會跳回這個路由，並帶著 authorization code
 * Passport 會自動用 code 換取 access_token，並呼叫 verify callback
 * 
 * 流程：
 * 1. Google 重導回 http://localhost:3000/auth/google/callback?code=xxx
 * 2. Passport 用 code 換 token
 * 3. Passport 取得使用者資料
 * 4. 呼叫我們在 passport.js 寫的 verify callback
 * 5. 如果成功，執行下面的回調函數
 * 
 * URL 參數：
 * - ?code=xxx          (成功時)
 * - ?error=xxx         (失敗時)
 */
router.get('/callback',
    // 先印出 callback 收到的 query（Auth0 會傳回 code / error / state）
    (req, res, next) => {
        console.log('[Auth0] /auth/callback query =', req.query);
        next();
    },
    // 使用 custom callback 以便在失敗時記錄更詳細資訊
    (req, res, next) => {
        passport.authenticate('auth0', { session: false }, (err, user, info) => {
            if (err) {
                console.error('❌ passport authenticate error:', err, info);
                return res.redirect('/login.html?error=oauth_failed');
            }
            if (!user) {
                console.error('❌ passport authenticate failed, info:', info);
                return res.redirect('/login.html?error=oauth_failed');
            }
            // 將 user 掛回 req，進入下一個處理器
            req.user = user;
            next();
        })(req, res, next);
    },

    async (req, res) => {
        try {
            const user = req.user;
            console.log('✅ Auth0 登入成功:', user && user.email);

            const token = jwt.sign(
                {
                    userId: user.id,
                    email: user.email,
                    role: user.role || ROLES.USER,
                    loginMethod: 'auth0'
                },
                process.env.JWT_SECRET,
                { expiresIn: '7d' }
            );

            // 透過 URL fragment 回傳 token（前端會解析並儲存）
            res.redirect(`/login.html#token=${token}`);

        } catch (error) {
            console.error('❌ 回調處理錯誤:', error);
            res.redirect('/login.html?error=server_error');
        }
    }
);

/**
 * 路由 3: GET /auth/logout
 * 🚪 登出功能
 * 
 * 清除 session 並登出
 * （如果使用 JWT，前端只需刪除 localStorage 中的 token）
 */
router.get('/logout', (req, res) => {
    // 如果使用 Passport session
    req.logout((err) => {
        if (err) {
            console.error('❌ 登出錯誤:', err);
            return res.status(500).json({ error: 'Logout failed' });
        }

        console.log('👋 使用者登出');
        res.json({ message: 'Logged out successfully' });
    });
});

/**
 * 路由 4: GET /auth/status
 * 📊 檢查登入狀態（測試用）
 * 
 * 回傳目前使用者的登入狀態
 */
router.get('/status', (req, res) => {
    if (req.user) {
        res.json({
            loggedIn: true,
            user: {
                id: req.user.id,
                email: req.user.email,
                name: req.user.name
            }
        });
    } else {
        res.json({
            loggedIn: false
        });
    }
});

module.exports = router;
