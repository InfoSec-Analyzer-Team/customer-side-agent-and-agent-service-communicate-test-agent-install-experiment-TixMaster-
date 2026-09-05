# Stage 3 多元度驗收報告 — XSS

- 樣本數：907
- **Diversity_stage = 0.3363**

## Warnings

- ⚠️ stage 3: 907/907 筆樣本不符合定義判準 [{'feature': 'has_xss', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations，只列前 500 筆，真實總數見 defining_violations_total）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 1 | 172.17.0.1 | 2026-08-30T15:41:23+00:00 | GET / HTTP/1.1 | / | GET | python-requests/2.34.2 |
| 1 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 2 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET / HTTP/1.1 | / | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 2 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 3 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET / HTTP/1.1 | / | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 3 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 4 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET /sitemap.xml HTTP/1.1 | /sitemap.xml | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 4 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 5 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET /robots.txt HTTP/1.1 | /robots.txt | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 5 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 6 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET /login.html HTTP/1.1 | /login.html | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 6 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 7 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET /index.html HTTP/1.1 | /index.html | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 7 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 8 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET /$%7Bevent.image%7D HTTP/1.1 | /$%7Bevent.image%7D | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 8 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 9 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET /register.html HTTP/1.1 | /register.html | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 9 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 10 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET /register.html?confirmPassword=ZAP&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 HTTP/1.1 | /register.html?confirmPassword=ZAP&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 10 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 11 | 172.17.0.1 | 2026-08-30T15:41:25+00:00 | GET /login.html?email=zaproxy%40example.com&password=ZAP HTTP/1.1 | /login.html?email=zaproxy%40example.com&password=ZAP | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 11 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 12 | 172.17.0.1 | 2026-08-30T15:41:30+00:00 | GET /5646181195926579176 HTTP/1.1 | /5646181195926579176 | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 12 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 13 | 172.17.0.1 | 2026-08-30T15:41:30+00:00 | GET /733547859182095375 HTTP/1.1 | /733547859182095375 | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 13 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 14 | 172.17.0.1 | 2026-08-30T15:41:30+00:00 | GET /register.html?confirmPassword=c%3A%2FWindows%2Fsystem.ini&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 HTTP/1.1 | /register.html?confirmPassword=c%3A%2FWindows%2Fsystem.ini&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 14 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 15 | 172.17.0.1 | 2026-08-30T15:41:30+00:00 | GET /login.html?email=c%3A%2FWindows%2Fsystem.ini&password=ZAP HTTP/1.1 | /login.html?email=c%3A%2FWindows%2Fsystem.ini&password=ZAP | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 15 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 16 | 172.17.0.1 | 2026-08-30T15:41:30+00:00 | GET /login.html?email=..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2FWindows%2Fsystem.ini&password=ZAP HTTP/1.1 | /login.html?email=..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2FWindows%2Fsystem.ini&password=ZAP | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 16 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 17 | 172.17.0.1 | 2026-08-30T15:41:30+00:00 | GET /register.html?confirmPassword=..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2FWindows%2Fsystem.ini&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 HTTP/1.1 | /register.html?confirmPassword=..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2FWindows%2Fsystem.ini&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 17 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 18 | 172.17.0.1 | 2026-08-30T15:41:31+00:00 | GET /login.html?email=c%3A%5CWindows%5Csystem.ini&password=ZAP HTTP/1.1 | /login.html?email=c%3A%5CWindows%5Csystem.ini&password=ZAP | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 18 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 19 | 172.17.0.1 | 2026-08-30T15:41:31+00:00 | GET /register.html?confirmPassword=c%3A%5CWindows%5Csystem.ini&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 HTTP/1.1 | /register.html?confirmPassword=c%3A%5CWindows%5Csystem.ini&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |
| 19 | nginx/collected/nginx01_batch_xss_zap_fullscan_clean_001.log | 20 | 172.17.0.1 | 2026-08-30T15:41:31+00:00 | GET /register.html?confirmPassword=..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5CWindows%5Csystem.ini&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 HTTP/1.1 | /register.html?confirmPassword=..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5C..%5CWindows%5Csystem.ini&email=zaproxy%40example.com&name=ZAP&password=ZAP&phone=9999999999 | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 |

...還有 887 筆，明細見 JSON 輸出的 `defining_violations`（JSON 也有截斷，見 config.MAX_DEFINING_VIOLATIONS）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_special_chars` | 0.6364 | — | — |
| `url_length` | 0.3019 | — | — |
| `url_encoding_count` | 0.6364 | — | — |
| `os_type` | 0.0041 | 0.25 | 0, 2, 3, 4, 5, 6 |
| `request_method` | 0.1026 | 0.25 | DELETE, HEAD, OPTIONS, PATCH, PUT, TRACE |
