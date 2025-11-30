# 🚨 監控警報系統設定指南 (Prometheus + Alertmanager)

本指南說明如何設定與測試 TixMaster 的監控警報系統。當系統發生異常（如網站掛掉、高錯誤率、高延遲）時，系統會自動發送 Email 通知。

## 📋 架構概觀

- **Prometheus**: 負責收集 Metrics 並評估警報規則 (`prometheus_rules.yml`)。
- **Alertmanager**: 負責接收 Prometheus 的警報，進行分組、抑制，並發送通知（如 Email）。
- **Grafana**: 用於視覺化 Metrics（本指南主要關注警報部分）。

## 🛠️ 設定步驟

### 1. 設定 Email 通知 (使用 .env)

為了安全起見，我們將 Email 和密碼設定在 `.env` 檔案中，而不是直接寫在設定檔裡。

1. **編輯 `.env` 檔案**：
   在 `alertmanager` 資料夾中建立或編輯 `.env` 檔案 (`alertmanager/.env`)，填入您的 Gmail 資訊：

   ```env
   SMTP_EMAIL=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

   > **💡 如何取得 Google 應用程式密碼？**
   > 1. 前往 [Google 帳戶安全性](https://myaccount.google.com/security)。
   > 2. 確保已開啟 **「兩步驟驗證」**。
   > 3. 在搜尋欄搜尋 **「應用程式密碼」** (App passwords)。
   > 4. 建立新密碼：應用程式選「郵件」，裝置選「其他 (自訂名稱)」，輸入 `TixMaster`。
   > 5. 複製產生的 16 位數密碼（移除空格），填入上方的 `smtp_auth_password`。

2. **產生設定檔**：
   執行以下 PowerShell 指令，它會讀取 `.env` 並產生 `alertmanager/config.yml`：

   ```powershell
   .\generate_alert_config.ps1
   ```

### 2. 啟動監控系統

使用 Docker Compose 啟動所有服務：

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

這將會啟動：
- Prometheus (http://localhost:9091)
- Grafana (http://localhost:3001)
- Alertmanager (http://localhost:9093)

## ⚠️ 警報規則

目前的警報規則定義在 `prometheus_rules.yml`：

1. **InstanceDown**: 當 Backend 無法連線 (`up == 0`) 超過 1 分鐘。
2. **HighErrorRate**: 當 4xx 錯誤率 (`status_code=4xx`) 超過 0 (即發生任何 500 錯誤) 持續 1 分鐘。
3. **HighLatency**: 當 95% 的請求回應時間超過 5 秒持續 1 分鐘。

## 🧪 測試警報

### 測試 1: 網站掛掉 (Instance Down)

1. 停止 Backend 服務：
   ```bash
   # 如果 Backend 是用 Docker 跑的
   docker stop tixmaster-backend
   
   # 如果是在本機跑的，直接 Ctrl+C 停止它
   ```
2. 等待約 1-2 分鐘。
3. 檢查 Prometheus Alerts 頁面 (http://localhost:9091/alerts)，應該會看到 `InstanceDown` 變為 `FIRING`。
4. 檢查 Alertmanager (http://localhost:9093)，應該會看到警報。
5. 檢查您的 Email 信箱。

### 測試 2: 高錯誤率 (High Error Rate)

Backend 提供了一個測試用的 Crash API。

1. 確保 Backend 正在執行。
2. 呼叫 Crash API (這會導致 Backend 回傳錯誤並重啟/停止)：
   ```bash
   curl -X POST http://localhost:3000/api/crash
   ```
   或者，如果您無法輕易讓伺服器掛掉，可以手動修改程式碼拋出 500 錯誤，然後連續發送請求。
   
   *注意：由於 `rate()` 函數的特性，您可能需要持續產生錯誤幾次才能觸發警報。*

### 測試 3: 高延遲 (High Latency)

Backend 提供了一個測試用的 Slow API。

1. 呼叫 Slow API (預設延遲 6 秒，超過警報閾值 5 秒)：
   ```bash
   # 在瀏覽器打開或使用 curl
   curl http://localhost:3000/api/slow
   ```
2. 由於 Prometheus 的警報規則是檢查「過去一段時間的 95% 請求延遲」，您可能需要**連續呼叫多次**（例如連續重新整理網頁或執行多次 curl），讓整體平均延遲拉高。
3. 等待約 1-2 分鐘，檢查 Prometheus Alerts 頁面，`HighLatency` 應變為 `FIRING`。

## 🔍 故障排除

- **收不到 Email**:
  - 檢查 `alertmanager/config.yml` 的 SMTP 設定是否正確。
  - 如果使用 Gmail，確保已啟用 2-Step Verification 並使用 App Password。
  - 查看 Alertmanager logs: `docker logs tixmaster-alertmanager`。

- **Prometheus 抓不到 Metrics**:
  - 檢查 Backend 是否正在執行。
  - 檢查 http://localhost:3000/metrics 是否能存取。
  - 查看 Prometheus targets: http://localhost:9091/targets。
