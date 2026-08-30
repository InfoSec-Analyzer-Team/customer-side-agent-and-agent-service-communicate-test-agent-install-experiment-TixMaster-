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

## Review-Driven Replacement

The first submitted batches were replaced after PR review because several of
them had strong shortcut-learning risks: fixed tool User-Agent strings
(`sqlmap`/`Nikto`), repeated request templates, narrow method coverage, and weak
IP/OS/time diversity.

The current collected dataset therefore removes those old tool-heavy batches
from the formal log set and replaces them with browser-like attack batches.
These new batches still come from real HTTP requests through Nginx, but mix
User-Agent, OS family, `X-Forwarded-For`, referrer, language, method, and
payload variants so the model has to learn request content instead of a single
tool fingerprint.

## Batch Summary

| Batch ID | Label | Traffic Type | Tool / Method | Count | Purpose |
|---|---|---|---|---:|---|
| nginx01_batch_sqli_browserua_001 | BAHAYA | sqli_payload_browser_like | PowerShell Invoke-WebRequest | 240 | SQLi payload attempts without sqlmap User-Agent shortcut |
| nginx01_batch_xss_browserua_001 | BAHAYA | xss_payload_browser_like | PowerShell Invoke-WebRequest | 240 | XSS payload attempts with desktop/mobile browser UA diversity |
| nginx01_batch_path_traversal_encoded_001 | BAHAYA | path_traversal_encoded_browser_like | PowerShell Invoke-WebRequest | 240 | Encoded path traversal variants including `..%2F` and double encoding |
| nginx01_batch_dicurigai_diverse_probe_001 | DICURIGAI | diverse_suspicious_probe | PowerShell Invoke-WebRequest | 225 | Diverse suspicious probes without repeating only 10 templates |

## Diversity Controls

The replacement batches intentionally vary these support features:

```text
User-Agent: Windows Chrome, Mac Safari, Linux Chrome, iPhone Safari,
            Android Chrome, Firefox, Edge
X-Forwarded-For: 198.51.100.0/24, 203.0.113.0/24, 192.0.2.0/24
Referrer: none, local pages, search-like, external-like, social-like
HTTP methods: GET, POST, HEAD, OPTIONS; DICURIGAI also includes PUT,
              DELETE, TRACE
Accept-Language: en-US, zh-TW, id-ID
```

The IP ranges are RFC 5737 documentation ranges used only for lab simulation.
They are varied through Nginx `X-Forwarded-For` handling so the access log does
not collapse to the Docker bridge address.

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
  -Tool powershell_invoke_webrequest `
  -Notes "<notes>"
```

## 1. SQLi Browser-Like

Batch:

```text
nginx01_batch_sqli_browserua_001
```

Payload families:

```text
' OR '1'='1
UNION SELECT 1,2,3
AND 7110=9042
'--
OR SLEEP(1)
ASCII(SUBSTR(database(),1,1)) > 64
```

Purpose:

```text
Keep SQLi payload evidence in the request URL while removing the obvious
sqlmap User-Agent shortcut.
```

## 2. XSS Browser-Like

Batch:

```text
nginx01_batch_xss_browserua_001
```

Payload families:

```text
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
javascript:alert(1)
"><script>alert(1)</script>
<iframe src=javascript:alert(1)>
```

Purpose:

```text
Preserve XSS attack-attempt payloads while mixing desktop and mobile browser
User-Agent strings.
```

## 3. Encoded Path Traversal

Batch:

```text
nginx01_batch_path_traversal_encoded_001
```

Payload families:

```text
..%2F..%2F..%2Fetc%2Fpasswd
%2e%2e%2f%2e%2e%2fetc%2fpasswd
%252e%252e%252f%252e%252e%252fetc%252fpasswd
....//....//etc/passwd
..%5C..%5Cwindows%5Cwin.ini
```

Purpose:

```text
Address the review finding that simple traversal detection misses common
encoded variants such as ..%2F.
```

## 4. DICURIGAI Diverse Probe

Batch:

```text
nginx01_batch_dicurigai_diverse_probe_001
```

Probe families:

```text
/.env
/.git/config
/admin
/phpmyadmin
/server-status
/backup.zip
/db.sql
/wp-login.php
/.aws/credentials
/actuator/env
double-encoded probes
long query strings
```

Purpose:

```text
Replace the old 100-line probe batch that repeated only 10 request templates.
This batch uses more path variation, more methods, more IPs, and full
browser-like User-Agent strings.
```

## Labeling Rule

Nginx access.log 本身不包含 label。Label 寫在對應的 `.meta.txt` 中，例如：

```text
nginx01_batch_xss_browserua_001.log
nginx01_batch_xss_browserua_001.meta.txt  -> label: BAHAYA
```

後續轉 dataset 時，應由 `.meta.txt` 將整批 log 補上 label 欄位。

## Important Notes

1. `BAHAYA` 表示明確攻擊 payload 或 browser-like attack-attempt traffic。
2. `DICURIGAI` 表示可疑探測、異常結構或輕量 probe，但不一定是確認攻擊。
3. 這些是 lab-generated browser-like attack attempt logs，不是 production incident logs。
4. 有些 TixMaster 路徑會被 SPA fallback 回 200，因此不要只依賴 status code 或 response size 判斷惡意程度。
5. 訓練模型時應避免過度依賴 source_ip、hour、User-Agent 單一特徵，應更重視 payload pattern、URL 結構、encoding、method、path 等特徵。
