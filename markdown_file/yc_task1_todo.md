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
畫一張系統架構圖，標示出 Frontend -> Backend -> Database 的連線，以及哪裡可能會斷線
規劃一下 Grafana 或監控畫面的排版，讓它看起來直觀、漂亮
@賽冠恩 
設定監控儀表板
 設定一個警報：當網站掛掉 (回傳 500 或 Timeout) 時，自動寄 Email
寫下 SOP的具體指令。例如：1. 檢查 Log, 2. 如果是 DB 連不上
@許升
對網站使用DDOS
使用RUNBOOK實際操作