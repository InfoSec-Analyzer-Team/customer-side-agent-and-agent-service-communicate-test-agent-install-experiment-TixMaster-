# OPS-01 外部監控設定指南 (Uptime Monitoring)

本指南協助您完成「設定外部監控服務」任務，確保 TixMaster 服務可從外部網路存取。

## 1. 前置確認：服務公開性

外部監控服務 (如 UptimeRobot, Better Stack) 必須能透過網際網路存取您的應用程式。

### 情況 A：您已有部署的公開網址 (Staging/Production)

* 直接使用該網址 (例如：`https://api.tixmaster.com` 或 `http://<Public-IP>:3000`)。

### 情況 B：您目前在本地端 (Localhost) 開發

* 外部服務無法直接存取 `localhost`。
* **解決方案**：使用 Tunnel 工具 (如 **ngrok**) 將本地服務暫時公開。

#### 使用 ngrok 公開本地服務 (範例)

1. 下載並安裝 [ngrok](https://ngrok.com/download)。
2. 開啟終端機 (PowerShell)，執行以下指令 (假設後端跑在 Port 3000)：

    ```powershell
    ngrok http 3000
    ```

3. 複製畫面上的 `Forwarding` 網址 (例如 `https://xxxx-xxxx.ngrok-free.app`)。這就是您的**外部監控網址**。

---

## 2. 設定 UptimeRobot (推薦)

UptimeRobot 提供免費且簡單的 HTTP 監控。

1. 前往 [UptimeRobot](https://uptimerobot.com/) 並註冊/登入。
2. 點擊儀表板左上角的 **+ Add New Monitor**。
3. 填寫設定：
    * **Monitor Type**: 選擇 `HTTP(s)`。
    * **Friendly Name**: 輸入 `TixMaster Backend`。
    * **URL (or IP)**: 貼上您的公開網址 (或 ngrok 網址)。
    * **Monitoring Interval**: 建議設為 `5 min` (免費版最低)。
    * **Alert Contacts**: 勾選您的 Email 以接收通知。
4. 點擊 **Create Monitor**。

---

## 3. 設定 Better Stack (替代方案)

介面較現代化，同樣提供免費方案。

1. 前往 [Better Stack](https://betterstack.com/uptime) 註冊。
2. 進入 **Monitors** -> **Create monitor**。
3. **URL to monitor**: 貼上您的公開網址。
4. **Alerting**: 設定 Email 通知。
5. 儲存設定。

---

## 4. 驗證與產出

1. 等待約 5-10 分鐘，讓服務進行第一次檢查。
2. 確認儀表板上的狀態條呈現 **綠色 (Up / Operational)**。
3. **截圖**該畫面 (需包含服務名稱與綠色狀態條)。
4. 將截圖存檔，並更新至任務回報區。

> **注意**：若使用 ngrok 免費版，網址會在重啟 ngrok 後改變，監控將會失效 (變紅)。此方法僅適合短期驗證任務使用。
