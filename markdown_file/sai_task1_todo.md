# **任務 1 — 可觀測性：Logs 與 Metrics（Achieving）**

@賽冠恩

- [x] 設定一個警報：當網站掛掉（回傳 `500` 或發生 Timeout）時，自動寄 Email（已使用 Prometheus + Alertmanager 完成）。
- [ ] 設定 Grafana Alerting：處理與業務邏輯相關、需要看圖調整閾值的警報（如：訂單量異常下跌、API 回應時間變慢）。
- 寫下 SOP 的具體指令（步驟要可操作、可複製）。例如：
  1. 檢查 Log：
     - 如果在本機或 VM：`tail -n 200 backend/logs/*.log` 或 `Get-Content .\\backend\\logs\\app.log -Tail 200`（PowerShell）
     - 如果在容器或 k8s：`kubectl logs -l app=tixmaster --tail=200` 或 `docker logs --tail 200 <container>`
  2. 如果懷疑是 DB 連線問題：
     - 檢查 DB 可用性：`pg_isready -h <db_host> -p <port>` 或使用 `psql -h <db_host> -U <user> -d tixmaster -c '\\l'`
     - 檢查後端至 DB 的網路連線：`Test-NetConnection -ComputerName <db_host> -Port 5432`（PowerShell）
  3. 若需要重啟服務：
     - systemd: `sudo systemctl restart tixmaster`（若用 systemd 管理）
     - PM2: `pm2 restart server`（若用 PM2）
  4. 若警報觸發：通知流程
     - 先將主要 log 與錯誤快照截圖，上傳至共享資料夾或 Issue，並標註 on-call 人員
     - 若為 DB 連線問題，執行 DB 回復 SOP（見 DB Runbook）

- 交付物：
  - 儀表板截圖（至少包含 1. 請求率 2. 錯誤率 3. 延遲分布）
  - Alert 設定檔（Prometheus Alerting 規則或 Grafana 警報截圖）
  - SOP 文件（包含可執行指令與聯絡窗口）

---

如需我將更完整的 Alert 規則範例、Grafana 面板 JSON 或 Email 設定範本也一併加入，請告訴我要用哪種監控堆疊（Prometheus+Alertmanager 或 Grafana Alerting / Elasticsearch + Watcher 等）。
