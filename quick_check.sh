#!/bin/bash

# TixMaster 快速診斷腳本
# 用途: 快速檢查系統健康狀態
# 使用方式: ./quick_check.sh

echo "╔════════════════════════════════════════════╗"
echo "║   TixMaster 系統健康檢查                   ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "⏰ 檢查時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================
# 1. 服務狀態檢查
# ============================================
echo "📊 [1/8] 檢查服務狀態..."
HEALTH_RESPONSE=$(curl -s http://localhost:3000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    STATUS=$(echo $HEALTH_RESPONSE | jq -r '.status' 2>/dev/null)
    if [ "$STATUS" == "OK" ]; then
        echo -e "   ${GREEN}✓${NC} Backend 服務: 運行中"
    else
        echo -e "   ${RED}✗${NC} Backend 服務: 異常"
    fi
else
    echo -e "   ${RED}✗${NC} Backend 服務: 無法連接"
fi
echo ""

# ============================================
# 2. 5xx 錯誤率檢查
# ============================================
echo "❌ [2/8] 檢查 5xx 錯誤率..."
ERROR_RATE=$(curl -s "http://localhost:9091/api/v1/query?query=100*sum(rate(http_errors_total{status_code=~\"5..\"}[5m]))/sum(rate(http_requests_total[5m]))" 2>/dev/null | jq -r '.data.result[0].value[1]' 2>/dev/null)
if [ ! -z "$ERROR_RATE" ] && [ "$ERROR_RATE" != "null" ]; then
    ERROR_RATE_NUM=$(echo "$ERROR_RATE" | awk '{printf "%.2f", $1}')
    if (( $(echo "$ERROR_RATE_NUM < 0.1" | bc -l) )); then
        echo -e "   ${GREEN}✓${NC} 5xx 錯誤率: ${ERROR_RATE_NUM}% (正常)"
    elif (( $(echo "$ERROR_RATE_NUM < 1" | bc -l) )); then
        echo -e "   ${YELLOW}⚠${NC} 5xx 錯誤率: ${ERROR_RATE_NUM}% (警告)"
    else
        echo -e "   ${RED}✗${NC} 5xx 錯誤率: ${ERROR_RATE_NUM}% (危險)"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} 無法取得錯誤率數據"
fi
echo ""

# ============================================
# 3. P95 回應時間檢查
# ============================================
echo "⏱️  [3/8] 檢查 P95 回應時間..."
P95_LATENCY=$(curl -s "http://localhost:9091/api/v1/query?query=histogram_quantile(0.95,sum(rate(http_request_duration_ms_bucket[5m]))by(le))" 2>/dev/null | jq -r '.data.result[0].value[1]' 2>/dev/null)
if [ ! -z "$P95_LATENCY" ] && [ "$P95_LATENCY" != "null" ]; then
    P95_NUM=$(echo "$P95_LATENCY" | awk '{printf "%.2f", $1}')
    if (( $(echo "$P95_NUM < 500" | bc -l) )); then
        echo -e "   ${GREEN}✓${NC} P95 延遲: ${P95_NUM} ms (良好)"
    elif (( $(echo "$P95_NUM < 1000" | bc -l) )); then
        echo -e "   ${YELLOW}⚠${NC} P95 延遲: ${P95_NUM} ms (警告)"
    else
        echo -e "   ${RED}✗${NC} P95 延遲: ${P95_NUM} ms (危險)"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} 無法取得延遲數據"
fi
echo ""

# ============================================
# 4. CPU 使用率檢查
# ============================================
echo "💻 [4/8] 檢查 CPU 使用率..."
CPU_METRIC=$(curl -s http://localhost:3000/metrics 2>/dev/null | grep "^process_cpu_user_seconds_total" | tail -1)
if [ ! -z "$CPU_METRIC" ]; then
    echo -e "   ${GREEN}✓${NC} CPU Metric 可用"
    echo "   $CPU_METRIC"
else
    echo -e "   ${YELLOW}⚠${NC} 無法取得 CPU 數據"
fi
echo ""

# ============================================
# 5. 記憶體使用檢查
# ============================================
echo "💾 [5/8] 檢查記憶體使用..."
MEMORY_BYTES=$(curl -s http://localhost:3000/metrics 2>/dev/null | grep "^process_resident_memory_bytes" | awk '{print $2}')
if [ ! -z "$MEMORY_BYTES" ]; then
    MEMORY_MB=$(echo "scale=2; $MEMORY_BYTES / 1024 / 1024" | bc)
    if (( $(echo "$MEMORY_MB < 200" | bc -l) )); then
        echo -e "   ${GREEN}✓${NC} 記憶體使用: ${MEMORY_MB} MB (正常)"
    elif (( $(echo "$MEMORY_MB < 500" | bc -l) )); then
        echo -e "   ${YELLOW}⚠${NC} 記憶體使用: ${MEMORY_MB} MB (偏高)"
    else
        echo -e "   ${RED}✗${NC} 記憶體使用: ${MEMORY_MB} MB (過高)"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} 無法取得記憶體數據"
fi
echo ""

# ============================================
# 6. 資料庫連線檢查
# ============================================
echo "🗄️  [6/8] 檢查資料庫狀態..."
DB_CHECK=$(docker exec -it tixmaster-postgres psql -U postgres -c "SELECT 1;" 2>/dev/null)
if [ $? -eq 0 ]; then
    ACTIVE_CONN=$(docker exec -it tixmaster-postgres psql -U postgres -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | tr -d ' \r')
    echo -e "   ${GREEN}✓${NC} 資料庫: 已連接"
    echo "   活躍連線數: $ACTIVE_CONN"
else
    echo -e "   ${RED}✗${NC} 資料庫: 無法連接"
fi
echo ""

# ============================================
# 7. Docker 容器狀態
# ============================================
echo "🐳 [7/8] 檢查 Docker 容器..."
docker ps --filter "name=tixmaster" --format "   {{.Names}}: {{.Status}}" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} Docker 容器檢查完成"
else
    echo -e "   ${YELLOW}⚠${NC} Docker 未運行或無容器"
fi
echo ""

# ============================================
# 8. Prometheus & Grafana 狀態
# ============================================
echo "📈 [8/8] 檢查監控系統..."
PROM_STATUS=$(curl -s http://localhost:9091/-/healthy 2>/dev/null)
GRAFANA_STATUS=$(curl -s http://localhost:3001/api/health 2>/dev/null)

if [ ! -z "$PROM_STATUS" ]; then
    echo -e "   ${GREEN}✓${NC} Prometheus: 運行中 (http://localhost:9091)"
else
    echo -e "   ${RED}✗${NC} Prometheus: 無法連接"
fi

if [ ! -z "$GRAFANA_STATUS" ]; then
    echo -e "   ${GREEN}✓${NC} Grafana: 運行中 (http://localhost:3001)"
else
    echo -e "   ${RED}✗${NC} Grafana: 無法連接"
fi
echo ""

# ============================================
# 總結
# ============================================
echo "╔════════════════════════════════════════════╗"
echo "║   檢查完成                                 ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "💡 提示:"
echo "   - 綠色 ✓ = 正常"
echo "   - 黃色 ⚠ = 警告"
echo "   - 紅色 ✗ = 異常"
echo ""
echo "📖 詳細故障排除請參考: markdown_file/RUNBOOK.md"
echo ""
