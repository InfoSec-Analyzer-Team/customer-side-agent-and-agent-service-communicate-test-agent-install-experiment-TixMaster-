# 故障注入伺服器

`fault_injection_server.js` 是一個獨立的 Node.js 伺服器，用於模擬各種故障場景以進行測試和監控。此伺服器提供注入故障的端點，例如高延遲、超時、依賴失敗和資源尖峰。這是一個驗證應用程式韌性和穩健性的寶貴工具。

## 先決條件

- 系統已安裝 Node.js。
- 確保已安裝所需的依賴項，執行以下命令：
  ```bash
  npm install
  ```

## 啟動伺服器

要啟動故障注入伺服器，請使用以下命令：
```bash
node backend/scripts/fault_injection_server.js
```

或者，您可以使用 `package.json` 中定義的 npm 腳本：
```bash
npm run fault:server
```

伺服器預設會啟動在 `http://localhost:3999`。

## 環境變數

可以使用以下環境變數來控制故障注入伺服器的行為：

- `FAULT_SERVER_PORT`：伺服器運行的埠號（預設：`3999`）。
- `ENABLE_FAULT_INJECTION`：設置為 `true` 以啟用故障注入端點（預設：`false`）。

## 可用端點（基礎）

### 1. 高延遲
- **端點**：`/api/fault/latency`
- **方法**：`GET`
- **查詢參數**：
  - `durationMs`：延遲的持續時間（毫秒）。
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/latency?durationMs=3000"
  ```

### 2. 超時
- **端點**：`/api/fault/timeout`
- **方法**：`GET`
- **查詢參數**：
  - `durationMs`：超時的持續時間（毫秒）。
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/timeout?durationMs=5000"
  ```

### 3. 依賴失敗
- **端點**：`/api/fault/dependency`
- **方法**：`GET`
- **查詢參數**：
  - `type`：要模擬失敗的依賴類型（例如：`db`、`http`）。
  - `mode`：失敗模式（例如：`simulate`）。
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/dependency?type=db&mode=simulate"
  ```

### 4. 隨機錯誤（等同 random）
- **端點**：`/api/fault/random`
- **方法**：`GET`
- **查詢參數**：
  - `errorRate`：0~1 間的失敗機率（預設 0.3）。
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/random?errorRate=0.3"
  ```

### 5. CPU 尖峰
- **端點**：`/api/fault/cpu-spike`
- **方法**：`GET`
- **查詢參數**：
  - `durationMs`：CPU 尖峰的持續時間（毫秒）。
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/cpu-spike?durationMs=5000"
  ```

### 6. 記憶體壓力
- **端點**：`/api/fault/memory-pressure`
- **方法**：`GET`
- **查詢參數**：
  - `sizeMb`：要分配的記憶體大小（MB）。
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/memory-pressure?sizeMb=100"
  ```

### 7. HTTP 依賴失敗
- **端點**：`/api/fault/http-dependency`
- **方法**：`GET`
- **查詢參數**：
  - `url`：要模擬失敗的 HTTP 依賴 URL。
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/http-dependency?url=http://example.com"
  ```

### 8. DNS 故障
- **端點**：`/api/fault/dns-failure`
- **方法**：`GET`
- **查詢參數**：
  - `hostname`：要模擬 DNS 故障的主機名稱。
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/dns-failure?hostname=example.com"
  ```

## 注意事項

- 確保將 `ENABLE_FAULT_INJECTION` 環境變數設置為 `true` 才能使用這些端點。
- 請在受控的測試環境中負責任地使用這些端點。

## 貢獻

如果您希望為故障注入伺服器做出貢獻，請遵循主 `README.md` 文件中的指南。

## 授權

此專案採用 MIT 許可證授權。詳見 `LICENSE` 文件。

---

## 進階端點

以下端點用於更進一步的網路/資源/錯誤情境模擬，請務必在測試環境使用。

### A. Crash（強制終止進程）
- **端點**：`/api/fault/crash`
- **方法**：`GET`
- **查詢參數**：
  - `code`：結束代碼（0~255，預設 1）
  - `confirm`：必須為 `YES` 才會執行
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/crash?code=1&confirm=YES"
  ```

### B. 延遲抖動（jitter）
- **端點**：`/api/fault/delay-jitter`
- **方法**：`GET`
- **查詢參數**：
  - `meanMs`：平均延遲毫秒（預設 1000）
  - `jitterMs`：最大抖動毫秒（預設 500）
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/delay-jitter?meanMs=1000&jitterMs=500"
  ```

