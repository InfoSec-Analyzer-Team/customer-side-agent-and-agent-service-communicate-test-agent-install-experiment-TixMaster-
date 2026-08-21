# Stage 1 多元度驗收報告 — 敏感路徑

- 樣本數：16107
- **Diversity_stage = 0.2142**

## Warnings

- ⚠️ stage 1: 11223/16107 筆樣本不符合定義判準 [{'feature': 'accesses_sensitive_path', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations，只列前 500 筆，真實總數見 defining_violations_total）
- ⚠️ stage 1: 支撐特徵 'ua_length' 完全塌縮（d=0）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 264 | nginx/collected/nginx01_batch_nikto_scan_001.log | 1 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET / HTTP/1.1 | / | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 265 | nginx/collected/nginx01_batch_nikto_scan_001.log | 2 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET / HTTP/1.1 | / | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 266 | nginx/collected/nginx01_batch_nikto_scan_001.log | 3 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET / HTTP/1.1 | / | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 267 | nginx/collected/nginx01_batch_nikto_scan_001.log | 4 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET /Et6fMbjV.md HTTP/1.1 | /Et6fMbjV.md | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 268 | nginx/collected/nginx01_batch_nikto_scan_001.log | 5 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET /Et6fMbjV.en HTTP/1.1 | /Et6fMbjV.en | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 269 | nginx/collected/nginx01_batch_nikto_scan_001.log | 6 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET /Et6fMbjV.htpasswd HTTP/1.1 | /Et6fMbjV.htpasswd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 270 | nginx/collected/nginx01_batch_nikto_scan_001.log | 7 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET /Et6fMbjV.list HTTP/1.1 | /Et6fMbjV.list | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 271 | nginx/collected/nginx01_batch_nikto_scan_001.log | 8 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET /Et6fMbjV.cfm HTTP/1.1 | /Et6fMbjV.cfm | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 272 | nginx/collected/nginx01_batch_nikto_scan_001.log | 9 | 172.22.0.1 | 2026-08-06T13:59:57+00:00 | GET /Et6fMbjV.se HTTP/1.1 | /Et6fMbjV.se | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 274 | nginx/collected/nginx01_batch_nikto_scan_001.log | 11 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV HTTP/1.1 | /Et6fMbjV | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 275 | nginx/collected/nginx01_batch_nikto_scan_001.log | 12 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.jsp+ HTTP/1.1 | /Et6fMbjV.jsp+ | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 276 | nginx/collected/nginx01_batch_nikto_scan_001.log | 13 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.markdown HTTP/1.1 | /Et6fMbjV.markdown | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 277 | nginx/collected/nginx01_batch_nikto_scan_001.log | 14 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.lic HTTP/1.1 | /Et6fMbjV.lic | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 278 | nginx/collected/nginx01_batch_nikto_scan_001.log | 15 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.genpopuplist HTTP/1.1 | /Et6fMbjV.genpopuplist | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 279 | nginx/collected/nginx01_batch_nikto_scan_001.log | 16 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.conf HTTP/1.1 | /Et6fMbjV.conf | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 280 | nginx/collected/nginx01_batch_nikto_scan_001.log | 17 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.snp HTTP/1.1 | /Et6fMbjV.snp | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 281 | nginx/collected/nginx01_batch_nikto_scan_001.log | 18 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.eml HTTP/1.1 | /Et6fMbjV.eml | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 282 | nginx/collected/nginx01_batch_nikto_scan_001.log | 19 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.idc HTTP/1.1 | /Et6fMbjV.idc | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 283 | nginx/collected/nginx01_batch_nikto_scan_001.log | 20 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.es HTTP/1.1 | /Et6fMbjV.es | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |
| 284 | nginx/collected/nginx01_batch_nikto_scan_001.log | 21 | 172.22.0.1 | 2026-08-06T13:59:58+00:00 | GET /Et6fMbjV.stm HTTP/1.1 | /Et6fMbjV.stm | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 |

...還有 11203 筆，明細見 JSON 輸出的 `defining_violations`（JSON 也有截斷，見 config.MAX_DEFINING_VIOLATIONS）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `os_type` | 0.0520 | 0.25 | 0, 2, 3, 4, 5, 6 |
| `ua_length` | 0.0000 | — | — |
| `request_method` | 0.0377 | 0.75 | DELETE, PATCH |
| `url_depth` | 0.5000 | — | — |
| `url_length` | 0.6706 | — | — |
| `referrer_type` | 0.0252 | 0.33 | 1, 2, 3, 4 |
