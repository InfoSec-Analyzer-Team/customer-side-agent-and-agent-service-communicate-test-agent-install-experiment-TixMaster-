/**
 * 檢查管理員帳號是否存在
 */

const db = require('./config/database');

async function checkAdmin() {
    try {
        console.log('正在檢查管理員帳號...\n');

        // 查詢管理員
        const result = await db.query(
            'SELECT id, email, name, phone, role, created_at FROM users WHERE email = $1',
            ['admin@tixmaster.com']
        );

        if (result.rows.length === 0) {
            console.log('❌ 管理員帳號不存在');
            console.log('\n請執行以下命令創建管理員：');
            console.log('  cd c:\\_AG11\\TixMaster');
            console.log('  .\\create_admin.ps1');
            console.log('\n或手動執行 SQL：');
            console.log('  psql -U postgres -d tixmaster -f create_admin.sql');
        } else {
            const admin = result.rows[0];
            console.log('✅ 管理員帳號已存在\n');
            console.log('ID:', admin.id);
            console.log('Email:', admin.email);
            console.log('姓名:', admin.name);
            console.log('手機:', admin.phone);
            console.log('角色:', admin.role);
            console.log('創建時間:', admin.created_at);

            console.log('\n登入資訊：');
            console.log("  URL: /admin-login.html  (訪問你的部署主機的此路徑)");
            console.log('  Email: admin@tixmaster.com');
            console.log('  密碼: admin123');
        }

        process.exit(0);
    } catch (error) {
        console.error('❌ 錯誤:', error.message);
        process.exit(1);
    }
}

checkAdmin();