### C. 部分回應（partial-response）
- **端點**：`/api/fault/partial-response`
- **方法**：`GET`
- **查詢參數**：
  - `bytes`：要先寫出的位元組數（預設 256，上限 10MB）
  - `delayMs`：開始寫出前延遲（預設 0）
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/partial-response?bytes=512&delayMs=100"
  ```

### D. 連線中斷（dropped-connection）
- **端點**：`/api/fault/dropped-connection`
- **方法**：`GET`
- **查詢參數**：
  - `delayMs`：中斷前延遲毫秒（預設 0）
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/dropped-connection?delayMs=500"
  ```

### E. 流量限制（rate-limit）
- **端點**：`/api/fault/rate-limit`
- **方法**：`GET`
- **查詢參數**：
  - `limit`：期間內允許次數（預設 10）
  - `periodSec`：期間秒數（預設 60）
  - `status`：超限回應狀態碼（預設 429）
- **回應標頭**：`X-RateLimit-Limit`、`X-RateLimit-Remaining`、`X-RateLimit-Reset`
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/rate-limit?limit=5&periodSec=30&status=429"
  ```

### F. 記憶體洩漏（memory-leak）
- **端點**：`/api/fault/memory-leak`
- **方法**：`GET`
- **查詢參數**：
  - `mode`：`start` | `stop` | `status`
  - `stepMb`：每次增量（MB，start 用，預設 5）
  - `intervalMs`：分配間隔（毫秒，start 用，預設 1000）
- **範例**：
  ```bash
  # 開始
  curl "http://localhost:3999/api/fault/memory-leak?mode=start&stepMb=5&intervalMs=1000"
  # 查詢
  curl "http://localhost:3999/api/fault/memory-leak?mode=status"
  # 停止
  curl "http://localhost:3999/api/fault/memory-leak?mode=stop"
  ```

### G. 磁碟 I/O 壓力（disk-io）
- **端點**：`/api/fault/disk-io`
- **方法**：`GET`
- **查詢參數**：
  - `sizeMb`：寫入暫存檔案的大小（MB，預設 50，上限 1024）
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/disk-io?sizeMb=100"
  ```

### H. 日誌大量輸出（log-spam）
- **端點**：`/api/fault/log-spam`
- **方法**：`GET`
- **查詢參數**：
  - `lines`：要輸出的行數（預設 1000）
  - `intervalMs`：每行間隔（毫秒，預設 5）
  - `level`：`error` | `warn` | `info` | `debug`（預設 info）
- **範例**：
  ```bash
  curl "http://localhost:3999/api/fault/log-spam?lines=200&intervalMs=10&level=warn"
  ```

## 啟動與守門

- 啟用守門：需設定 `ENABLE_FAULT_ENDPOINTS=true`，否則所有端點回 403。
- 變更埠號：可用 `FAULT_PORT` 覆寫（預設 3999）。

## 快速測試（PowerShell 範例）

```powershell
$env:ENABLE_FAULT_ENDPOINTS='true'; $env:FAULT_PORT='3999'; npm run fault:server
# 另開一個視窗後測試
curl "http://localhost:3999/health"
curl "http://localhost:3999/api/fault/delay-jitter?meanMs=800&jitterMs=200"
curl "http://localhost:3999/api/fault/rate-limit?limit=2&periodSec=10";
```
# 故障注入伺服器

`fault_injection_server.js` 是一個獨立的 Node.js 伺服器，用於模擬各種故障場景以進行測試和監控。此伺服器提供注入故障的端點，例如高延遲、超時、依賴失敗和資源尖峰。這是一個驗證應用程式韌性和穩健性的寶貴工具。

---

## 🚀 伺服器 (`fault_injection_server.js`) 說明

### 目的
提供一個簡易的 HTTP 介面，讓開發者或測試人員可以觸發應用程式中的各種錯誤、延遲和資源壓力狀況，以測試應用程式的容錯能力。

### 先決條件
- 系統已安裝 Node.js。
- 確保已安裝所需的依賴項，執行以下命令：
  ```bash
  npm install