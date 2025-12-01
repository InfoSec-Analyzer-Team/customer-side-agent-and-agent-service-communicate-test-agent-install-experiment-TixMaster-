# TixMaster 監控系統標準作業程序 (SOP)

**文件編號**:SOP-MON-001

**生效日期**: 2025-12-01

---

## 1. 目的

本文件規範 TixMaster 系統在發生異常或收到警報時的標準排查與處理流程，確保系統可用性與問題能被快速定位。

## 2. 適用範圍

本 SOP 適用於開發與測試環境的後端服務 (Node.js)、資料庫 (PostgreSQL) 及監控堆疊 (Prometheus, Grafana, Alertmanager)。

## 3. 故障排除程序

### 3.1 檢查後端 Logs

當收到錯誤警報或發現 API 回應異常時，請優先檢查後端 Logs。

**執行環境**: Windows PowerShell

* **查看即時錯誤 Log (追蹤最新 50 行)**:

    ```powershell
    Get-Content .\backend\logs\error.log -Tail 50 -Wait
    ```

* **查看所有 Log (追蹤最新 100 行)**:

    ```powershell
    Get-Content .\backend\logs\combined.log -Tail 100
    ```

* **若後端運行於 Docker 容器內**:

    ```powershell
    docker logs tixmaster-backend --tail 100
    ```

### 3.2 檢查監控服務狀態

若 Grafana 無數據或 Alertmanager 未發送警報，請檢查監控堆疊狀態。

* **確認服務存活狀態**:

    ```powershell
    docker ps
    ```

    *應包含: `tixmaster-prometheus`, `tixmaster-grafana`, `tixmaster-alertmanager`*

* **重啟監控堆疊 (若服務掛掉)**:

    ```powershell
    docker-compose -f docker-compose.monitoring.yml restart
    ```

* **檢查 Alertmanager UI**:
    瀏覽器開啟: [http://localhost:9093](http://localhost:9093)

### 3.3 資料庫連線檢查

若 Log 出現 DB 連線錯誤 (Connection Refused / Timeout)。

* **測試 DB Port 連線 (PowerShell)**:

    ```powershell
    Test-NetConnection -ComputerName localhost -Port 5432
    ```

    *預期結果: `TcpTestSucceeded : True`*

* **檢查 DB 容器狀態 (若使用 Docker)**:

    ```powershell
    docker ps | findstr postgres
    ```

### 3.4 服務重啟流程

若確認服務卡死或更新程式碼後需要重啟。

* **開發環境 (手動啟動)**:
    1. 在終端機按 `Ctrl+C` 停止服務。
    2. 重新執行:

       ```powershell
       npm run dev
       # 或
       node backend/server.js
       ```

* **PM2 管理環境**:

    ```powershell
    pm2 restart tixmaster-backend
    ```

## 4. 警報觸發處理流程 (Incident Response)

當收到 Email 警報 (如 `InstanceDown`, `HighErrorRate`, `LowOrderVolume`) 時：

1. **確認災情**:
    * 開啟 Grafana Dashboard ([http://localhost:3001](http://localhost:3001))。
    * 確認異常發生的時間區段與趨勢。

2. **蒐集證據**:
    * 截圖 Grafana 異常面板。
    * 截圖 `error.log` 中的關鍵錯誤訊息 (使用 3.1 步驟)。

3. **初步排查**:
    * **InstanceDown**: 檢查後端服務是否存活 (步驟 3.4)。
    * **HighErrorRate**: 檢查 `error.log` 具體報錯 (如 DB 連線失敗、程式碼 Bug)。
    * **LowOrderVolume**: 確認是否為離峰時間或行銷活動結束，若非預期則檢查下單 API。

4. **通報與紀錄**:
    * 將截圖與 Log 上傳至 Issue Tracking System。
    * 標註相關開發人員。

---
