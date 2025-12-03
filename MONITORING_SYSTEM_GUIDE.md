# 🚨 TixMaster 監控警報系統手冊

本文件說明 TixMaster 的完整監控警報系統架構、設定方式與維運指南。本系統結合了 **Prometheus + Alertmanager** (基礎設施監控) 與 **Grafana Alerting** (業務邏輯監控)，確保系統穩定性與業務運作正常。

## 📋 系統架構

| 元件 | 角色 | 監控目標 | 警報通知方式 |
| :--- | :--- | :--- | :--- |
| **Prometheus** | 核心監控與警報引擎 | 基礎設施 (CPU/Mem)、服務存活 (Up/Down)、錯誤率 (5xx) | 透過 Alertmanager 發送 Email |
| **Alertmanager** | 警報路由與管理 | 接收 Prometheus 的警報，進行分組、抑制與發送 | Email (Gmail SMTP) |
| **Grafana** | 視覺化與業務警報 | 業務指標 (訂單量)、趨勢分析 (API 變慢)、儀表板 | Email (Grafana SMTP) |

---

## 🛠️ 快速啟動

### 1. 設定 Email 認證

為了安全起見，SMTP 認證資訊儲存在 `.env` 檔案中。

1. 在 `alertmanager` 資料夾中建立 `.env` 檔案 (`alertmanager/.env`)：
   ```env
   SMTP_EMAIL=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```
   > *注意：Gmail 請使用「應用程式密碼」(App Password)，而非登入密碼。*

2. 產生 Alertmanager 設定檔：
   ```powershell
   .\generate_alert_config.ps1
   ```

### 2. 啟動服務

使用 Docker Compose 啟動所有監控服務：

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

服務存取位置：
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3001 (帳號/密碼: admin/admin)
- **Alertmanager**: http://localhost:9093

---

## ⚠️ 警報規則清單

### 1. 基礎設施警報 (Prometheus + Alertmanager)

這些規則定義在 `prometheus_rules.yml`，主要關注系統是否「活著」。

| 警報名稱 | 觸發條件 | 說明 | 嚴重性 |
| :--- | :--- | :--- | :--- |
| **InstanceDown** | `up == 0` (持續 1m) | Backend 服務無法連線 | Critical |
| **HighErrorRate** | `status_code=5xx` > 0 (持續 1m) | 發生任何 500 伺服器錯誤 | Critical |
| **HighLatency** | P95 延遲 > 5秒 (持續 1m) | 系統回應極慢 (嚴重卡頓) | Warning |

### 2. 業務邏輯警報 (Grafana Alerting)

這些規則定義在 `grafana/provisioning/alerting/tixmaster_alerts.yaml`，關注業務運作是否正常。

| 警報名稱 | 觸發條件 | 說明 | 嚴重性 |
| :--- | :--- | :--- | :--- |
| **Low Order Volume** | 訂單量 < 0.01/s (持續 5m) | 長時間沒有新訂單 (可能結帳壞了) | Critical |
| **API Slow Response** | P95 延遲 > 2秒 (持續 2m) | API 回應變慢 (效能退化) | Warning |

---

## 🧪 測試與驗證 SOP

### 測試 1: 模擬網站掛掉 (Instance Down)
1. 停止 Backend 容器：`docker stop tixmaster-backend`
2. 等待 1-2 分鐘。
3. 檢查 Email 是否收到 **[FIRING:1] InstanceDown** 通知。

### 測試 2: 模擬高錯誤率 (High Error Rate)
1. 呼叫 Crash API (會導致 400 錯誤)：
   ```bash
   curl -X POST http://localhost:3000/api/crash
   ```
2. 連續執行數次，直到 Prometheus 觸發警報。

### 測試 3: 模擬 API 變慢 (Slow Response)
1. 呼叫 Slow API (預設延遲 6 秒)：
   ```bash
   # 建議開啟多個終端機或瀏覽器分頁同時執行
   curl http://localhost:3000/api/slow
   ```
2. 觀察 Grafana 儀表板，確認 P95 延遲上升。
3. 等待 2 分鐘，檢查是否收到 Grafana 的 **API Slow Response** 通知。

---

## 🔍 故障排除

- **Grafana 警報顯示 "Provisioned" 無法編輯**：
  這是正常的。為了確保設定一致性，我們使用檔案 (`tixmaster_alerts.yaml`) 來管理警報規則。若要修改規則，請編輯該 YAML 檔案並重啟 Grafana。

- **收不到 Email**：
  - 檢查 `alertmanager/.env` (Prometheus 警報) 與 `docker-compose.monitoring.yml` (Grafana 警報) 中的 SMTP 設定。
  - 確認 Google 帳號已開啟兩步驟驗證並使用應用程式密碼。
  - 查看 Logs：
    - Alertmanager: `docker logs tixmaster-alertmanager`
    - Grafana: `docker logs tixmaster-grafana`
