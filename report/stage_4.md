# Stage 4 多元度驗收報告 — 路徑遍歷

- 樣本數：120（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）
- **Diversity_stage = 0.2351**

## Warnings

- ⚠️ stage 4: 30/120 筆樣本不符合定義判準 [{'feature': 'has_path_traversal', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations）
- ⚠️ stage 4: n_samples=120 < MIN_SAMPLES=200，熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻
- ⚠️ stage 4: 支撐特徵 'os_type' 完全塌縮（d=0）
- ⚠️ stage 4: 支撐特徵 'has_double_encoding' 完全塌縮（d=0）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/collected/nginx01_batch_path_traversal_001.log | 1 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | Mozilla/5.0 Chrome |
| 2 | nginx/collected/nginx01_batch_path_traversal_001.log | 3 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | Mozilla/5.0 Chrome |
| 8 | nginx/collected/nginx01_batch_path_traversal_001.log | 9 | 172.22.0.1 | 2026-08-11T15:17:15+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | curl/8.0 |
| 10 | nginx/collected/nginx01_batch_path_traversal_001.log | 11 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | dotdotpwn/3.0 |
| 16 | nginx/collected/nginx01_batch_path_traversal_001.log | 17 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | dotdotpwn/3.0 |
| 18 | nginx/collected/nginx01_batch_path_traversal_001.log | 19 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | dotdotpwn/3.0 |
| 24 | nginx/collected/nginx01_batch_path_traversal_001.log | 25 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | curl/8.0 |
| 26 | nginx/collected/nginx01_batch_path_traversal_001.log | 27 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | Mozilla/5.0 Chrome |
| 32 | nginx/collected/nginx01_batch_path_traversal_001.log | 33 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | nikto |
| 34 | nginx/collected/nginx01_batch_path_traversal_001.log | 35 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | nikto |
| 40 | nginx/collected/nginx01_batch_path_traversal_001.log | 41 | 172.22.0.1 | 2026-08-11T15:17:16+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | curl/8.0 |
| 42 | nginx/collected/nginx01_batch_path_traversal_001.log | 43 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | curl/8.0 |
| 48 | nginx/collected/nginx01_batch_path_traversal_001.log | 49 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | curl/8.0 |
| 50 | nginx/collected/nginx01_batch_path_traversal_001.log | 51 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | nikto |
| 56 | nginx/collected/nginx01_batch_path_traversal_001.log | 57 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | dotdotpwn/3.0 |
| 58 | nginx/collected/nginx01_batch_path_traversal_001.log | 59 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | Mozilla/5.0 Chrome |
| 64 | nginx/collected/nginx01_batch_path_traversal_001.log | 65 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | nikto |
| 66 | nginx/collected/nginx01_batch_path_traversal_001.log | 67 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | nikto |
| 72 | nginx/collected/nginx01_batch_path_traversal_001.log | 73 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /etc/passwd HTTP/1.1 | /etc/passwd | GET | Mozilla/5.0 Chrome |
| 74 | nginx/collected/nginx01_batch_path_traversal_001.log | 75 | 172.22.0.1 | 2026-08-11T15:17:17+00:00 | GET /backend/.env HTTP/1.1 | /backend/.env | GET | dotdotpwn/3.0 |

...還有 10 筆，明細見 JSON 輸出的 `defining_violations`

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_depth` | 0.3333 | — | — |
| `url_length` | 0.2679 | — | — |
| `url_encoding_count` | 0.2800 | — | — |
| `os_type` | 0.0000 | 0.12 | 0, 1, 2, 3, 4, 5, 6 |
| `ua_length` | 0.5294 | — | — |
| `has_double_encoding` | 0.0000 | 0.50 | 1 |
