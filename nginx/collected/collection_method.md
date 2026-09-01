# Nginx Attack Log Collection Method

本資料夾內的 log 皆為本機 lab 環境中，攻擊工具或手動 payload 真的對本機 Nginx 發送 HTTP request 後，由 Nginx 自己寫出的 access log。不是手寫偽造 log。

Target:

```text
http://localhost:8080
```

收集方式固定為：

```text
1. capture-nginx-batch.ps1 start 記錄 access.log 起始行數
2. 執行工具或手動 payload 對 Nginx 發 request
3. capture-nginx-batch.ps1 finish 擷取本批新增 log
4. 產生 .log 與 .meta.txt
```

注意：這些資料是 lab / pentest traffic，不是 production real-world incident log。

## Batch Summary

| Batch ID | Label | Traffic Type | Tool / Method | Count | Purpose |
|---|---|---|---|---:|---|
| nginx01_batch_nikto_scan_001 | BAHAYA | tool_generated_scan | Nikto Docker | 15843 | 敏感路徑掃描、弱點掃描、scanner UA |
| nginx01_batch_sqlmap_sqli_001 | BAHAYA | tool_generated_sqli | sqlmap Docker | 378 | SQL Injection 測試請求 |
| nginx01_batch_xss_001 | BAHAYA | xss_payload_attempt | PowerShell manual payload | 250 | XSS payload attempt |
| nginx01_batch_path_traversal_001 | BAHAYA | path_traversal_attempt | PowerShell manual payload | 120 | Path traversal attempt |
| nginx01_batch_dicurigai_probe_001 | DICURIGAI | suspicious_probe_mixed | PowerShell manual probe | 100 | 可疑但非確認攻擊的探測流量 |

## Common Capture Commands

Start batch:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\capture-nginx-batch.ps1 `
  -Action start `
  -BatchId <batch_id>
```

Finish batch:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\capture-nginx-batch.ps1 `
  -Action finish `
  -BatchId <batch_id> `
  -Label <AMAN/DICURIGAI/BAHAYA> `
  -TrafficType <traffic_type> `
  -Tool <tool> `
  -Notes "<notes>"
```

## 1. Nikto Scan

Batch:

```text
nginx01_batch_nikto_scan_001
```

Command:

```powershell
docker run --rm ghcr.io/sullo/nikto:latest -h http://host.docker.internal:8080
```

Label:

```text
BAHAYA
```

Reason:

```text
Nikto 會產生大量敏感路徑探測與弱點掃描 request，例如 metadata endpoint、wp-config.php、admin/login、swagger、graphql 等。
```

Covers features:

```text
accesses_sensitive_path
is_bot
os_type / ua_length
url_depth
scanner-like behavior
```

## 2. SQL Injection via sqlmap

Batch:

```text
nginx01_batch_sqlmap_sqli_001
```

Command:

```powershell
docker run --rm parrotsec/sqlmap:latest `
  -u "http://host.docker.internal:8080/api/events?id=1" `
  --batch --level=2 --risk=1
```

Label:

```text
BAHAYA
```

Reason:

```text
sqlmap 會對 id 參數發送 boolean-based、error-based、time-based、UNION 等 SQLi 測試 payload。即使目標未被確認可注入，這批仍是 SQLi attack attempt log。
```

Covers features:

```text
has_sql_injection
url_encoding_count
url_special_chars
suspicious_user_agent
query_param_payload
```

## 3. XSS Payload Attempts

Batch:

```text
nginx01_batch_xss_001
```

Method:

```text
PowerShell 手動送出 XSS payload，payload 放在 query string 中，確保 Nginx access.log 能記錄到。
```

Example payloads:

```text
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
"><script>alert(document.domain)</script>
<iframe src=javascript:alert(1)>
```

Example target paths:

```text
/event-detail.html?id=1&name=<payload>
/login.html?returnUrl=<payload>
/register.html?name=<payload>
/api/events?keyword=<payload>
/search?q=<payload>
```

Label:

```text
BAHAYA
```

Reason:

```text
這批是 XSS attack attempt log。它表示 request 內含 XSS payload，但不宣稱網站一定成功執行 JavaScript。
```

Covers features:

```text
has_xss
url_special_chars
url_encoding_count
payload_in_query
```

## 4. Path Traversal Attempts

Batch:

```text
nginx01_batch_path_traversal_001
```

Method:

```text
PowerShell 手動送出 path traversal payload。
```

Example payloads:

```text
/../../etc/passwd
/..%2F..%2F..%2Fetc%2Fpasswd
/static/../../backend/.env
/download?file=..%2F..%2F..%2Fetc%2Fpasswd
/download?file=..%5C..%5Cwindows%5Cwin.ini
/images/%2e%2e/%2e%2e/%2e%2e/etc/passwd
/view?file=..%2F..%2F..%2Fetc%2Fshadow
/api/events?file=..%2F..%2F..%2Fetc%2Fpasswd
```

Label:

```text
BAHAYA
```

Reason:

```text
這批 request 嘗試使用 ../、URL encoded traversal、Windows 路徑等方式讀取敏感檔案。
```

Covers features:

```text
has_path_traversal
accesses_sensitive_path
url_encoding_count
url_depth
```

## 5. Suspicious Probe Mixed

Batch:

```text
nginx01_batch_dicurigai_probe_001
```

Method:

```text
PowerShell 手動送出可疑但非確認攻擊的 request。
```

Included request types:

```text
敏感路徑探測但使用瀏覽器 UA
輕量單引號 probe
雙重編碼 probe
OPTIONS / TRACE / PUT 等異常 method
超長 URL
大量 query parameters
curl / PowerShell UA
```

Label:

```text
DICURIGAI
```

Reason:

```text
這批行為可疑，但不一定能確認為成功攻擊，因此標為 DICURIGAI，而不是 BAHAYA。
```

Covers features:

```text
accesses_sensitive_path
request_method
url_length
url_depth
url_param_count
has_double_encoding
suspicious_user_agent
```

## Labeling Rule

Nginx access.log 本身不包含 label。Label 寫在對應的 `.meta.txt` 中，例如：

```text
nginx01_batch_xss_001.log
nginx01_batch_xss_001.meta.txt  -> label: BAHAYA
```

後續轉 dataset 時，應由 `.meta.txt` 將整批 log 補上 label 欄位。

## Important Notes

1. `BAHAYA` 表示明確攻擊 payload 或工具攻擊流量。
2. `DICURIGAI` 表示可疑探測、異常結構或輕量 probe，但不一定是確認攻擊。
3. 這些是 lab-generated / tool-generated attack attempt logs，不是 production incident logs。
4. 有些 TixMaster 路徑會被 SPA fallback 回 200，因此不要只依賴 status code 或 response size 判斷惡意程度。
5. 訓練模型時應避免過度依賴 source_ip、hour、User-Agent 單一特徵，應更重視 payload pattern、URL 結構、encoding、method、path 等特徵。
