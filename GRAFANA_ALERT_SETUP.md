# 📊 Grafana 業務警報設定指南

本指南說明如何在 Grafana 中設定與業務邏輯相關的警報，例如「訂單量異常下跌」或「API 回應變慢」。這些警報通常需要透過圖表觀察趨勢來調整閾值 (Threshold)。

## 📋 前置準備

1. **重啟 Backend**：
   我們剛剛新增了 `orders_total` 這個 Metric，請務必重啟 Backend 讓它生效。
   ```bash
   # Docker
   docker restart tixmaster-backend
   
   # 本機
   # Ctrl+C 停止後重新執行 node server.js
   ```

2. **確認 Grafana 運作中**：
   前往 http://localhost:3001 (帳號/密碼預設為 admin/admin)。

## 🚨 設定警報 1：訂單量異常下跌 (Low Order Volume)

這個警報用於偵測系統是否長時間沒有新訂單，可能是因為結帳流程壞了，但系統沒有報錯。

### 步驟 1: 建立 Alert Rule
1. 在 Grafana 左側選單點擊 **Alerting** > **Alert rules**。
2. 點擊 **New alert rule**。
3. **設定查詢 (Define query)**:
   - Data source 選擇 **Prometheus**。
   - Query A 輸入：`rate(orders_total[5m])`
     - *這代表過去 5 分鐘的平均每秒訂單數。*
   - 點擊 **Run queries** 查看目前的數值。

### 步驟 2: 設定條件 (Define condition)
1. Condition 選擇 **Query A**。
2. 設定閾值：
   - **IS BELOW** (低於)
   - **0.01** (範例值，代表每 100 秒不到 1 張單)
   - *注意：這個值需要根據您的實際業務量調整。如果是熱門演唱會開賣，這個值應該設很高；如果是半夜，可能要設很低或忽略。*

### 步驟 3: 設定評估行為 (Set evaluation behavior)
1. **Evaluate every**: `1m` (每分鐘檢查一次)
2. **For**: `5m` (持續 5 分鐘都低於閾值才發警報)
   - *這可以避免因為剛好沒人買票就誤報。*

### 步驟 4: 設定通知 (Configure labels and notifications)
1. **Alert name**: `LowOrderVolume`
2. **Summary**: 訂單量異常低
3. **Description**: 過去 5 分鐘內訂單量低於預期，請檢查結帳流程。
4. 點擊 **Save rule and exit**。

---

## 🐢 設定警報 2：API 回應變慢 (Slow API Response)

這個警報比 Prometheus 的 `HighLatency` 更靈活，您可以看著圖表拉出一條「不可接受」的線。

### 步驟 1: 建立 Alert Rule
1. 點擊 **New alert rule**。
2. **設定查詢**:
   - Data source 選擇 **Prometheus**。
   - Query A 輸入：`histogram_quantile(0.95, rate(http_request_duration_ms_bucket[5m]))`
     - *這代表過去 5 分鐘內，95% 的請求回應時間 (P95 Latency)。*

### 步驟 2: 設定條件
1. Condition 選擇 **Query A**。
2. 設定閾值：
   - **IS ABOVE** (高於)
   - **2000** (2000ms = 2秒)
   - *您可以直接在預覽圖表上拖拉這條紅線，找到適合的閾值。*

### 步驟 3: 設定評估行為
1. **Evaluate every**: `1m`
2. **For**: `2m` (持續 2 分鐘都慢才發警報)

### 步驟 4: 設定通知
1. **Alert name**: `APISlowResponse`
2. **Summary**: API 回應速度變慢
3. **Description**: P95 延遲超過 2 秒。
4. 點擊 **Save rule and exit**。

## 📧 設定 Grafana 通知管道 (Contact Points)

Grafana 預設不會寄信，您需要設定 Contact Point。

1. 左側選單 **Alerting** > **Contact points**。
2. 點擊 **Add contact point**。
3. **Name**: `Email`
4. **Integration**: `Email`
5. **Addresses**: 輸入您的 Email。
6. 點擊 **Test** 測試寄信 (需先在 `grafana.ini` 或 Docker env 設定 SMTP，見下文)。
7. 儲存後，去 **Notification policies** 將 Default policy 指向這個 Contact point。

### 💡 補充：Grafana SMTP 設定 (Docker Compose)
若要讓 Grafana 寄信，請修改 `docker-compose.monitoring.yml` 的 grafana 區塊，加入環境變數：

```yaml
    environment:
      - GF_SMTP_ENABLED=true
      - GF_SMTP_HOST=smtp.gmail.com:587
      - GF_SMTP_USER=your-email@gmail.com
      - GF_SMTP_PASSWORD=your-app-password
      - GF_SMTP_FROM_ADDRESS=your-email@gmail.com
```
