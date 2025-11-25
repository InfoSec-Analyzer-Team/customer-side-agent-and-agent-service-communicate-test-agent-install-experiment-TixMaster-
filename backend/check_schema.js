/**
 * 檢查 users 表結構
 */

const db = require('./config/database');

async function checkSchema() {
    try {
        console.log('正在檢查 users 表結構...\n');

        const result = await db.query(`
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        `);

        if (result.rows.length === 0) {
            console.log('❌ users 表不存在！');
            console.log('\n請執行以下命令創建資料庫結構：');
            console.log('  psql -U postgres -d tixmaster -f init.sql');
        } else {
            console.log('✅ users 表結構：\n');
            console.log('欄位名稱'.padEnd(20), '資料類型'.padEnd(20), '可空', '預設值');
            console.log('-'.repeat(80));

            result.rows.forEach(col => {
                console.log(
                    col.column_name.padEnd(20),
                    col.data_type.padEnd(20),
                    col.is_nullable.padEnd(5),
                    col.column_default || 'NULL'
                );
            });
        }

        process.exit(0);
    } catch (error) {
        console.error('❌ 錯誤:', error.message);
        process.exit(1);
    }
}

checkSchema();
