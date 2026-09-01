# Stage 4 多元度驗收報告 — 路徑遍歷

- 樣本數：120（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）
- **Diversity_stage = 0.2351**

## Warnings

- ⚠️ stage 4: 105/120 筆樣本不符合定義判準 [{'feature': 'has_path_traversal', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations）
- ⚠️ stage 4: n_samples=120 < MIN_SAMPLES=200，熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻
- ⚠️ stage 4: 支撐特徵 'os_type' 完全塌縮（d=0）
- ⚠️ stage 4: 支撐特徵 'has_double_encoding' 完全塌縮（d=0）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/collected/nginx01_batch_path_traversal_001.log | 1 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | Mozilla/5.0 Chrome |
| 1 | nginx/collected/nginx01_batch_path_traversal_001.log | 2 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /..%2F..%2F..%2Fetc%2Fpasswd | GET | - |
| 2 | nginx/collected/nginx01_batch_path_traversal_001.log | 3 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | Mozilla/5.0 Chrome |
| 3 | nginx/collected/nginx01_batch_path_traversal_001.log | 4 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /download?file=..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /download?file=..%2F..%2F..%2Fetc%2Fpasswd | GET | nikto |
| 4 | nginx/collected/nginx01_batch_path_traversal_001.log | 5 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /download?file=..%5C..%5Cwindows%5Cwin.ini HTTP/1.1 | /download?file=..%5C..%5Cwindows%5Cwin.ini | GET | Mozilla/5.0 Chrome |
| 6 | nginx/collected/nginx01_batch_path_traversal_001.log | 7 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /view?file=..%2F..%2F..%2Fetc%2Fshadow HTTP/1.1 | /view?file=..%2F..%2F..%2Fetc%2Fshadow | GET | curl/8.0 |
| 7 | nginx/collected/nginx01_batch_path_traversal_001.log | 8 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /api/events?file=..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /api/events?file=..%2F..%2F..%2Fetc%2Fpasswd | GET | dotdotpwn/3.0 |
| 8 | nginx/collected/nginx01_batch_path_traversal_001.log | 9 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | curl/8.0 |
| 9 | nginx/collected/nginx01_batch_path_traversal_001.log | 10 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /..%2F..%2F..%2Fetc%2Fpasswd | GET | - |
| 10 | nginx/collected/nginx01_batch_path_traversal_001.log | 11 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | dotdotpwn/3.0 |
| 11 | nginx/collected/nginx01_batch_path_traversal_001.log | 12 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /download?file=..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /download?file=..%2F..%2F..%2Fetc%2Fpasswd | GET | dotdotpwn/3.0 |
| 12 | nginx/collected/nginx01_batch_path_traversal_001.log | 13 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /download?file=..%5C..%5Cwindows%5Cwin.ini HTTP/1.1 | /download?file=..%5C..%5Cwindows%5Cwin.ini | GET | nikto |
| 14 | nginx/collected/nginx01_batch_path_traversal_001.log | 15 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /view?file=..%2F..%2F..%2Fetc%2Fshadow HTTP/1.1 | /view?file=..%2F..%2F..%2Fetc%2Fshadow | GET | nikto |
| 15 | nginx/collected/nginx01_batch_path_traversal_001.log | 16 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /api/events?file=..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /api/events?file=..%2F..%2F..%2Fetc%2Fpasswd | GET | curl/8.0 |
| 16 | nginx/collected/nginx01_batch_path_traversal_001.log | 17 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | dotdotpwn/3.0 |
| 17 | nginx/collected/nginx01_batch_path_traversal_001.log | 18 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /..%2F..%2F..%2Fetc%2Fpasswd | GET | - |
| 18 | nginx/collected/nginx01_batch_path_traversal_001.log | 19 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | dotdotpwn/3.0 |
| 19 | nginx/collected/nginx01_batch_path_traversal_001.log | 20 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /download?file=..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /download?file=..%2F..%2F..%2Fetc%2Fpasswd | GET | curl/8.0 |
| 20 | nginx/collected/nginx01_batch_path_traversal_001.log | 21 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /download?file=..%5C..%5Cwindows%5Cwin.ini HTTP/1.1 | /download?file=..%5C..%5Cwindows%5Cwin.ini | GET | dotdotpwn/3.0 |
| 22 | nginx/collected/nginx01_batch_path_traversal_001.log | 23 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /view?file=..%2F..%2F..%2Fetc%2Fshadow HTTP/1.1 | /view?file=..%2F..%2F..%2Fetc%2Fshadow | GET | curl/8.0 |

...還有 85 筆，明細見 JSON 輸出的 `defining_violations`

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_depth` | 0.3333 | — | — |
| `url_length` | 0.2679 | — | — |
| `url_encoding_count` | 0.2800 | — | — |
| `os_type` | 0.0000 | 0.12 | 0, 1, 2, 3, 4, 5, 6 |
| `ua_length` | 0.5294 | — | — |
| `has_double_encoding` | 0.0000 | 0.50 | 1 |
