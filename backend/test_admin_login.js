/**
 * 測試管理員登入 API
 */

const fetch = require('node-fetch');

async function testLogin() {
    try {
        console.log('測試管理員登入 API...\n');

        const response = await fetch('http://localhost:3000/api/users/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: 'admin@tixmaster.com',
                password: 'admin123'
            })
        });

        console.log('狀態碼:', response.status, response.statusText);

        const data = await response.json();

        if (response.ok) {
            console.log('\n✅ 登入成功！\n');
            console.log('Token:', data.token.substring(0, 50) + '...');
            console.log('\n使用者資訊:');
            console.log('  ID:', data.user.id);
            console.log('  Email:', data.user.email);
            console.log('  姓名:', data.user.name);
            console.log('  角色:', data.user.role);

            if (data.user.role === 'admin') {
                console.log('\n✅ 角色驗證通過：管理員');
            } else {
                console.log('\n❌ 角色驗證失敗：不是管理員');
            }
        } else {
            console.log('\n❌ 登入失敗');
            console.log('錯誤:', data.error || data.message);
        }

        process.exit(0);
    } catch (error) {
        console.error('\n❌ 測試失敗:', error.message);
        console.log('\n請確認後端伺服器已啟動：');
        console.log('  cd backend');
        console.log('  npm start');
        process.exit(1);
    }
}

testLogin();
