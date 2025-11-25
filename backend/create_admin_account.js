/**
 * 直接創建管理員帳號（使用 Node.js）
 */

const db = require('./config/database');
const bcrypt = require('bcrypt');

async function createAdmin() {
    try {
        console.log('正在創建管理員帳號...\n');

        // 檢查是否已存在
        const checkResult = await db.query(
            'SELECT id FROM users WHERE email = $1',
            ['admin@tixmaster.com']
        );

        if (checkResult.rows.length > 0) {
            console.log('❌ 管理員帳號已存在');
            console.log('如需重置密碼，請手動刪除後重新創建');
            process.exit(0);
        }

        // 使用預先生成的 hash（與 create_admin.sql 相同）
        const passwordHash = '$2b$10$SJHcEDF1dBZ03/eJNSXyyeE1Y6pqzgYN/x1X/Si7ivm0gFEe2MUgG';

        // 創建管理員
        const result = await db.query(
            `INSERT INTO users (email, password_hash, name, phone, role, created_at, updated_at)
             VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
             RETURNING id, email, name, role`,
            ['admin@tixmaster.com', passwordHash, 'System Admin', '0900000000', 'admin']
        );

        const admin = result.rows[0];

        console.log('✅ 管理員帳號創建成功！\n');
        console.log('ID:', admin.id);
        console.log('Email:', admin.email);
        console.log('姓名:', admin.name);
        console.log('角色:', admin.role);

    console.log('\n登入資訊：');
    console.log("  URL: /admin-login.html  (訪問你的部署主機的此路徑)");
        console.log('  Email: admin@tixmaster.com');
        console.log('  密碼: admin123');

        process.exit(0);
    } catch (error) {
        console.error('❌ 錯誤:', error.message);
        process.exit(1);
    }
}

createAdmin();
