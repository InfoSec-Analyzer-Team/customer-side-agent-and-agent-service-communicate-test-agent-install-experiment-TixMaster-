# Stage 2 多元度驗收報告 — SQLi

- 樣本數：378
- **Diversity_stage = 0.2684**

## Warnings

- ⚠️ stage 2: 259/378 筆樣本不符合定義判準 [{'feature': 'has_sql_injection', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations）
- ⚠️ stage 2: 支撐特徵 'os_type' 完全塌縮（d=0）
- ⚠️ stage 2: 支撐特徵 'ua_length' 完全塌縮（d=0）
- ⚠️ stage 2: 支撐特徵 'url_param_count' 完全塌縮（d=0）
- ⚠️ stage 2: 支撐特徵 'request_method' 完全塌縮（d=0）

## 不符合定義判準的樣本

| index | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 172.22.0.1 | 2026-08-06T14:15:45+00:00 | GET /api/events?id=1 HTTP/1.1 | /api/events?id=1 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 2 | 3 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1 HTTP/1.1 | /api/events?id=1 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 3 | 4 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=6275 HTTP/1.1 | /api/events?id=6275 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 4 | 5 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%29%29%28.%29%27.%2C%22%29 HTTP/1.1 | /api/events?id=1%29%29%28.%29%27.%2C%22%29 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 5 | 6 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%27PDjlVW%3C%27%22%3EYGheEx HTTP/1.1 | /api/events?id=1%27PDjlVW%3C%27%22%3EYGheEx | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 6 | 7 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%29%20AND%207973%3D2007%20AND%20%288113%3D8113 HTTP/1.1 | /api/events?id=1%29%20AND%207973%3D2007%20AND%20%288113%3D8113 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 7 | 8 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%29%29%20AND%209588%3D7570%20AND%20%28%285328%3D5328 HTTP/1.1 | /api/events?id=1%29%29%20AND%209588%3D7570%20AND%20%28%285328%3D5328 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 8 | 9 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%20AND%207110%3D9042 HTTP/1.1 | /api/events?id=1%20AND%207110%3D9042 | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 9 | 10 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%20AND%206218%3D3524--%20hJSL HTTP/1.1 | /api/events?id=1%20AND%206218%3D3524--%20hJSL | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 10 | 11 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%27%29%20AND%204947%3D9521%20AND%20%28%27IwIp%27%3D%27IwIp HTTP/1.1 | /api/events?id=1%27%29%20AND%204947%3D9521%20AND%20%28%27IwIp%27%3D%27IwIp | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 11 | 12 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%27%29%29%20AND%201399%3D2063%20AND%20%28%28%27vXKC%27%3D%27vXKC HTTP/1.1 | /api/events?id=1%27%29%29%20AND%201399%3D2063%20AND%20%28%28%27vXKC%27%3D%27vXKC | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 12 | 13 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%27%20AND%205206%3D9476%20AND%20%27KyHp%27%3D%27KyHp HTTP/1.1 | /api/events?id=1%27%20AND%205206%3D9476%20AND%20%27KyHp%27%3D%27KyHp | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 13 | 14 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%27%29%20AND%204845%3D1847%20AND%20%28%27sFOb%27%20LIKE%20%27sFOb HTTP/1.1 | /api/events?id=1%27%29%20AND%204845%3D1847%20AND%20%28%27sFOb%27%20LIKE%20%27sFOb | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 14 | 15 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%25%27%20AND%205678%3D4103%20AND%20%27BIsQ%25%27%3D%27BIsQ HTTP/1.1 | /api/events?id=1%25%27%20AND%205678%3D4103%20AND%20%27BIsQ%25%27%3D%27BIsQ | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 15 | 16 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%27%20AND%207114%3D9249%20AND%20%27TEjT%27%20LIKE%20%27TEjT HTTP/1.1 | /api/events?id=1%27%20AND%207114%3D9249%20AND%20%27TEjT%27%20LIKE%20%27TEjT | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 16 | 17 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%22%29%20AND%206118%3D5908%20AND%20%28%22HdVL%22%3D%22HdVL HTTP/1.1 | /api/events?id=1%22%29%20AND%206118%3D5908%20AND%20%28%22HdVL%22%3D%22HdVL | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 17 | 18 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%22%20AND%208392%3D9563%20AND%20%22LLVv%22%3D%22LLVv HTTP/1.1 | /api/events?id=1%22%20AND%208392%3D9563%20AND%20%22LLVv%22%3D%22LLVv | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 27 | 28 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%29%20AND%206750%3D8207--%20DNJF HTTP/1.1 | /api/events?id=1%29%20AND%206750%3D8207--%20DNJF | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 28 | 29 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%29%29%20AND%203489%3D3534--%20yJRZ HTTP/1.1 | /api/events?id=1%29%29%20AND%203489%3D3534--%20yJRZ | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |
| 29 | 30 | 172.22.0.1 | 2026-08-06T14:15:46+00:00 | GET /api/events?id=1%27%29%20AND%208708%3D6423--%20jrQW HTTP/1.1 | /api/events?id=1%27%29%20AND%208708%3D6423--%20jrQW | GET | sqlmap/1.10.4#stable (https://sqlmap.org) |

...還有 239 筆，完整明細見 JSON 輸出的 `defining_violations`

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
