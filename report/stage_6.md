# Stage 6 多元度驗收報告 — 檔案包含

- 樣本數：22（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）
- **Diversity_stage = 0.3304**

## Warnings

- ⚠️ stage 6: 16/22 筆樣本不符合定義判準 [{'feature': 'has_file_inclusion', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations）
- ⚠️ stage 6: n_samples=22 < MIN_SAMPLES=200，熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻
- ⚠️ stage 6: 支撐特徵 'os_type' 完全塌縮（d=0）
- ⚠️ stage 6: 支撐特徵 'ua_length' 完全塌縮（d=0）
- ⚠️ stage 6: 支撐特徵 'url_encoding_count' 完全塌縮（d=0）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 1 | 172.20.0.1 | 2026-08-26T03:09:00+00:00 | GET /api/events/1/attachment?file=poster.txt HTTP/1.1 | /api/events/1/attachment?file=poster.txt | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 1 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 2 | 172.20.0.1 | 2026-08-26T03:14:40+00:00 | GET /api/events/1/attachment?file=../../etc/passwd HTTP/1.1 | /api/events/1/attachment?file=../../etc/passwd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 2 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 3 | 172.20.0.1 | 2026-08-26T03:17:15+00:00 | GET /api/events/1/attachment?file=..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%2F..%2Fetc%2Fpasswd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 3 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 4 | 172.20.0.1 | 2026-08-26T03:17:15+00:00 | GET /api/events/1/attachment?file=..%2F..%2Fetc%2Fpasswd HTTP/1.1 | /api/events/1/attachment?file=..%2F..%2Fetc%2Fpasswd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 4 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 5 | 172.20.0.1 | 2026-08-26T03:20:41+00:00 | GET /api/events/1/attachment?file=..%5C..%5Cwindows%5Cwin.ini HTTP/1.1 | /api/events/1/attachment?file=..%5C..%5Cwindows%5Cwin.ini | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 5 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 6 | 172.20.0.1 | 2026-08-26T03:20:47+00:00 | GET /api/events/1/attachment?file=..%5C..%5Cwindows%5Cwin.ini HTTP/1.1 | /api/events/1/attachment?file=..%5C..%5Cwindows%5Cwin.ini | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 6 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 7 | 172.20.0.1 | 2026-08-26T03:21:03+00:00 | GET /api/events/1/attachment?file=..%5C..%5Cwindows%5Cwin.ini HTTP/1.1 | /api/events/1/attachment?file=..%5C..%5Cwindows%5Cwin.ini | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 7 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 8 | 172.20.0.1 | 2026-08-26T03:21:17+00:00 | GET /api/events/1/attachment?file=../../etc/passwd HTTP/1.1 | /api/events/1/attachment?file=../../etc/passwd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 8 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 9 | 172.20.0.1 | 2026-08-26T03:21:27+00:00 | GET /api/events/1/attachment?file=../../etc/passwd HTTP/1.1 | /api/events/1/attachment?file=../../etc/passwd | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 10 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 11 | 172.20.0.1 | 2026-08-26T03:21:45+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 12 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 13 | 172.20.0.1 | 2026-08-26T03:23:38+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 14 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 15 | 172.20.0.1 | 2026-08-26T03:23:43+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 16 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 17 | 172.20.0.1 | 2026-08-26T03:23:44+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 18 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 19 | 172.20.0.1 | 2026-08-26T03:24:05+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 20 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 21 | 172.20.0.1 | 2026-08-26T03:24:46+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 21 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 22 | 172.20.0.1 | 2026-08-26T03:55:44+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_length` | 0.6522 | — | — |
| `url_special_chars` | 1.0000 | — | — |
| `os_type` | 0.0000 | 0.12 | 0, 2, 3, 4, 5, 6, 7 |
| `ua_length` | 0.0000 | — | — |
| `url_encoding_count` | 0.0000 | — | — |
