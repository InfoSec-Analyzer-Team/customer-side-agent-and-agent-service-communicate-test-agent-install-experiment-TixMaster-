#!/usr/bin/env node
/**
 * Metrics Verification Script
 *
 * 計算並驗證 Payment Completion Rate 和 Buy Now CTR
 * 用於驗證 Hypothesis 1 和 Hypothesis 2
 */

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_BASE = `${BASE_URL}/api`;

// 顏色輸出
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
    magenta: '\x1b[35m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
    console.log('\n' + '='.repeat(80));
    log(title, 'cyan');
    console.log('='.repeat(80));
}

function logMetric(label, value, unit = '') {
    const formattedValue = typeof value === 'number' ? value.toLocaleString() : value;
    log(`  ${label.padEnd(40)} ${formattedValue}${unit}`, 'bright');
}

// 獲取指標數據
async function getMetrics(startDate = null, endDate = null) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const url = `${API_BASE}/analytics/metrics${params.toString() ? '?' + params.toString() : ''}`;

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
}

// 獲取事件摘要
async function getSummary() {
    const response = await fetch(`${API_BASE}/analytics/summary`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
}

// 計算提升幅度 (Lift %)
function calculateLift(controlRate, treatmentRate) {
    if (!controlRate || controlRate === 0) return null;
    return ((treatmentRate - controlRate) / controlRate) * 100;
}

// 顯示 Hypothesis 1 結果
function displayHypothesis1(data) {
    logSection('📊 Hypothesis 1: Urgency Tactic - Payment Completion Rate');

    console.log('\n  假設：在結帳頁面加入倒數計時器，將能製造稀缺感，提升結帳完成率');
    console.log('  成功標準：付款完成率提升 ≥ 10%\n');

    if (!data || data.length === 0) {
        log('  ⚠️  尚無數據', 'yellow');
        return;
    }

    const controlGroup = data.find(d => d.has_timer === false);
    const treatmentGroup = data.find(d => d.has_timer === true);

    console.log('  Control Group (無倒數計時器):');
    if (controlGroup) {
        logMetric('總進入結帳頁次數', controlGroup.total_sessions, ' sessions');
        logMetric('完成付款次數', controlGroup.completed_payments, ' payments');
        logMetric('付款完成率', controlGroup.completion_rate_percent, '%');
    } else {
        log('    無數據', 'yellow');
    }

    console.log('\n  Treatment Group (有倒數計時器):');
    if (treatmentGroup) {
        logMetric('總進入結帳頁次數', treatmentGroup.total_sessions, ' sessions');
        logMetric('完成付款次數', treatmentGroup.completed_payments, ' payments');
        logMetric('付款完成率', treatmentGroup.completion_rate_percent, '%');
    } else {
        log('    無數據', 'yellow');
    }

    // 計算提升幅度
    if (controlGroup && treatmentGroup) {
        const lift = calculateLift(
            parseFloat(controlGroup.completion_rate_percent),
            parseFloat(treatmentGroup.completion_rate_percent)
        );

        console.log('\n  📈 結果分析:');
        if (lift !== null) {
            const liftStr = lift >= 0 ? `+${lift.toFixed(2)}%` : `${lift.toFixed(2)}%`;
            logMetric('提升幅度 (Lift)', liftStr);

            if (lift >= 10) {
                log('  ✅ 達成成功標準！(提升 ≥ 10%)', 'green');
            } else if (lift > 0) {
                log('  ⚠️  有提升但未達成功標準 (需 ≥ 10%)', 'yellow');
            } else {
                log('  ❌ 未達成功標準，倒數計時器反而降低完成率', 'red');
            }
        }
    }
}

// 顯示 Hypothesis 2 結果
function displayHypothesis2(data) {
    logSection('📊 Hypothesis 2: Social Proof - Buy Now CTR');

    console.log('\n  假設：顯示「正在瀏覽人數」將能創造 FOMO 效應，提升「立即購票」點擊率');
    console.log('  成功標準：Buy Now CTR 提升 ≥ 15%\n');

    if (!data || data.length === 0) {
        log('  ⚠️  尚無數據', 'yellow');
        return;
    }

    const controlGroup = data.find(d => d.has_viewing_count === false);
    const treatmentGroup = data.find(d => d.has_viewing_count === true);

    console.log('  Control Group (無瀏覽人數):');
    if (controlGroup) {
        logMetric('總瀏覽活動頁次數', controlGroup.total_views, ' views');
        logMetric('點擊「立即購票」次數', controlGroup.buy_clicks, ' clicks');
        logMetric('點擊率 (CTR)', controlGroup.ctr_percent, '%');
    } else {
        log('    無數據', 'yellow');
    }

    console.log('\n  Treatment Group (有瀏覽人數):');
    if (treatmentGroup) {
        logMetric('總瀏覽活動頁次數', treatmentGroup.total_views, ' views');
        logMetric('點擊「立即購票」次數', treatmentGroup.buy_clicks, ' clicks');
        logMetric('點擊率 (CTR)', treatmentGroup.ctr_percent, '%');
    } else {
        log('    無數據', 'yellow');
    }

    // 計算提升幅度
    if (controlGroup && treatmentGroup) {
        const lift = calculateLift(
            parseFloat(controlGroup.ctr_percent),
            parseFloat(treatmentGroup.ctr_percent)
        );

        console.log('\n  📈 結果分析:');
        if (lift !== null) {
            const liftStr = lift >= 0 ? `+${lift.toFixed(2)}%` : `${lift.toFixed(2)}%`;
            logMetric('提升幅度 (Lift)', liftStr);

            if (lift >= 15) {
                log('  ✅ 達成成功標準！(提升 ≥ 15%)', 'green');
            } else if (lift > 0) {
                log('  ⚠️  有提升但未達成功標準 (需 ≥ 15%)', 'yellow');
            } else {
                log('  ❌ 未達成功標準，瀏覽人數反而降低點擊率', 'red');
            }
        }
    }
}

// 顯示事件摘要
function displaySummary(summary) {
    logSection('📋 Analytics Events Summary (最近 7 天)');

    if (!summary || summary.length === 0) {
        log('  ⚠️  尚無事件記錄', 'yellow');
        return;
    }

    console.log('\n  事件類型                              次數        獨立 Sessions    最後事件時間');
    console.log('  ' + '-'.repeat(76));

    summary.forEach(event => {
        const eventType = event.event_type.padEnd(35);
        const count = String(event.count).padStart(8);
        const sessions = String(event.unique_sessions).padStart(12);
        const lastEvent = new Date(event.last_event).toLocaleString('zh-TW');

        console.log(`  ${eventType} ${count}      ${sessions}      ${lastEvent}`);
    });
}

// 主函數
async function main() {
    logSection('🚀 TixMaster - Metrics Verification Report');

    try {
        // 1. 檢查後端連線
        console.log('\n檢查後端連線...');
    const healthResponse = await fetch(`${BASE_URL}/health`);
        if (!healthResponse.ok) {
            throw new Error('後端伺服器未運行');
        }
        log('✅ 後端伺服器連線正常\n', 'green');

        // 2. 獲取事件摘要
        const { summary } = await getSummary();
        displaySummary(summary);

        // 3. 獲取指標
        console.log('\n獲取 A/B 測試指標...');
        const metrics = await getMetrics();

        // 4. 顯示 Hypothesis 1
        displayHypothesis1(metrics.hypothesis1.data);

        // 5. 顯示 Hypothesis 2
        displayHypothesis2(metrics.hypothesis2.data);

        // 6. 結論
        logSection('💡 建議');
        console.log('\n  根據以上數據分析：');
        console.log('  1. 如果兩個假設都達成功標準 → 保留兩個功能');
        console.log('  2. 如果只有一個假設達標 → 保留達標功能，移除未達標功能');
        console.log('  3. 如果兩個假設都未達標 → 移除兩個功能，或調整設計後重新測試');
        console.log('  4. 如果數據量不足 → 繼續收集更多數據再做決策\n');

        logSection('✅ 報告完成');

    } catch (error) {
        log(`\n❌ 錯誤: ${error.message}`, 'red');
        process.exit(1);
    }
}

// 執行
main().catch(error => {
    log(`執行失敗: ${error.message}`, 'red');
    process.exit(1);
});
