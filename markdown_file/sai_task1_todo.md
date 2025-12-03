# **任務 1 — 可觀測性：Logs 與 Metrics（Achieving）**

@賽冠恩

- [x] 設定一個警報：當網站掛掉（回傳 `500` 或發生 Timeout）時，自動寄 Email（已使用 Prometheus + Alertmanager 完成）。
- [x] 設定 Grafana Alerting：處理與業務邏輯相關、需要看圖調整閾值的警報（如：訂單量異常下跌、API 回應時間變慢）。
- [x] 寫下 SOP 的具體指令（步驟要可操作、可複製）：
  - 已建立獨立 SOP 文件，請參閱：[MONITORING_SOP.md](./MONITORING_SOP.md)

- 交付物：
  - 儀表板截圖（至少包含 1. 請求率 2. 錯誤率 3. 延遲分布）
  - Alert 設定檔（Prometheus Alerting 規則或 Grafana 警報截圖）
  - SOP 文件（包含可執行指令與聯絡窗口）

# **任務 OPS-01 (Task 1): 設定外部監控 (Uptime Monitoring)**

- [ ] 設定外部監控服務
  - 工具推薦：Better Stack (Uptime) 或 UptimeRobot。
  - 目標：確保從外部網路可存取服務。
  - **操作指南**：請參閱 [OPS_01_UPTIME_MONITORING_GUIDE.md](./OPS_01_UPTIME_MONITORING_GUIDE.md)
- [ ] 產出：
  - 提供一張「綠色健康狀態條」的截圖。

# **任務 OPS-03 (Task 2): 繪製服務地圖 (Service Map)**

- [x] 繪製系統架構圖 (System Architecture Diagram)
  - 已完成架構圖繪製與故障點分析，請參閱：[OPS_03_SERVICE_MAP.md](./OPS_03_SERVICE_MAP.md)
- [x] 內容要求：
  - 顯示流量流向：User -> Load Balancer -> Web Server -> Database。
  - 用 **紅色** 標示潛在的「故障點」(Failure Points)。

---

如需我將更完整的 Alert 規則範例、Grafana 面板 JSON 或 Email 設定範本也一併加入，請告訴我要用哪種監控堆疊（Prometheus+Alertmanager 或 Grafana Alerting / Elasticsearch + Watcher 等）。
