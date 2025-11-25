/**
 * 執行資料庫遷移
 */

const db = require('./config/database');
const fs = require('fs');
const path = require('path');

async function migrate() {
    try {
        console.log('開始資料庫遷移...\n');

        // 讀取 SQL 檔案
        const sqlFile = path.join(__dirname, 'add_password_hash.sql');
        const sql = fs.readFileSync(sqlFile, 'utf8');

        // 執行 SQL
        await db.query(sql);

        console.log('✅ 遷移完成！\n');

        // 驗證結果
        const result = await db.query(`
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'password_hash'
        `);

        if (result.rows.length > 0) {
            console.log('✅ password_hash 欄位已成功添加到 users 表');
        } else {
            console.log('❌ 欄位添加失敗');
        }

        process.exit(0);
    } catch (error) {
        console.error('❌ 遷移失敗:', error.message);
        process.exit(1);
    }
}

migrate();
