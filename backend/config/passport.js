const passport = require('passport');
const Auth0Strategy = require('passport-auth0');
const db = require('./database');

/**
 * 🔍 Passport.js 設定檔
 * 
 * Passport 是一個認證中介軟體，它的工作流程：
 * 1. 使用者點擊「Google 登入」
 * 2. Passport 帶使用者去 Google 登入頁面
 * 3. 使用者授權後，Google 回傳資料給我們
 * 4. Passport 呼叫 verify callback（下面的函數）
 * 5. 我們在 callback 中處理使用者資料（存入資料庫）
 */

// 設定 Auth0 OAuth 策略
passport.use(new Auth0Strategy({
    domain: process.env.AUTH0_DOMAIN,
    clientID: process.env.AUTH0_CLIENT_ID,
    clientSecret: process.env.AUTH0_CLIENT_SECRET,
    callbackURL: process.env.AUTH0_CALLBACK_URL || "http://localhost:3000/auth/callback",
    scope: 'openid profile email'
},

    async function (accessToken, refreshToken, extraParams, profile, done) {
        try {
            console.log('📧 Auth0 OAuth - 收到使用者資料:', profile.displayName || profile.username);

            const providerId = profile.id;

            // Step 1: 檢查這個 Auth0 帳號是否已經註冊過
            const oauthCheck = await db.query(
                'SELECT * FROM oauth_accounts WHERE provider = $1 AND provider_user_id = $2',
                ['auth0', providerId]
            );

            let user;

            if (oauthCheck.rows.length > 0) {
                console.log('✅ 使用者已存在，直接登入');
                const oauthAccount = oauthCheck.rows[0];

                const userResult = await db.query(
                    'SELECT id, email, name, phone, role FROM users WHERE id = $1',
                    [oauthAccount.user_id]
                );

                user = userResult.rows[0];

                // 更新 token
                await db.query(
                    `UPDATE oauth_accounts 
           SET access_token = $1, 
               refresh_token = $2, 
               token_expires_at = NOW() + INTERVAL '1 hour',
               updated_at = NOW()
           WHERE id = $3`,
                    [accessToken, refreshToken, oauthAccount.id]
                );

            } else {
                console.log('🆕 新使用者或連結現有帳號');

                const email = profile.emails && profile.emails[0] ? profile.emails[0].value : null;
                const name = profile.displayName || profile.username || 'Auth0 User';

                // 如果此 email 已存在，將 OAuth 帳號連結到現有使用者
                const existingUser = email ? await db.query('SELECT * FROM users WHERE email = $1', [email]) : { rows: [] };

                if (existingUser.rows.length > 0) {
                    user = existingUser.rows[0];
                } else {
                    const userResult = await db.query(
                        `INSERT INTO users (email, name, password_hash, created_at) 
             VALUES ($1, $2, NULL, NOW()) 
             RETURNING id, email, name, phone, role`,
                        [email, name]
                    );
                    user = userResult.rows[0];
                }

                await db.query(
                    `INSERT INTO oauth_accounts 
           (user_id, provider, provider_user_id, access_token, refresh_token, token_expires_at, created_at)
           VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '1 hour', NOW())`,
                    [user.id, 'auth0', providerId, accessToken, refreshToken]
                );
            }

            done(null, user);

        } catch (error) {
            console.error('❌ Auth0 OAuth 錯誤:', error);
            done(error, null);
        }
    }
));

/**
 * 🔐 serializeUser - 決定要在 session 中儲存什麼
 * 
 * 登入成功後，Passport 會呼叫這個函數
 * 我們只儲存 user.id（不要儲存整個 user 物件，太大了）
 */
passport.serializeUser((user, done) => {
    console.log('💾 序列化使用者 ID:', user.id);
    done(null, user.id);
});

/**
 * 🔓 deserializeUser - 從 session 中的 ID 取得完整使用者資料
 * 
 * 每次使用者發送請求時，Passport 會呼叫這個函數
 * 用儲存的 ID 去資料庫查詢完整資料
 */
passport.deserializeUser(async (id, done) => {
    try {
        const result = await db.query(
            'SELECT id, email, name, phone, created_at FROM users WHERE id = $1',
            [id]
        );

        if (result.rows.length === 0) {
            return done(new Error('使用者不存在'), null);
        }

        console.log('🔍 反序列化使用者:', result.rows[0].email);
        done(null, result.rows[0]);

    } catch (error) {
        console.error('❌ 反序列化錯誤:', error);
        done(error, null);
    }
});

module.exports = passport;
