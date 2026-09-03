# Stage 9 多元度驗收報告 — 特殊字元密集

- 樣本數：150（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）
- **Diversity_stage = 0.2742**

## Warnings

- ⚠️ stage 9: 150/150 筆樣本不符合定義判準 [{'feature': 'has_xss', 'op': 'eq', 'value': 1}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations）
- ⚠️ stage 9: config.SPECIAL_CHARS_DENSE_THRESHOLD 尚未由團隊拍板，目前定義判準只驗證 has_xss==1，未驗 url_special_chars 密集門檻
- ⚠️ stage 9: n_samples=150 < MIN_SAMPLES=200，熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 1 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%7Ccat%20%2Fetc%2Fpasswd%3B%26%26id%3B%24%28whoami%29 HTTP/1.1 | /api/events?keyword=%7Ccat%20%2Fetc%2Fpasswd%3B%26%26id%3B%24%28whoami%29 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 1 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 2 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Csvg%2Fonload%3Dalert%281%29%3E%27%22%3B%28%29%5B%5D HTTP/1.1 | /api/events?keyword=%3Csvg%2Fonload%3Dalert%281%29%3E%27%22%3B%28%29%5B%5D | GET | Fuzz Faster U Fool v2.1.0-dev |
| 2 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 3 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3B%7C%26%26%24%28id%29%60whoami%60%3C%3E%27%22 HTTP/1.1 | /api/events?keyword=%3B%7C%26%26%24%28id%29%60whoami%60%3C%3E%27%22 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 3 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 4 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3C%3E%27%22%3B%25%28%29%5B%5D%7B%7D HTTP/1.1 | /api/events?keyword=%3C%3E%27%22%3B%25%28%29%5B%5D%7B%7D | GET | Fuzz Faster U Fool v2.1.0-dev |
| 4 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 5 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Cmarquee%20onstart%3Dalert%281%29%3E%27%22%3B%25 HTTP/1.1 | /api/events?keyword=%3Cmarquee%20onstart%3Dalert%281%29%3E%27%22%3B%25 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 5 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 6 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%27%22%3E%3Cscript%3Ealert%281%29%3C%2Fscript%3E%3B%25 HTTP/1.1 | /api/events?keyword=%27%22%3E%3Cscript%3Ealert%281%29%3C%2Fscript%3E%3B%25 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 6 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 7 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Bping%20-c%201%20127.0.0.1%3B%7C%26%26%60id%60 HTTP/1.1 | /api/events?keyword=%3Bping%20-c%201%20127.0.0.1%3B%7C%26%26%60id%60 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 7 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 8 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Cbody%20onload%3Dalert%281%29%3E%27%22%3B%25%28%29 HTTP/1.1 | /api/events?keyword=%3Cbody%20onload%3Dalert%281%29%3E%27%22%3B%25%28%29 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 8 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 9 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Cinput%20autofocus%20onfocus%3Dalert%281%29%3E%27%22 HTTP/1.1 | /api/events?keyword=%3Cinput%20autofocus%20onfocus%3Dalert%281%29%3E%27%22 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 9 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 10 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%22%27%3Cimg%20src%3Dx%20onerror%3Dalert%281%29%3E%3B%25%7B%7D HTTP/1.1 | /api/events?keyword=%22%27%3Cimg%20src%3Dx%20onerror%3Dalert%281%29%3E%3B%25%7B%7D | GET | Fuzz Faster U Fool v2.1.0-dev |
| 10 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 11 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%5B%5D%7B%7D%28%29%3C%3E%27%22%3B%3A%2C.%2F%5C%7C%25 HTTP/1.1 | /api/events?keyword=%5B%5D%7B%7D%28%29%3C%3E%27%22%3B%3A%2C.%2F%5C%7C%25 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 11 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 12 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%24%7Bjndi%3Aldap%3A%2F%2F127.0.0.1%2Fa%7D%3C%3E%27%22 HTTP/1.1 | /api/events?keyword=%24%7Bjndi%3Aldap%3A%2F%2F127.0.0.1%2Fa%7D%3C%3E%27%22 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 12 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 13 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%27%22%60%3C%3E%3B%7C%26%24%28%29%5B%5D%7B%7D%25%23%40 HTTP/1.1 | /api/events?keyword=%27%22%60%3C%3E%3B%7C%26%24%28%29%5B%5D%7B%7D%25%23%40 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 13 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 14 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%7B%7B7*7%7D%7D%24%7B7*7%7D%3C%25%3D7*7%25%3E HTTP/1.1 | /api/events?keyword=%7B%7B7*7%7D%7D%24%7B7*7%7D%3C%25%3D7*7%25%3E | GET | Fuzz Faster U Fool v2.1.0-dev |
| 14 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 15 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Cmath%3E%3Cmtext%3E%3C%2Fmtext%3E%3Cscript%3Ealert%281%29%3C%2Fscript%3E HTTP/1.1 | /api/events?keyword=%3Cmath%3E%3Cmtext%3E%3C%2Fmtext%3E%3Cscript%3Ealert%281%29%3C%2Fscript%3E | GET | Fuzz Faster U Fool v2.1.0-dev |
| 15 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 16 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Cscript%3Econfirm%28document.domain%29%3C%2Fscript%3E%27%22 HTTP/1.1 | /api/events?keyword=%3Cscript%3Econfirm%28document.domain%29%3C%2Fscript%3E%27%22 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 16 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 17 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=..%5C..%5Cwindows%5Cwin.ini%00%3C%3E%27%22%3B%25 HTTP/1.1 | /api/events?keyword=..%5C..%5Cwindows%5Cwin.ini%00%3C%3E%27%22%3B%25 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 17 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 18 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Cscript%3Ealert%281%29%3C%2Fscript%3E%27%22%3B%25%28%29 HTTP/1.1 | /api/events?keyword=%3Cscript%3Ealert%281%29%3C%2Fscript%3E%27%22%3B%25%28%29 | GET | Fuzz Faster U Fool v2.1.0-dev |
| 18 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 19 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3C%25%20Runtime.getRuntime%28%29.exec%28%27id%27%29%20%25%3E HTTP/1.1 | /api/events?keyword=%3C%25%20Runtime.getRuntime%28%29.exec%28%27id%27%29%20%25%3E | GET | Fuzz Faster U Fool v2.1.0-dev |
| 19 | nginx/collected/nginx01_batch_special_chars_dense_ffuf_001.log | 20 | 10.77.9.21 | 2026-09-01T06:21:10+00:00 | GET /api/events?keyword=%3Cdetails%20open%20ontoggle%3Dalert%281%29%3E%27%22%3B HTTP/1.1 | /api/events?keyword=%3Cdetails%20open%20ontoggle%3Dalert%281%29%3E%27%22%3B | GET | Fuzz Faster U Fool v2.1.0-dev |

...還有 130 筆，明細見 JSON 輸出的 `defining_violations`

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_length` | 0.0621 | — | — |
| `os_type` | 0.6406 | 0.50 | 0, 1, 2, 6 |
| `url_encoding_count` | 0.1200 | — | — |
