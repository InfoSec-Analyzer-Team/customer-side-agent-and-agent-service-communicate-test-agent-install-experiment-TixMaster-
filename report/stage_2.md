# Stage 2 多元度驗收報告 — SQLi

- 樣本數：750
- **Diversity_stage = 0.4104**

## Warnings

- ⚠️ stage 2: 266/750 筆樣本不符合定義判準 [{'feature': 'has_sql_injection', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations）
- ⚠️ stage 2: 支撐特徵 'url_param_count' 的 QCD=0，但實際有 2 種取值（不是真塌縮，是低基數或尾部集中分布讓 Q1=Q3——見 §2.3 QCD 已知限制，strict 門檻的「塌縮數」不該把這種情況算進去）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 1 | 172.17.0.1 | 2026-08-30T13:59:24+00:00 | GET /api/events?id=1 HTTP/1.1 | /api/events?id=1 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 2 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 3 | 172.17.0.1 | 2026-08-30T13:59:24+00:00 | GET /api/events?id=1 HTTP/1.1 | /api/events?id=1 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 3 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 4 | 172.17.0.1 | 2026-08-30T13:59:24+00:00 | GET /api/events?id=3259 HTTP/1.1 | /api/events?id=3259 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 4 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 5 | 172.17.0.1 | 2026-08-30T13:59:24+00:00 | GET /api/events?id=1%29%22%29.%27%28%2C%28%29%28 HTTP/1.1 | /api/events?id=1%29%22%29.%27%28%2C%28%29%28 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 5 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 6 | 172.17.0.1 | 2026-08-30T13:59:24+00:00 | GET /api/events?id=1%27yDxHNI%3C%27%22%3EULJWaQ HTTP/1.1 | /api/events?id=1%27yDxHNI%3C%27%22%3EULJWaQ | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 212 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 213 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%29%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 213 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 214 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%29%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%29%29%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 214 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 215 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 215 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 216 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%27%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%27%29%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 216 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 217 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%27%29%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%27%29%29%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 217 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 218 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%27%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%27%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 218 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 219 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%25%27%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%25%27%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 219 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 220 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%22%29%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%22%29%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 220 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 221 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%22%3BSELECT%20SLEEP%285%29%23 HTTP/1.1 | /api/events?id=1%22%3BSELECT%20SLEEP%285%29%23 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 271 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 272 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%20AND%20SLEEP%285%29 HTTP/1.1 | /api/events?id=1%20AND%20SLEEP%285%29 | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 272 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 273 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%20AND%20SLEEP%285%29--%20rBwc HTTP/1.1 | /api/events?id=1%20AND%20SLEEP%285%29--%20rBwc | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 273 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 274 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%27%29%20AND%20SLEEP%285%29%20AND%20%28%27bVXQ%27%3D%27bVXQ HTTP/1.1 | /api/events?id=1%27%29%20AND%20SLEEP%285%29%20AND%20%28%27bVXQ%27%3D%27bVXQ | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 274 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 275 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%27%29%29%20AND%20SLEEP%285%29%20AND%20%28%28%27TZbv%27%3D%27TZbv HTTP/1.1 | /api/events?id=1%27%29%29%20AND%20SLEEP%285%29%20AND%20%28%28%27TZbv%27%3D%27TZbv | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 275 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 276 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%27%20AND%20SLEEP%285%29%20AND%20%27jZaf%27%3D%27jZaf HTTP/1.1 | /api/events?id=1%27%20AND%20SLEEP%285%29%20AND%20%27jZaf%27%3D%27jZaf | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |
| 276 | nginx/collected/nginx01_batch_sqli_sqlmap_randomua_002.log | 277 | 172.17.0.1 | 2026-08-30T13:59:26+00:00 | GET /api/events?id=1%27%29%20AND%20SLEEP%285%29%20AND%20%28%27wTsq%27%20LIKE%20%27wTsq HTTP/1.1 | /api/events?id=1%27%29%20AND%20SLEEP%285%29%20AND%20%28%27wTsq%27%20LIKE%20%27wTsq | GET | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 |

...還有 246 筆，明細見 JSON 輸出的 `defining_violations`

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `os_type` | 0.3333 | 0.25 | 0, 1, 2, 3, 6, 7 |
| `url_length` | 0.5768 | — | — |
| `url_special_chars` | 0.6571 | — | — |
| `url_param_count` | 0.0000 | — | — |
| `request_method` | 0.2380 | 0.25 | DELETE, HEAD, OPTIONS, PATCH, PUT, TRACE |
| `url_encoding_count` | 0.6571 | — | — |
