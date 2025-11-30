# **任務 1 — 可觀測性：Logs 與 Metrics（Achieving）**

學生需完成：

- 確保應用與環境能產生 **日誌（logs）**、**指標（metrics）**，及可選的 **追蹤（traces）**。
- 整合任一收集方式，例如：
    - **終端機式檢視工具：** kubectl logs、docker logs、自製 CLI
    - **圖形化儀表板：** Grafana、Kibana、Prometheus UI、Elastic APM、自訂 Dashboard

需提供以下截圖：

- 日誌內容（log entries）
- 指標（CPU、記憶體、延遲、請求率、錯誤率等）

並需解釋可觀測性的設定如何提升系統可靠性。


## **2. 開發者（Developer）**

專注於程式儀表化、logging 與可復原性。

需完成：

- 實作應用日誌（建議採用 structured logs）與明確的 severity levels。
- 實作指標（Prometheus counters/gauges/histograms 或自訂 metrics）。
- 建立簡易儀表板或終端介面來顯示 logs/metrics。
- 加入警報或閾值（即使為模擬亦可）。
- 撰寫符合 SLI/SLO/SLA 的開發策略文件。
- 說明程式中關於 logging 格式、correlation IDs、錯誤處理策略的設計選擇。

--- 

@昱辰
修改後端程式碼，確保 Log。要包含 Level (Info/Error), Timestamp, UserID。JSON 格式
寫一支 API /api/crash，一呼叫這支 API，伺服器就要故意當機
規劃一下 Grafana 或監控畫面的排版，讓它看起來直觀、漂亮

---

## 📋 任務 1 執行清單

### Phase 1: 後端日誌系統建置
- [x] 安裝 logging 套件（winston 或 pino）
- [x] 設定結構化日誌格式（JSON）
  - [x] Level (Info/Error/Warning)
  - [x] Timestamp
  - [x] UserID（如有登入）
  - [x] Request ID
- [x] 修改所有 API 端點加入日誌
- [ ] 測試日誌輸出是否正確

### Phase 2: Crash API 實作
- [x] 建立 `/api/crash` 端點
- [x] 實作伺服器當機邏輯
- [x] 測試 API 是否能正確觸發當機
![alt text](image-1.png)
![alt text](<螢幕擷取畫面 2025-11-30 041811.png>)
### Phase 3: Metrics 收集
- [x] 安裝 Prometheus client 套件
- [x] 建立 `/metrics` 端點
- [x] 實作以下 metrics:
  - [x] HTTP 請求總數（counter）
  - [x] HTTP 請求延遲（histogram）
  - [x] 活躍請求數（gauge）
  - [x] 錯誤率（counter）
---
test API requests to generate metrics

![alt text](image-2.png)

Check HTTP metrics after requests

![alt text](image-3.png)

HTTP 請求總數：
/metrics - 200 狀態碼
/health - 200 狀態碼
/api/events/ - 200 狀態碼
/api/users/:id - 404 狀態碼（注意 ID 999 被自動轉換為 :id）


### Phase 4: 監控系統設定
- [x] 安裝 Prometheus
- [x] 設定 Prometheus scrape targets
- [x] 安裝 Grafana
- [x] 建立 Grafana dashboard
  - [x] CPU 使用率
  - [x] 記憶體使用率
  - [x] HTTP 請求率
  - [x] 回應時間
  - [x] 錯誤率

### Phase 5: 儀表板設計
- [x] 規劃 Grafana 儀表板排版
- [x] 設計視覺化圖表
- [x] 調整顏色與主題
- [x] 確保直觀易讀

**完成內容**:
- ✅ 建立完整的 Grafana Dashboard JSON (`grafana/dashboards/tixmaster-overview.json`)
- ✅ 8 個精心設計的 Panel:
  - CPU 使用率 & 記憶體使用量 (Gauge)
  - HTTP 請求率 (Time Series)
  - HTTP 回應時間 P50/P95 (Time Series)
  - HTTP 錯誤率 4xx/5xx (Stacked Area)
  - 活躍請求數 & 總請求數 (Gauge & Stat)
  - HTTP 狀態碼分佈 (Pie Chart)
