/**
 * 一鍵設置管理員
 * 自動執行所有必要步驟
 */

const db = require('./config/database');
const fs = require('fs');
const path = require('path');

async function setupAdmin() {
    console.log('='.repeat(60));
    console.log('🚀 TixMaster 管理員自動設置');
    console.log('='.repeat(60));
    console.log('');

    try {
        // Step 1: 檢查並添加 password_hash 欄位
        console.log('📋 步驟 1/3: 檢查資料庫結構...');

        const columnCheck = await db.query(`
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'password_hash'
        `);

        if (columnCheck.rows.length === 0) {
            console.log('  ⚠️  缺少 password_hash 欄位，正在添加...');

            const sqlFile = path.join(__dirname, 'add_password_hash.sql');
            const sql = fs.readFileSync(sqlFile, 'utf8');
            await db.query(sql);

            console.log('  ✅ password_hash 欄位已添加');
        } else {
            console.log('  ✅ password_hash 欄位已存在');
        }

        console.log('');

        // Step 2: 檢查並創建管理員帳號
        console.log('👤 步驟 2/3: 檢查管理員帳號...');

        const adminCheck = await db.query(
            'SELECT id, email, name, role FROM users WHERE email = $1',
            ['admin@tixmaster.com']
        );

        if (adminCheck.rows.length === 0) {
            console.log('  ⚠️  管理員帳號不存在，正在創建...');

            const passwordHash = '$2b$10$SJHcEDF1dBZ03/eJNSXyyeE1Y6pqzgYN/x1X/Si7ivm0gFEe2MUgG';

            const result = await db.query(
                `INSERT INTO users (email, password_hash, name, phone, role, created_at, updated_at)
                 VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                 RETURNING id, email, name, role`,
                ['admin@tixmaster.com', passwordHash, 'System Admin', '0900000000', 'admin']
            );

            const admin = result.rows[0];
            console.log('  ✅ 管理員帳號已創建');
            console.log('     ID:', admin.id);
            console.log('     Email:', admin.email);
        } else {
            const admin = adminCheck.rows[0];
            console.log('  ✅ 管理員帳號已存在');
            console.log('     ID:', admin.id);
            console.log('     Email:', admin.email);
            console.log('     角色:', admin.role);

            // 確保角色是 admin
            if (admin.role !== 'admin') {
                console.log('  ⚠️  角色不是 admin，正在更新...');
                await db.query(
                    'UPDATE users SET role = $1 WHERE email = $2',
                    ['admin', 'admin@tixmaster.com']
                );
                console.log('  ✅ 角色已更新為 admin');
            }
        }

        console.log('');

        // Step 3: 驗證設置
        console.log('🔍 步驟 3/3: 驗證設置...');

        const verifyResult = await db.query(
            'SELECT id, email, name, role FROM users WHERE email = $1 AND role = $2',
            ['admin@tixmaster.com', 'admin']
        );

        if (verifyResult.rows.length > 0) {
            console.log('  ✅ 驗證通過！管理員帳號設置完成');
        } else {
            throw new Error('驗證失敗：無法找到管理員帳號');
        }

        console.log('');
        console.log('='.repeat(60));
        console.log('✅ 設置完成！');
        console.log('='.repeat(60));
        console.log('');
        console.log('📝 登入資訊：');
        console.log('   URL:      http://localhost:3000/admin-login.html');
        console.log('   Email:    admin@tixmaster.com');
        console.log('   密碼:     admin123');
        console.log('');
        console.log('💡 下一步：');
        console.log('   1. 確保後端運行: npm start');
        console.log('   2. 訪問管理員登入頁面');
        console.log('   3. 使用上述帳密登入');
        console.log('');

        process.exit(0);
    } catch (error) {
        console.error('');
        console.error('❌ 設置失敗:', error.message);
        console.error('');
        console.error('請檢查：');
        console.error('  1. PostgreSQL 是否運行');
        console.error('  2. 資料庫 tixmaster 是否存在');
        console.error('  3. .env 檔案設置是否正確');
        console.error('');
        process.exit(1);
    }
}

setupAdmin();
