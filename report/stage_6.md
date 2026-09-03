# Stage 6 多元度驗收報告 — 檔案包含

- 樣本數：974
- **Diversity_stage = 0.0454**

## Warnings

- ⚠️ stage 6: 926/974 筆樣本不符合定義判準 [{'any': [{'feature': 'has_file_inclusion', 'op': 'eq', 'value': 1, 'exclude_from_support': True}, {'feature': 'has_path_traversal', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]}]，可能混入其他 stage 的樣本，或定義判準本身設錯（明細見 StageDiversityReport.defining_violations，只列前 500 筆，真實總數見 defining_violations_total）
- ⚠️ stage 6: 支撐特徵 'url_special_chars' 的 QCD=0，但實際有 6 種取值（不是真塌縮，是低基數或尾部集中分布讓 Q1=Q3——見 §2.3 QCD 已知限制，strict 門檻的「塌縮數」不該把這種情況算進去）
- ⚠️ stage 6: 支撐特徵 'url_encoding_count' 的 QCD=0，但實際有 5 種取值（不是真塌縮，是低基數或尾部集中分布讓 Q1=Q3——見 §2.3 QCD 已知限制，strict 門檻的「塌縮數」不該把這種情況算進去）

## 不符合定義判準的樣本

| index | log_source | log_line_no | ip | datetime | request | url | request_method | browser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 1 | 172.20.0.1 | 2026-08-26T03:09:00+00:00 | GET /api/events/1/attachment?file=poster.txt HTTP/1.1 | /api/events/1/attachment?file=poster.txt | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 10 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 11 | 172.20.0.1 | 2026-08-26T03:21:45+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 12 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 13 | 172.20.0.1 | 2026-08-26T03:23:38+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 14 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 15 | 172.20.0.1 | 2026-08-26T03:23:43+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 16 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 17 | 172.20.0.1 | 2026-08-26T03:23:44+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 18 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 19 | 172.20.0.1 | 2026-08-26T03:24:05+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 20 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 21 | 172.20.0.1 | 2026-08-26T03:24:46+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 21 | nginx/LFI_method_record/access3_Local_file_inclusion_1.log | 22 | 172.20.0.1 | 2026-08-26T03:55:44+00:00 | GET /favicon.ico HTTP/1.1 | /favicon.ico | GET | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 |
| 22 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 1 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/aliases HTTP/1.1 | /api/events/1/attachment?file=/etc/aliases | GET | Wfuzz/3.1.0 |
| 23 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 2 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/apache2/httpd.conf HTTP/1.1 | /api/events/1/attachment?file=/etc/apache2/httpd.conf | GET | Wfuzz/3.1.0 |
| 24 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 3 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/passwd HTTP/1.1 | /api/events/1/attachment?file=/etc/passwd | GET | Wfuzz/3.1.0 |
| 25 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 4 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/my.cnf HTTP/1.1 | /api/events/1/attachment?file=/etc/my.cnf | GET | Wfuzz/3.1.0 |
| 26 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 5 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/modules.conf HTTP/1.1 | /api/events/1/attachment?file=/etc/modules.conf | GET | Wfuzz/3.1.0 |
| 27 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 6 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/httpd/logs/access_log HTTP/1.1 | /api/events/1/attachment?file=/etc/httpd/logs/access_log | GET | Wfuzz/3.1.0 |
| 28 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 7 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/lilo.conf HTTP/1.1 | /api/events/1/attachment?file=/etc/lilo.conf | GET | Wfuzz/3.1.0 |
| 29 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 8 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/logrotate.d/vsftpd.log HTTP/1.1 | /api/events/1/attachment?file=/etc/logrotate.d/vsftpd.log | GET | Wfuzz/3.1.0 |
| 30 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 9 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/lsb-release HTTP/1.1 | /api/events/1/attachment?file=/etc/lsb-release | GET | Wfuzz/3.1.0 |
| 31 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 10 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/logrotate.d/proftpd HTTP/1.1 | /api/events/1/attachment?file=/etc/logrotate.d/proftpd | GET | Wfuzz/3.1.0 |
| 32 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 11 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/lighttpd.conf HTTP/1.1 | /api/events/1/attachment?file=/etc/lighttpd.conf | GET | Wfuzz/3.1.0 |
| 33 | nginx/LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log | 12 | 172.20.0.1 | 2026-08-26T04:32:11+00:00 | GET /api/events/1/attachment?file=/etc/logrotate.d/ftp HTTP/1.1 | /api/events/1/attachment?file=/etc/logrotate.d/ftp | GET | Wfuzz/3.1.0 |

...還有 906 筆，明細見 JSON 輸出的 `defining_violations`（JSON 也有截斷，見 config.MAX_DEFINING_VIOLATIONS）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_length` | 0.1296 | — | — |
| `url_special_chars` | 0.0000 | — | — |
| `os_type` | 0.0519 | 0.25 | 0, 2, 3, 4, 5, 6 |
| `url_encoding_count` | 0.0000 | — | — |
