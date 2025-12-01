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

---

如需我將更完整的 Alert 規則範例、Grafana 面板 JSON 或 Email 設定範本也一併加入，請告訴我要用哪種監控堆疊（Prometheus+Alertmanager 或 Grafana Alerting / Elasticsearch + Watcher 等）。
