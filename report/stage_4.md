# Stage 4 多元度驗收報告 — 路徑遍歷

- 樣本數：165（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）
- **Diversity_stage = 0.4754**

## Warnings

- ⚠️ stage 4: 30/165 筆樣本不符合定義判準 [{'feature': 'has_path_traversal', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations）
- ⚠️ stage 4: n_samples=165 < MIN_SAMPLES=200，熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | nginx/collected/nginx01_batch_path_traversal_ffuf_002.log | 3 | 172.17.0.1 | 2026-09-01T06:08:30+00:00 | GET /api/events/1/attachment?file=etc/passwd HTTP/1.1 | /api/events/1/attachment?file=etc/passwd | GET | Fuzz Faster U Fool v2.1.0-dev |
| 4 | nginx/collected/nginx01_batch_path_traversal_ffuf_002.log | 5 | 172.17.0.1 | 2026-09-01T06:08:30+00:00 | GET /api/events/1/attachment?file=..%25322f..%25322fetc%25322fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%25322f..%25322fetc%25322fpasswd | GET | Fuzz Faster U Fool v2.1.0-dev |
| 5 | nginx/collected/nginx01_batch_path_traversal_ffuf_002.log | 6 | 172.17.0.1 | 2026-09-01T06:08:30+00:00 | GET /api/events/1/attachment?file=..%252f..%252fetc%252fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%252f..%252fetc%252fpasswd | GET | Fuzz Faster U Fool v2.1.0-dev |
| 12 | nginx/collected/nginx01_batch_path_traversal_ffuf_002.log | 13 | 172.17.0.1 | 2026-09-01T06:08:30+00:00 | GET /api/events/1/attachment?file=..;/..;/etc/passwd HTTP/1.1 | /api/events/1/attachment?file=..;/..;/etc/passwd | GET | Fuzz Faster U Fool v2.1.0-dev |
| 14 | nginx/collected/nginx01_batch_path_traversal_ffuf_002.log | 15 | 172.17.0.1 | 2026-09-01T06:08:30+00:00 | GET /api/events/1/attachment?file=..%252F..%252Fetc%252Fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%252F..%252Fetc%252Fpasswd | GET | Fuzz Faster U Fool v2.1.0-dev |
| 15 | nginx/collected/nginx01_batch_path_traversal_ffuf_002.log | 16 | 172.17.0.1 | 2026-09-01T06:08:30+00:00 | GET /api/events/1/attachment?file=%252e%252e%252f%252e%252e%252fetc%252fpasswd HTTP/1.1 | /api/events/1/attachment?file=%252e%252e%252f%252e%252e%252fetc%252fpasswd | GET | Fuzz Faster U Fool v2.1.0-dev |
| 33 | nginx/collected/nginx01_batch_path_traversal_ffuf_ipua_003.log | 1 | 10.88.4.31 | 2026-09-01T13:07:06+00:00 | GET /api/events/1/attachment?file=..%25322f..%25322fetc%25322fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%25322f..%25322fetc%25322fpasswd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 40 | nginx/collected/nginx01_batch_path_traversal_ffuf_ipua_003.log | 8 | 10.88.4.31 | 2026-09-01T13:07:06+00:00 | GET /api/events/1/attachment?file=etc/passwd HTTP/1.1 | /api/events/1/attachment?file=etc/passwd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 44 | nginx/collected/nginx01_batch_path_traversal_ffuf_ipua_003.log | 12 | 10.88.4.31 | 2026-09-01T13:07:06+00:00 | GET /api/events/1/attachment?file=..%252F..%252Fetc%252Fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%252F..%252Fetc%252Fpasswd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 45 | nginx/collected/nginx01_batch_path_traversal_ffuf_ipua_003.log | 13 | 10.88.4.31 | 2026-09-01T13:07:06+00:00 | GET /api/events/1/attachment?file=%252e%252e%252f%252e%252e%252fetc%252fpasswd HTTP/1.1 | /api/events/1/attachment?file=%252e%252e%252f%252e%252e%252fetc%252fpasswd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 46 | nginx/collected/nginx01_batch_path_traversal_ffuf_ipua_003.log | 14 | 10.88.4.31 | 2026-09-01T13:07:06+00:00 | GET /api/events/1/attachment?file=..;/..;/etc/passwd HTTP/1.1 | /api/events/1/attachment?file=..;/..;/etc/passwd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 47 | nginx/collected/nginx01_batch_path_traversal_ffuf_ipua_003.log | 15 | 10.88.4.31 | 2026-09-01T13:07:06+00:00 | GET /api/events/1/attachment?file=..%252f..%252fetc%252fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%252f..%252fetc%252fpasswd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 69 | nginx/collected/nginx01_batch_path_traversal_ffuf_postquery_night_004.log | 4 | 10.99.4.41 | 2026-09-01T13:33:40+00:00 | POST /api/events/1/attachment?file=..%25322f..%25322fetc%25322fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%25322f..%25322fetc%25322fpasswd | POST | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 75 | nginx/collected/nginx01_batch_path_traversal_ffuf_postquery_night_004.log | 10 | 10.99.4.41 | 2026-09-01T13:33:40+00:00 | POST /api/events/1/attachment?file=etc/passwd HTTP/1.1 | /api/events/1/attachment?file=etc/passwd | POST | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 80 | nginx/collected/nginx01_batch_path_traversal_ffuf_postquery_night_004.log | 15 | 10.99.4.41 | 2026-09-01T13:33:41+00:00 | POST /api/events/1/attachment?file=..%252F..%252Fetc%252Fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%252F..%252Fetc%252Fpasswd | POST | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 85 | nginx/collected/nginx01_batch_path_traversal_ffuf_postquery_night_004.log | 20 | 10.99.4.41 | 2026-09-01T13:33:41+00:00 | POST /api/events/1/attachment?file=..%252f..%252fetc%252fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%252f..%252fetc%252fpasswd | POST | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 89 | nginx/collected/nginx01_batch_path_traversal_ffuf_postquery_night_004.log | 24 | 10.99.4.41 | 2026-09-01T13:33:41+00:00 | POST /api/events/1/attachment?file=%252e%252e%252f%252e%252e%252fetc%252fpasswd HTTP/1.1 | /api/events/1/attachment?file=%252e%252e%252f%252e%252e%252fetc%252fpasswd | POST | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 98 | nginx/collected/nginx01_batch_path_traversal_ffuf_postquery_night_004.log | 33 | 10.99.4.41 | 2026-09-01T13:33:41+00:00 | POST /api/events/1/attachment?file=..;/..;/etc/passwd HTTP/1.1 | /api/events/1/attachment?file=..;/..;/etc/passwd | POST | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 |
| 100 | nginx/collected/nginx01_batch_path_traversal_ffuf_morning_005.log | 2 | 10.120.4.51 | 2026-09-02T02:46:24+00:00 | GET /api/events/1/attachment?file=..%25322f..%25322fetc%25322fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%25322f..%25322fetc%25322fpasswd | GET | Mozilla/5.0 (Macintosh; Intel Mac OS X 15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/20.0 Safari/605.1.15 |
| 102 | nginx/collected/nginx01_batch_path_traversal_ffuf_morning_005.log | 4 | 10.120.4.51 | 2026-09-02T02:46:24+00:00 | GET /api/events/1/attachment?file=..%252f..%252fetc%252fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%252f..%252fetc%252fpasswd | GET | Mozilla/5.0 (Macintosh; Intel Mac OS X 15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/20.0 Safari/605.1.15 |

...還有 10 筆，明細見 JSON 輸出的 `defining_violations`

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_depth` | 0.2727 | — | — |
| `url_length` | 0.0642 | — | — |
| `url_encoding_count` | 1.0000 | — | — |
| `os_type` | 0.5073 | 0.38 | 0, 2, 3, 4, 6 |
| `has_double_encoding` | 0.5328 | 1.00 | — |
