# Feature Engineering Spec

## IP

| Feature | Description |
|---|---|
| `ip_type` | `public` / `private_class_a` (10.x) / `private_class_b` (172.16–31.x) / `private_class_c` (192.168.x) / `loopback` (127.x) / `invalid` / `unknown` (缺失) |
| `ip_first_octet` | IP 第一個 octet 數值 (0–255)，缺失填 0 |

---

## Datetime String

| Feature | Description |
|---|---|
| `datetime_parsed` | 解析後的時間物件 (`errors='coerce'`) |
| `hour` | 小時 (0–23)，缺失填 0 |
| `day_of_week` | 星期幾 (0 = 週一，6 = 週日)，缺失填 0 |
| `is_weekend` | 是否週末 (0/1)，`day_of_week >= 5` |
| `is_odd_hour` | 是否異常時段 (0/1)，凌晨 1–6am |
| `time_period` | 時段分類：`night` (0–6am) = 0 / `morning` (6–12) = 1 / `afternoon` (12–18) = 2 / `evening` (18–0) = 3 |

---

## Request

| Feature | Description |
|---|---|
| `request_method` | HTTP 方法 (GET, POST, PUT, DELETE, ...)，regex 提取第一個單字 |
| `request_version` | HTTP 版本 (HTTP/1.0, HTTP/1.1, HTTP/2.0)，regex 提取行尾 |
| `url` | 從 request 提取的 URL 路徑（方法與版本之間） |

---

## URL

| Feature | Description |
|---|---|
| `url_length` | URL 字元長度，缺失填 0 |
| `url_depth` | 路徑深度，計算 `/` 數量，缺失填 0 |
| `url_param_count` | 參數數量，計算 `?` 和 `&` 數量，缺失填 0 |
| `url_special_chars` | 特殊字元數量 `< > ' " ; % ( ) [ ] { }`，缺失填 0 |
| `has_sql_injection` | SQL Injection 模式 (0/1)：`union select` / `select from` / `insert into` / `drop table` / OR 注入 / `1=1` / 時間盲注 / SQL 註解 |
| `has_xss` | XSS 模式 (0/1)：`<script` / `javascript:` / `onerror=` / `onload=` / `alert(` / `document.cookie` / `<iframe` / `<img onerror` |
| `has_path_traversal` | 路徑遍歷攻擊 (0/1)：`../` 或 `..\` 或 `%2e%2e` |
| `has_command_injection` | 命令注入 (0/1)：`;ls` / `;cat` / `;rm` / `;wget` / `;curl` / 管道 / `&&` / 反引號 / `$()` / `${}` / `/etc/passwd` / `/bin/bash` |
| `has_file_inclusion` | 檔案包含攻擊 (0/1)：`file://` / `php://` / `data://` / `expect://` / `input://` |
| `url_encoding_count` | URL 編碼數量，計算 `%XX` 格式，缺失填 0 |
| `has_double_encoding` | 雙重編碼 (0/1)：`%25XX`，用於繞過 WAF |
| `accesses_sensitive_path` | 存取敏感路徑 (0/1)：`admin` / `backup` / `config` / `database` / `db` / `test` / `temp` / `tmp` / `log` / `old` / `bak` / `phpmyadmin` / `wp-admin` / `wp-login` / `.git` / `.env` |
| `url_file_type` | 副檔名類型：`none` = 0 / `script` (php, asp, aspx, jsp, cgi) = 1 / `image` (jpg, png, gif, svg, webp, ico) = 2 / `asset` (css, js) = 3 / `document` (pdf, doc, xls...) = 4 / `other` = 5 |

---

## Referer

| Feature | Description |
|---|---|
| `has_referrer` | 是否有 Referrer (0/1)，排除 `-` 和 null |
| `referrer_type` | 來源類型：`none` = 0 / `local` (localhost, 127, 192.168, 10.0) = 1 / `ip_address` (可疑) = 2 / `search_engine` = 3 / `social` = 4 / `external` = 5 |
| `referrer_length` | Referrer 字元長度，無 referrer 填 0 |

> **search_engine**：google / bing / yahoo / baidu / duckduckgo / yandex / naver / sogou  
> **social**：facebook / twitter / instagram / linkedin / youtube / tiktok / line / telegram  
> ⚠️ 目前 dataset (universitas.com) 幾乎無搜尋引擎與社交媒體流量，換資料集後可能需要重新評估此特徵重要性。

---

## Status

| Feature | Description |
|---|---|
| `status` | HTTP 狀態碼數值 (int)，無效值填 0 |
| `status_category` | 狀態碼百位數分類 (1 / 2 / 3 / 4 / 5)，無效填 0 |
| `is_error_status` | 是否為錯誤狀態 (0/1)，4xx / 5xx |
| `is_success_status` | 是否為成功狀態 (0/1)，2xx |

---

## Size

| Feature | Description |
|---|---|
| `size` | 回應大小 bytes (int)，無效值填 0 |
| `size_category` | 大小分類：`zero` = 0 / `<1KB` = 1 / `1–10KB` = 2 / `10–100KB` = 3 / `100KB–1MB` = 4 / `>1MB` = 5 |
| `log_size` | `log1p(size)`，對數轉換處理長尾分布 |

---

## Browser (User Agent)

| Feature | Description |
|---|---|
| `os_type` | 作業系統：`unknown` = 0 / `windows` = 1 / `android` = 2 / `ios` = 3 / `linux` = 4 / `mac` = 5 / `bot` = 6 / `other` = 7 |
| `is_bot` | 是否為爬蟲／Bot (0/1)，`os_type == 6` |
| `ua_length` | User Agent 字元長度，缺失填 0 |