- ✅ 顏色語意學設計 (綠/黃/紅 閾值)
- ✅ 深色主題配置
- ✅ 自動刷新 (5 秒)
- ✅ 完整設定指南文件 (`MONITORING_SETUP_GUIDE.md`)

### Phase 6: 系統架構圖 這裡跳過 給DBA做 
- [ ] 繪製系統架構圖
  - [ ] Frontend → Backend
  - [ ] Backend → Database
  - [ ] 監控系統連線
- [ ] 標示可能斷線的點

### Phase 7: 警報設定 這裡跳過 給DBA做
- [ ] 設定 Alertmanager
- [ ] 建立警報規則（5xx 錯誤、Timeout）
- [ ] 設定 Email 通知
- [ ] 測試警報觸發

### Phase 8: SLI/SLO/SLA 文件
- [x] 定義 SLI（可用性、延遲、錯誤率）
- [x] 定義 SLO（目標值）
- [x] 撰寫開發策略文件
  - [x] Logging 格式說明
  - [x] Correlation ID 使用
  - [x] 錯誤處理策略

**完成內容**:
- ✅ **SLI/SLO/SLA 完整文件** (`SLI_SLO_SLA_DOCUMENT.md`)
  - 5 個核心 SLI 定義 (可用性、延遲、流量、錯誤率、飽和度)
  - 詳細 SLO 目標設定 (99.5% 可用性, P95 < 500ms)
  - SLA 承諾與賠償方案
  - 錯誤預算 (Error Budget) 管理
  - 警報分級策略 (P0-P3)
- ✅ **開發策略文件** (`DEVELOPMENT_STRATEGY.md`)
  - JSON 結構化日誌格式
  - Log Level 使用指南
  - Correlation ID 完整實作說明
  - 錯誤處理最佳實踐
  - 重試策略與 Circuit Breaker

### Phase 9: RUNBOOK 撰寫
- [x] 撰寫故障排除手冊
  - [x] 5xx 錯誤處理
  - [x] Timeout 處理
  - [x] DB 連線失敗處理
- [x] 撰寫 SOP 具體指令

**完成內容**:
- ✅ **完整 RUNBOOK 手冊** (`RUNBOOK.md`)
  - 🚨 5xx 伺服器錯誤完整處理流程（診斷、修復、預防）
  - ⏱️ Timeout 超時問題排查指南（慢查詢、N+1、外部 API）
  - 💾 資料庫連線失敗處理（連線池、備份、恢復）
  - 🔥 服務完全宕機緊急處理（2 分鐘檢查清單）
  - 📊 高負載與效能問題優化
  - 📞 升級路徑與事後檢討模板
- ✅ **快速診斷腳本**
  - `quick_check.sh` (Linux/Mac)
  - `quick_check.bat` (Windows)
  - 8 項系統健康檢查（服務、錯誤率、延遲、CPU、記憶體、資料庫、Docker、監控）
  - 彩色輸出與狀態指示

### Phase 10: 測試與截圖
- [ ] 截圖：日誌內容（JSON 格式）
- [ ] 截圖：Grafana 儀表板
- [ ] 截圖：Prometheus metrics
- [ ] 截圖：警報通知
- [ ] 測試 DDOS 攻擊情境
- [ ] 使用 RUNBOOK 實際操作

### Phase 11: 文件整理
- [ ] 整理所有截圖
- [ ] 完成系統架構圖
- [ ] 完成 SLI/SLO/SLA 文件
- [ ] 完成 RUNBOOK
- [ ] 撰寫可觀測性提升系統可靠性的說明

### Phase 12: 最終驗收
- [ ] 完整測試所有功能
- [ ] 準備 Demo
- [ ] 提交報告
