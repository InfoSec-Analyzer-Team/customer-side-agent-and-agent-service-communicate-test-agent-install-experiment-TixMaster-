# Stage 1 多元度驗收報告 — 敏感路徑

- 樣本數：4743
- **Diversity_stage = 0.2433**

## Warnings

- ⚠️ stage 1: 3990/4743 筆樣本不符合定義判準 [{'feature': 'accesses_sensitive_path', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations，只列前 500 筆，真實總數見 defining_violations_total）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | nginx/logs/access2_Dicurigai_sensitive_path.log | 17 | 172.20.0.1 | 2026-08-08T00:44:24+00:00 | GET /configuration.php HTTP/1.1 | /configuration.php | GET | curl/8.5.0 |
| 47 | nginx/logs/access2_Dicurigai_sensitive_path.log | 48 | 172.20.0.1 | 2026-08-08T00:50:47+00:00 | GET /configuration.php HTTP/1.1 | /configuration.php | GET | curl/8.5.0 |
| 72 | nginx/logs/access2_Dicurigai_sensitive_path.log | 73 | 172.20.0.1 | 2026-08-08T00:53:17+00:00 | GET /configuration.php HTTP/1.1 | /configuration.php | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 104 | nginx/logs/access2_Dicurigai_sensitive_path.log | 105 | 172.20.0.1 | 2026-08-15T20:05:45+00:00 | GET /configuration.php HTTP/1.1 | /configuration.php | GET | Nikto/2.5.0 |
| 137 | nginx/logs/access2_Dicurigai_sensitive_path.log | 138 | 172.20.0.1 | 2026-08-15T20:05:45+00:00 | GET /configuration.php HTTP/1.1 | /configuration.php | GET | Nikto/2.5.0 |
| 166 | nginx/logs/access2_Dicurigai_sensitive_path.log | 167 | 172.20.0.1 | 2026-08-15T20:08:52+00:00 | GET /configuration.php HTTP/1.1 | /configuration.php | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 240 | nginx/logs/access2_Dicurigai_sensitive_path.log | 241 | 172.20.0.1 | 2026-08-20T14:06:13+00:00 | HEAD /configuration.php HTTP/1.1 | /configuration.php | HEAD | gobuster/3.6 |
| 256 | nginx/logs/access2_Dicurigai_sensitive_path.log | 257 | 172.20.0.1 | 2026-08-20T14:06:14+00:00 | HEAD /configuration.php HTTP/1.1 | /configuration.php | HEAD | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 264 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 1 | 10.99.1.41 | 2026-09-01T14:00:58+00:00 | GET / HTTP/1.1 | / | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 265 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 2 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET / HTTP/1.1 | / | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 266 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 3 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET / HTTP/1.1 | / | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 267 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 4 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET /server-status HTTP/1.1 | /server-status | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 268 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 5 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET /icons/ HTTP/1.1 | /icons/ | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 269 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 6 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET /trace.axd HTTP/1.1 | /trace.axd | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 270 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 7 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET /nosuchfile.asp HTTP/1.1 | /nosuchfile.asp | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 271 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 8 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET /nosuchfile.aspx HTTP/1.1 | /nosuchfile.aspx | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 272 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 9 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET /localstart.asp HTTP/1.1 | /localstart.asp | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 273 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 10 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET /docs/ HTTP/1.1 | /docs/ | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 274 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 11 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET /server HTTP/1.1 | /server | GET | Nikto/2.5.0 stage1-lab-controlled-xff |
| 275 | nginx/collected/nginx01_batch_nikto_scan_xff_clean_003.log | 12 | 10.99.1.41 | 2026-09-01T14:00:59+00:00 | GET / HTTP/1.1 | / | GET | Nikto/2.5.0 stage1-lab-controlled-xff |

...還有 3970 筆，明細見 JSON 輸出的 `defining_violations`（JSON 也有截斷，見 config.MAX_DEFINING_VIOLATIONS）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `os_type` | 0.0526 | 0.25 | 0, 2, 3, 4, 5, 6 |
| `request_method` | 0.0484 | 0.62 | DELETE, PATCH, TRACE |
| `url_depth` | 0.5000 | — | — |
| `url_length` | 0.5769 | — | — |
| `referrer_type` | 0.0384 | 0.33 | 1, 2, 3, 4 |
