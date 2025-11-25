#!/usr/bin/env node
/**
 * Feature Flags Toggle 測試腳本
 *
 * 測試 toggle 功能的 true/false 控制
 */

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_BASE = `${BASE_URL}/api`;

// 顏色輸出
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
    console.log('\n' + '='.repeat(60));
    log(title, 'cyan');
    console.log('='.repeat(60));
}

function logTest(name) {
    log(`\n🧪 測試: ${name}`, 'blue');
}

function logSuccess(message) {
    log(`✅ ${message}`, 'green');
}

function logError(message) {
    log(`❌ ${message}`, 'red');
}

function logInfo(message) {
    log(`ℹ️  ${message}`, 'yellow');
}

// 測試結果統計
let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function recordTest(passed, testName) {
    totalTests++;
    if (passed) {
        passedTests++;
        logSuccess(`通過: ${testName}`);
    } else {
        failedTests++;
        logError(`失敗: ${testName}`);
    }
}

// 延遲函數
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 取得所有功能開關
async function getAllFlags() {
    const response = await fetch(`${API_BASE}/feature-flags`);
    return await response.json();
}

// 取得單一功能開關
async function getFlag(key) {
    const response = await fetch(`${API_BASE}/feature-flags/${key}`);
    return await response.json();
}

// 更新功能開關
async function updateFlag(key, enabled) {
    logInfo(`發送 PUT 請求: ${key} = ${enabled} (type: ${typeof enabled})`);

    const response = await fetch(`${API_BASE}/feature-flags/${key}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled })
    });

    const data = await response.json();

    if (!response.ok) {
        logError(`HTTP ${response.status}: ${JSON.stringify(data)}`);
        throw new Error(`Update failed: ${JSON.stringify(data)}`);
    }

    return data;
}

// 測試 1: 讀取初始狀態
async function test1_readInitialState() {
    logTest('讀取初始狀態');

    try {
        const data = await getAllFlags();
        console.log('當前狀態:', JSON.stringify(data, null, 2));

        const hasCheckoutTimer = data.flags.ENABLE_CHECKOUT_TIMER !== undefined;
        const hasViewingCount = data.flags.ENABLE_VIEWING_COUNT !== undefined;

        recordTest(hasCheckoutTimer && hasViewingCount, '讀取所有功能開關');

        return data.flags;
    } catch (error) {
        logError(`讀取失敗: ${error.message}`);
        recordTest(false, '讀取所有功能開關');
        throw error;
    }
}

// 測試 2: Toggle CHECKOUT_TIMER (false -> true)
async function test2_toggleCheckoutTimerOn() {
    logTest('啟用 CHECKOUT_TIMER (false -> true)');

    try {
        // 先設為 false
        await updateFlag('ENABLE_CHECKOUT_TIMER', false);
        await delay(500);

        // 讀取確認
        let flag = await getFlag('ENABLE_CHECKOUT_TIMER');
        logInfo(`設為 false 後: ${flag.enabled}`);
        recordTest(flag.enabled === false, 'CHECKOUT_TIMER 設為 false');

        await delay(500);

        // 切換為 true
        await updateFlag('ENABLE_CHECKOUT_TIMER', true);
        await delay(500);

        // 讀取確認
        flag = await getFlag('ENABLE_CHECKOUT_TIMER');
        logInfo(`設為 true 後: ${flag.enabled}`);
        recordTest(flag.enabled === true, 'CHECKOUT_TIMER 切換為 true');

        return flag;
    } catch (error) {
        logError(`測試失敗: ${error.message}`);
        recordTest(false, 'CHECKOUT_TIMER toggle (false -> true)');
        throw error;
    }
}

// 測試 3: Toggle CHECKOUT_TIMER (true -> false)
async function test3_toggleCheckoutTimerOff() {
    logTest('停用 CHECKOUT_TIMER (true -> false)');

    try {
        // 先設為 true
        await updateFlag('ENABLE_CHECKOUT_TIMER', true);
        await delay(500);

        // 讀取確認
        let flag = await getFlag('ENABLE_CHECKOUT_TIMER');
        logInfo(`設為 true 後: ${flag.enabled}`);
        recordTest(flag.enabled === true, 'CHECKOUT_TIMER 設為 true');

        await delay(500);

        // 切換為 false
        await updateFlag('ENABLE_CHECKOUT_TIMER', false);
        await delay(500);

        // 讀取確認
        flag = await getFlag('ENABLE_CHECKOUT_TIMER');
        logInfo(`設為 false 後: ${flag.enabled}`);
        recordTest(flag.enabled === false, 'CHECKOUT_TIMER 切換為 false');

        return flag;
    } catch (error) {
        logError(`測試失敗: ${error.message}`);
        recordTest(false, 'CHECKOUT_TIMER toggle (true -> false)');
        throw error;
    }
}

// 測試 4: Toggle VIEWING_COUNT (false -> true)
async function test4_toggleViewingCountOn() {
    logTest('啟用 VIEWING_COUNT (false -> true)');

    try {
        await updateFlag('ENABLE_VIEWING_COUNT', false);
        await delay(500);

        let flag = await getFlag('ENABLE_VIEWING_COUNT');
        logInfo(`設為 false 後: ${flag.enabled}`);
        recordTest(flag.enabled === false, 'VIEWING_COUNT 設為 false');

        await delay(500);

        await updateFlag('ENABLE_VIEWING_COUNT', true);
        await delay(500);

        flag = await getFlag('ENABLE_VIEWING_COUNT');
        logInfo(`設為 true 後: ${flag.enabled}`);
        recordTest(flag.enabled === true, 'VIEWING_COUNT 切換為 true');

        return flag;
    } catch (error) {
        logError(`測試失敗: ${error.message}`);
        recordTest(false, 'VIEWING_COUNT toggle (false -> true)');
        throw error;
    }
}

// 測試 5: Toggle VIEWING_COUNT (true -> false)
async function test5_toggleViewingCountOff() {
    logTest('停用 VIEWING_COUNT (true -> false)');

    try {
        await updateFlag('ENABLE_VIEWING_COUNT', true);
        await delay(500);

        let flag = await getFlag('ENABLE_VIEWING_COUNT');
        logInfo(`設為 true 後: ${flag.enabled}`);
        recordTest(flag.enabled === true, 'VIEWING_COUNT 設為 true');

        await delay(500);

        await updateFlag('ENABLE_VIEWING_COUNT', false);
        await delay(500);

        flag = await getFlag('ENABLE_VIEWING_COUNT');
        logInfo(`設為 false 後: ${flag.enabled}`);
        recordTest(flag.enabled === false, 'VIEWING_COUNT 切換為 false');

        return flag;
    } catch (error) {
        logError(`測試失敗: ${error.message}`);
        recordTest(false, 'VIEWING_COUNT toggle (true -> false)');
        throw error;
    }
}

// 測試 6: 快速連續切換
async function test6_rapidToggle() {
    logTest('快速連續切換測試');

    try {
        const key = 'ENABLE_CHECKOUT_TIMER';

        // 快速切換 5 次
        for (let i = 0; i < 5; i++) {
            const enabled = i % 2 === 0;
            await updateFlag(key, enabled);
            logInfo(`第 ${i + 1} 次切換: ${enabled}`);
            await delay(200);
        }

        // 最終確認
        const flag = await getFlag(key);
        logInfo(`最終狀態: ${flag.enabled}`);
        recordTest(flag.enabled === false, '快速連續切換後狀態正確');

        return flag;
    } catch (error) {
        logError(`測試失敗: ${error.message}`);
        recordTest(false, '快速連續切換');
        throw error;
    }
}

// 測試 7: 同時更新兩個開關
async function test7_updateBothFlags() {
    logTest('同時更新兩個功能開關');

    try {
        // 同時設定兩個開關
        await Promise.all([
            updateFlag('ENABLE_CHECKOUT_TIMER', true),
            updateFlag('ENABLE_VIEWING_COUNT', true)
        ]);

        await delay(500);

        // 讀取確認
        const data = await getAllFlags();
        const bothEnabled =
            data.flags.ENABLE_CHECKOUT_TIMER.enabled === true &&
            data.flags.ENABLE_VIEWING_COUNT.enabled === true;

        logInfo(`CHECKOUT_TIMER: ${data.flags.ENABLE_CHECKOUT_TIMER.enabled}`);
        logInfo(`VIEWING_COUNT: ${data.flags.ENABLE_VIEWING_COUNT.enabled}`);

        recordTest(bothEnabled, '同時啟用兩個開關');

        return data.flags;
    } catch (error) {
        logError(`測試失敗: ${error.message}`);
        recordTest(false, '同時更新兩個開關');
        throw error;
    }
}

// 測試 8: 型別檢查
async function test8_typeValidation() {
    logTest('型別檢查測試');

    try {
        // 測試錯誤的型別
        const response = await fetch(`${API_BASE}/feature-flags/ENABLE_CHECKOUT_TIMER`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ enabled: 'true' }) // 字串而非 boolean
        });

        const shouldFail = response.status === 400;
        logInfo(`發送字串 'true' -> HTTP ${response.status}`);
        recordTest(shouldFail, '拒絕非 boolean 值');

        // 測試正確的 boolean
        const response2 = await fetch(`${API_BASE}/feature-flags/ENABLE_CHECKOUT_TIMER`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ enabled: true }) // 正確的 boolean
        });

        const shouldPass = response2.status === 200;
        logInfo(`發送 boolean true -> HTTP ${response2.status}`);
        recordTest(shouldPass, '接受 boolean 值');

    } catch (error) {
        logError(`測試失敗: ${error.message}`);
        recordTest(false, '型別檢查');
    }
}

// 主測試流程
async function runAllTests() {
    logSection('🚀 開始 Feature Flags Toggle 測試');

    try {
        // 檢查後端連線
        logTest('檢查後端連線');
    const healthResponse = await fetch(`${BASE_URL}/health`);
        if (!healthResponse.ok) {
            throw new Error('後端伺服器未運行');
        }
        logSuccess('後端伺服器連線正常');

        // 執行測試
        await test1_readInitialState();
        await delay(1000);

        await test2_toggleCheckoutTimerOn();
        await delay(1000);

        await test3_toggleCheckoutTimerOff();
        await delay(1000);

        await test4_toggleViewingCountOn();
        await delay(1000);

        await test5_toggleViewingCountOff();
        await delay(1000);

        await test6_rapidToggle();
        await delay(1000);

        await test7_updateBothFlags();
        await delay(1000);

        await test8_typeValidation();

    } catch (error) {
        logError(`測試中斷: ${error.message}`);
    }

    // 顯示測試結果
    logSection('📊 測試結果');
    console.log(`總測試數: ${totalTests}`);
    logSuccess(`通過: ${passedTests}`);
    if (failedTests > 0) {
        logError(`失敗: ${failedTests}`);
    } else {
        logSuccess('全部測試通過！🎉');
    }

    const passRate = ((passedTests / totalTests) * 100).toFixed(1);
    log(`\n通過率: ${passRate}%\n`, passRate === '100.0' ? 'green' : 'yellow');
}

// 執行測試
runAllTests().catch(error => {
    logError(`執行失敗: ${error.message}`);
    process.exit(1);
});