45
37+8
原本dataset有10個特徵
去掉country gmt有八個。
pipeline 現在送出的 31 個欄位完全覆蓋模型需求，額外 3 個（DT 需要的）由 _add_missing_features 在 API 內計算，不需要從 pipeline 傳。文件上的 45 是「所有原始+衍生欄位」的總計，並非任何一個模型的實際輸入數。

45 = spec 上列過的所有欄位，包含：


|類別|例子|進模型？|
|--|--|--|
|中間過渡欄|datetime_parsed、url（從 request 解析出來再被用掉）|❌|
|因共線性移除|is_weekend（= day_of_week≥5）、is_success_status（= !is_error_status）、size_category（與 log_size 高度相關）	|❌|
|原始欄未轉換|size（只送 log_size）、request 原始字串|❌|
|SVM 專用 sin/cos|	hour_sin、hour_cos、dow_sin、dow_cos|❌（RF/XGB/DT 不用）|

34 = DT 模型實際接收的欄位：


31 (ML_API_ALLOWED_FIELDS，pipeline 傳)
 + 3 (API 內計算：attack_signal_count、attack_intensity、url_entropy)
= 34
RF 和 XGB 用 31，DT 用 34，SVM 用不同子集（~28，沒有 label-encoded categoricals，這是訓練時的歷史問題）。

簡單說：45 是「所有有關的欄位清單」，34 是「最貪心的那個模型的實際輸入」，中間差的 11 個要麼是中途產物、要麼被特徵選擇刷掉了。

---

## 各模型實際輸入欄位（從模型檔案讀取）

### RF / XGB — 31 個（相同）

| # | 欄位 | 來源 |
|---|------|------|
| 1 | `ip_first_octet` | pipeline |
| 2 | `hour` | pipeline |
| 3 | `day_of_week` | pipeline |
| 4 | `is_odd_hour` | pipeline |
| 5 | `time_period` | pipeline |
| 6 | `url_length` | pipeline |
| 7 | `url_depth` | pipeline |
| 8 | `url_param_count` | pipeline |
| 9 | `url_special_chars` | pipeline |
| 10 | `has_sql_injection` | pipeline |
| 11 | `has_xss` | pipeline |
| 12 | `has_path_traversal` | pipeline |
| 13 | `has_command_injection` | pipeline |
| 14 | `has_file_inclusion` | pipeline |
| 15 | `url_encoding_count` | pipeline |
| 16 | `has_double_encoding` | pipeline |
| 17 | `accesses_sensitive_path` | pipeline |
| 18 | `url_file_type` | pipeline |
| 19 | `has_referrer` | pipeline |
| 20 | `referrer_type` | pipeline |
| 21 | `referrer_length` | pipeline |
| 22 | `status` | pipeline |
| 23 | `status_category` | pipeline |
| 24 | `is_error_status` | pipeline |
| 25 | `log_size` | pipeline |
| 26 | `os_type` | pipeline |
| 27 | `is_bot` | pipeline |
| 28 | `ua_length` | pipeline |
| 29 | `ip_type_encoded` | API 內：pipeline 送整數 → decode → label encode |
| 30 | `request_method_encoded` | API 內：pipeline 送整數 → decode → label encode |
| 31 | `request_version_encoded` | API 內：pipeline 送整數 → decode → label encode |

### DT — 34 個（RF/XGB + 3）

上方 31 個，再加：

| # | 欄位 | 來源 |
|---|------|------|
| 32 | `attack_signal_count` | API 內計算：5 個攻擊 flag 加總 |
| 33 | `url_entropy` | API 內計算：目前 default 0.0（未實作） |
| 34 | `attack_intensity` | API 內計算：`attack_signal_count × log1p(url_length)` |

### SVM — 33 個（與 RF/XGB/DT 不同子集）

用 sin/cos 週期編碼取代線性整數，含 `is_weekend`、`is_success_status`、`size_category`，但**不含** label-encoded categoricals。sin/cos 特徵由 ML API 的 `_add_missing_features()` 呼叫 `extract_datetime_features()` 計算，端對端流程完整。

**SVM 特徵處理方式分類**

| 處理方式 | 欄位 | 與 RF/XGB/DT 的差異 |
|----------|------|----------------------|
| **sin/cos 週期編碼** | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | 取代線性整數 `hour`/`day_of_week`；`_add_missing_features()` 從傳入的 `hour`/`day_of_week` 自動計算 |
| **SVM 額外保留** | `is_weekend`, `is_success_status`, `size_category` | RF/XGB/DT 因共線性裁除；SVM 距離計算需要更完整的數值覆蓋，保留作連續特徵 |
| **不含，改用 OHE** | `ip_type_encoded`, `request_method_encoded`, `request_version_encoded` | RF/XGB/DT 以 label-encode 整數輸入；SVM 改用原始字串 (`CATEGORICAL_FEATURES`) 交由 Pipeline 內 `OneHotEncoder` 處理，避免序數距離問題 |

| # | 欄位 | 差異 |
|---|------|------|
| 1 | `ip_first_octet` | 同 RF/XGB |
| 2–5 | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | 取代 `hour`/`day_of_week` |
| 6 | `is_weekend` | RF/XGB/DT 不用，SVM 保留 |
| 7 | `is_odd_hour` | 同 RF/XGB |
| 8 | `time_period` | 同 RF/XGB |
| 9–25 | URL / Referrer / Status 欄位（17 個） | 同 RF/XGB |
| 26 | `is_success_status` | RF/XGB/DT 不用，SVM 保留 |
| 27 | `size_category` | RF/XGB/DT 不用，SVM 保留 |
| 28 | `log_size` | 同 RF/XGB |
| 29–31 | `os_type`, `is_bot`, `ua_length` | 同 RF/XGB |

> ⚠️ SVM 不含 `ip_type_encoded`、`request_method_encoded`、`request_version_encoded`