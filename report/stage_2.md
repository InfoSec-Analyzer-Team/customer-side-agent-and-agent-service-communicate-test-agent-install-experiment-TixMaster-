# Stage 2 多元度驗收報告 — SQLi

- 樣本數：378
- **Diversity_stage = 0.2684**

## Warnings

- ⚠️ stage 2: 102/378 筆樣本不符合定義判準 [{'feature': 'has_sql_injection', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations）
- ⚠️ stage 2: 支撐特徵 'os_type' 完全塌縮（d=0）
- ⚠️ stage 2: 支撐特徵 'ua_length' 完全塌縮（d=0）
- ⚠️ stage 2: 支撐特徵 'url_param_count' 完全塌縮（d=0）
- ⚠️ stage 2: 支撐特徵 'request_method' 完全塌縮（d=0）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 1 | 172.22.0.1 | 2026-08-06T14:15:45+00:00 | GET /api/events?id=1 HTTP/1.1 | /api/events?id=1 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 2 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 3 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1 HTTP/1.1 | /api/events?id=1 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 3 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 4 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=6275 HTTP/1.1 | /api/events?id=6275 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 4 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 5 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%29%29%28.%29%27.%2C%22%29 HTTP/1.1 | /api/events?id=1%29%29%28.%29%27.%2C%22%29 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 5 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 6 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%27PDjlVW%3C%27%22%3EYGheEx HTTP/1.1 | /api/events?id=1%27PDjlVW%3C%27%22%3EYGheEx | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 212 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 213 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%29%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 213 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 214 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%29%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%29%29%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 214 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 215 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 215 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 216 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%27%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%27%29%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 216 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 217 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%27%29%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%27%29%29%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 217 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 218 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%27%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%27%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 218 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 219 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%25%27%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%25%27%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 219 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 220 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%22%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%22%29%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 220 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 221 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%22%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%22%3BSELECT%20SLEEP%285%29%23 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 271 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 272 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%20AND%20SLEEP%285%29 HTTP/1.1 | /api/events?id=1%20AND%20SLEEP%285%29 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 272 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 273 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%20AND%20SLEEP%285%29--%20PwHB HTTP/1.1 | /api/events?id=1%20AND%20SLEEP%285%29--%20PwHB | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 273 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 274 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%27%29%20AND%20SLEEP%285%29%20AND%20%28%27nxfW%27%3D%27nxfW HTTP/1.1 | /api/events?id=1%27%29%20AND%20SLEEP%285%29%20AND%20%28%27nxfW%27%3D%27nxfW | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 274 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 275 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%27%29%29%20AND%20SLEEP%285%29%20AND%20%28%28%27eTAr%27%3D%27eTAr HTTP/1.1 | /api/events?id=1%27%29%29%20AND%20SLEEP%285%29%20AND%20%28%28%27eTAr%27%3D%27eTAr | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 275 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 276 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%27%20AND%20SLEEP%285%29%20AND%20%27HGmK%27%3D%27HGmK HTTP/1.1 | /api/events?id=1%27%20AND%20SLEEP%285%29%20AND%20%27HGmK%27%3D%27HGmK | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 276 | nginx/collected/nginx01_batch_sqlmap_sqli_001.log | 277 | 172.22.0.1 | 2026-08-06T14:15:49+00:00 | GET /api/events?id=1%27%29%20AND%20SLEEP%285%29%20AND%20%28%27qSGP%27%20LIKE%20%27qSGP HTTP/1.1 | /api/events?id=1%27%29%20AND%20SLEEP%285%29%20AND%20%28%27qSGP%27%20LIKE%20%27qSGP | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |

...還有 82 筆，明細見 JSON 輸出的 `defining_violations`

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `os_type` | 0.0000 | 0.12 | 0, 1, 2, 3, 4, 5, 6 |
| `ua_length` | 0.0000 | — | — |
| `url_length` | 0.5879 | — | — |
| `url_special_chars` | 0.6453 | — | — |
| `url_param_count` | 0.0000 | — | — |
| `request_method` | 0.0000 | 0.12 | DELETE, HEAD, OPTIONS, PATCH, POST, PUT, TRACE |
| `url_encoding_count` | 0.6453 | — | — |
