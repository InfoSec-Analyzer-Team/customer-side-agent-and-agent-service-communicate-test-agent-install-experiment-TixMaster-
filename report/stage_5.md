# Stage 5 多元度驗收報告 — 命令注入

- 樣本數：1786
- **Diversity_stage = 0.0436**

## Warnings

- ⚠️ stage 5: 1783/1786 筆樣本不符合定義判準 [{'feature': 'has_command_injection', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations，只列前 500 筆，真實總數見 defining_violations_total）
- ⚠️ stage 5: 支撐特徵 'url_param_count' 的 QCD=0，但實際有 2 種取值（不是真塌縮，是低基數或尾部集中分布讓 Q1=Q3——見 §2.3 QCD 已知限制，strict 門檻的「塌縮數」不該把這種情況算進去）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 1 | 172.17.0.1 | 2026-08-30T16:03:56+00:00 | GET /api/events?keyword=test HTTP/1.1 | /api/events?keyword=test | GET | commix/v4.1 (https://commixproject.com) |
| 1 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 2 | 172.17.0.1 | 2026-08-30T16:03:56+00:00 | GET /api/events?keyword=test HTTP/1.1 | /api/events?keyword=test | GET | commix/v4.1 (https://commixproject.com) |
| 2 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 3 | 172.17.0.1 | 2026-08-30T16:03:56+00:00 | GET /api/events?keyword=test HTTP/1.1 | /api/events?keyword=test | GET | commix/v4.1 (https://commixproject.com) |
| 3 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 4 | 172.17.0.1 | 2026-08-30T16:03:56+00:00 | GET /api/events?keyword=test HTTP/1.1 | /api/events?keyword=test | GET | commix/v4.1 (https://commixproject.com) |
| 7 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 8 | 172.17.0.1 | 2026-08-30T16:03:56+00:00 | GET /api/events?keyword=test HTTP/1.1 | /api/events?keyword=test | GET | Python-urllib/3.14 |
| 8 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 9 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test HTTP/1.1 | /api/events?keyword=test | GET | Python-urllib/3.14 |
| 9 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 10 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test HTTP/1.1 | /api/events?keyword=test | GET | commix/v4.1 (https://commixproject.com) |
| 10 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 11 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test%3Becho%20%24%28%285308%20%2B%205139%29%29%26echo%20%24%28%285308%20%2B%205139%29%29%7Cecho%20%24%28%285308%20%2B%205139%29%29test HTTP/1.1 | /api/events?keyword=test%3Becho%20%24%28%285308%20%2B%205139%29%29%26echo%20%24%28%285308%20%2B%205139%29%29%7Cecho%20%24%28%285308%20%2B%205139%29%29test | GET | commix/v4.1 (https://commixproject.com) |
| 11 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 12 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test%3Becho%20%24%28%285308%20%2B%205139%29%29%26echo%20%24%28%285308%20%2B%205139%29%29%7Cecho%20%24%28%285308%20%2B%205139%29%29test HTTP/1.1 | /api/events?keyword=test%3Becho%20%24%28%285308%20%2B%205139%29%29%26echo%20%24%28%285308%20%2B%205139%29%29%7Cecho%20%24%28%285308%20%2B%205139%29%29test | GET | commix/v4.1 (https://commixproject.com) |
| 12 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 13 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test%3Becho%20%24%28%285308%20%2B%205139%29%29%26echo%20%24%28%285308%20%2B%205139%29%29%7Cecho%20%24%28%285308%20%2B%205139%29%29test HTTP/1.1 | /api/events?keyword=test%3Becho%20%24%28%285308%20%2B%205139%29%29%26echo%20%24%28%285308%20%2B%205139%29%29%7Cecho%20%24%28%285308%20%2B%205139%29%29test | GET | commix/v4.1 (https://commixproject.com) |
| 13 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 14 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test%7Cset%20/a%20%285308%20%2B%205139%29%26set%20/a%20%285308%20%2B%205139%29 HTTP/1.1 | /api/events?keyword=test%7Cset%20/a%20%285308%20%2B%205139%29%26set%20/a%20%285308%20%2B%205139%29 | GET | commix/v4.1 (https://commixproject.com) |
| 14 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 15 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test%7Cset%20/a%20%285308%20%2B%205139%29%26set%20/a%20%285308%20%2B%205139%29 HTTP/1.1 | /api/events?keyword=test%7Cset%20/a%20%285308%20%2B%205139%29%26set%20/a%20%285308%20%2B%205139%29 | GET | commix/v4.1 (https://commixproject.com) |
| 15 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 16 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test%7Cset%20/a%20%285308%20%2B%205139%29%26set%20/a%20%285308%20%2B%205139%29 HTTP/1.1 | /api/events?keyword=test%7Cset%20/a%20%285308%20%2B%205139%29%26set%20/a%20%285308%20%2B%205139%29 | GET | commix/v4.1 (https://commixproject.com) |
| 16 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 17 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test.print%28phpinfo%28%29%29 HTTP/1.1 | /api/events?keyword=test.print%28phpinfo%28%29%29 | GET | commix/v4.1 (https://commixproject.com) |
| 17 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 18 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test.print%28phpinfo%28%29%29 HTTP/1.1 | /api/events?keyword=test.print%28phpinfo%28%29%29 | GET | commix/v4.1 (https://commixproject.com) |
| 18 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 19 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test.print%28phpinfo%28%29%29 HTTP/1.1 | /api/events?keyword=test.print%28phpinfo%28%29%29 | GET | commix/v4.1 (https://commixproject.com) |
| 19 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 20 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test.print%28exec%28phpinfo%28%29%29%29 HTTP/1.1 | /api/events?keyword=test.print%28exec%28phpinfo%28%29%29%29 | GET | commix/v4.1 (https://commixproject.com) |
| 20 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 21 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test.print%28exec%28phpinfo%28%29%29%29 HTTP/1.1 | /api/events?keyword=test.print%28exec%28phpinfo%28%29%29%29 | GET | commix/v4.1 (https://commixproject.com) |
| 21 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 22 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test.print%28exec%28phpinfo%28%29%29%29 HTTP/1.1 | /api/events?keyword=test.print%28exec%28phpinfo%28%29%29%29 | GET | commix/v4.1 (https://commixproject.com) |
| 22 | nginx/collected/nginx01_batch_command_injection_commix_001.log | 23 | 172.17.0.1 | 2026-08-30T16:04:01+00:00 | GET /api/events?keyword=test.print%28eval%28phpinfo%28%29%29%29 HTTP/1.1 | /api/events?keyword=test.print%28eval%28phpinfo%28%29%29%29 | GET | commix/v4.1 (https://commixproject.com) |

...還有 1763 筆，明細見 JSON 輸出的 `defining_violations`（JSON 也有截斷，見 config.MAX_DEFINING_VIOLATIONS）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_length` | 0.0213 | — | — |
| `url_special_chars` | 0.0370 | — | — |
| `os_type` | 0.1184 | 0.25 | 0, 1, 2, 3, 5, 6 |
| `request_method` | 0.0410 | 0.25 | DELETE, HEAD, OPTIONS, PATCH, PUT, TRACE |
| `url_param_count` | 0.0000 | — | — |
