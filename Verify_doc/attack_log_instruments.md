# 攻擊項目總表(對照 spec 特徵)

| # | 目標特徵 | 攻擊項目 | 做法 / 工具 | 需要 Kali? | 建議 label |
|---|----------|----------|-------------|------------|------------|
| 1 | `accesses_sensitive_path` | 敏感路徑掃描(已做) | curl/PowerShell 迴圈打 spec 清單那 16 個關鍵字 | ❌ | 多為 DICURIGAI |
| 2 | `has_sql_injection` | SQL Injection | sqlmap 打真實端點(`?id=`);手動補 union/boolean/time-based/註解變形 | ✅ 建議 | BAHAYA |
| 3 | `has_xss` | XSS 注入 | 手動 payload(`<script>` / `onerror=` / `<iframe>`)打搜尋框、可回顯參數;XSStrike 自動化 | 半 | BAHAYA |
| 4 | `has_path_traversal` | 路徑遍歷 | `../`、`%2e%2e`、編碼變形讀 `/etc/passwd`;dotdotpwn | ✅ 建議 | BAHAYA |
| 5 | `has_command_injection` | 命令注入 | `;`、`&&`、`$()`、反引號、`/etc/passwd`、`/bin/bash`;commix | ✅ 建議 | BAHAYA |
| 6 | `has_file_inclusion` | 檔案包含 (LFI/RFI) | `php://`、`file://`、`data://`、`expect://`、`input://`;手動 + wfuzz | 半 | BAHAYA |
| 7 | `has_double_encoding` | 雙重編碼繞 WAF | `%25XX` 手動構造(工具預設不打,必須手動) | ❌ 但要手工 | BAHAYA / DICURIGAI |
| 8 | `url_encoding_count` | URL 編碼變形 | 把上述 payload 做單層 `%XX` 編碼版本 | ❌ | 同對應攻擊 |
| 9 | `has_xss` + `url_special_chars` | 特殊字元密集 payload | 塞 `< > ' " ; % ( ) [ ] { }` 的請求 | ❌ | 視情況 |
| 10 | `is_bot` / `os_type` / `ua_length` | 掃描器 UA 多樣性 | 換不同 UA(gobuster/sqlmap/nikto/curl/空 UA/超長 UA) | ❌ | 隨附 |
| 11 | `request_method` | 異常 HTTP 方法 | 打 PUT/DELETE/OPTIONS/TRACE、畸形 method | ❌ | DICURIGAI |
| 12 | `url_length` / `url_depth` / `url_param_count` | 異常 URL 結構 | 超長 URL、超深路徑、大量參數(可疑但非攻擊) | ❌ | DICURIGAI |

## 三類容易被漏掉、但很重要的樣本

### A. 難樣本(最有訓練價值)
- 敏感路徑 + 瀏覽器 UA(路徑可疑但 UA 正常,最難判)
- 帶輕微 payload 的偵察(單引號試水溫)→ 天然的 DICURIGAI
- `has_double_encoding`:自動工具幾乎不產生,不手動就是全 0

### B. Benign 對照(不做會毀掉整個訓練集)
- 正常瀏覽你的 app(登入、看活動、買票流程)→ 大量 AMAN
- 正常存取合法端點(如果你 app 真的有 `/admin` 後台,正常登入要標 benign)
- 讓 `referrer_type`、`url_file_type`(css/js/image)、正常 2xx、合理 `ua_length` 有分佈

### C. DICURIGAI(可疑但非確認,三分類最難產的一類)
- 異常時段的正常請求
- 掃描偵察但未帶 payload
- 少見但合法的 UA、異常 HTTP 方法

## 環境分工建議
- **curl / PowerShell 就夠**:敏感路徑、雙重編碼、URL 結構異常、UA 多樣性、異常方法、手動 XSS/編碼變形
- **值得動用 Kali**:sqlmap(SQLi 各種變形窮舉)、commix(command injection)、dotdotpwn(path traversal 大量變形)——這些手動難窮舉,工具能產生大量多樣 payload

## 兩個貫穿所有類別的原則(重申,因為最容易搞砸)
1. **打真實存在的端點**,payload 才會進到應用邏輯、status/size 才真實。打不存在的路徑會觸發 SPA fallback(回 200/6537),status/size 就失真。
2. **時序自然分散**:分時段、分批跑,別全擠在同一分鐘,否則 `hour` / `time_period` / `is_odd_hour` 在攻擊類別裡沒變異。用「真跑」解決,不要事後竄改 timestamp。