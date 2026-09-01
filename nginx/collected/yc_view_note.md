對照規格 §3.1 的 12 個 stage，目前正式可用資料已改為非 PowerShell scripted attack-like batches。

| Log | 對應 stage | 狀態 |
|---|---|---|
| `collected/nginx01_batch_sqli_sqlmap_randomua_002.log` | stage 2 SQLi | 保留，sqlmap 工具真打 backend |
| `collected/nginx01_batch_xss_zap_fullscan_001.log` | stage 3 XSS | 保留，OWASP ZAP full scan 工具真打 backend |
| `collected/nginx01_batch_path_traversal_ffuf_002.log` | stage 4 Path Traversal | 保留，ffuf 工具真打 attachment sink |
| `collected/nginx01_batch_double_encoding_ffuf_002.log` | stage 7 Double Encoding | 保留，ffuf 工具真打 attachment sink |
| `collected/nginx01_batch_url_encoding_count_ffuf_001.log` | stage 8 URL Encoding Count | 保留，ffuf 工具真打 backend search endpoint |
| `collected/nginx01_batch_special_chars_dense_ffuf_001.log` | stage 9 Special Chars Dense | 保留，ffuf 工具真打 backend search endpoint |
| `collected/nginx01_batch_scanner_ua_gobuster_005.log` | stage 10 Scanner UA | 保留，gobuster 工具真打 lab target |
| `collected/nginx01_batch_abnormal_methods_ffuf_002.log` | stage 11 Abnormal Methods | 保留，ffuf 工具真打 common paths |
| `collected/nginx01_batch_abnormal_url_ffuf_001.log` | stage 12 Abnormal URL | 保留，ffuf 工具真打 abnormal URL structures |
| `collected/nginx01_batch_command_injection_commix_001.log` | stage 5 Command Injection | 保留，commix 工具真打 backend |
| `LFI_method_record/access3_Local_file_inclusion_1.log` | stage 6 LFI | 保留 |
| `LFI_method_record/access4_Local_file_inclusion_2_wfuzz.log` | stage 6 LFI | 保留 |
| `LFI_method_record/access5_Local_file_inclusion_3_wfuzz.log` | stage 6 LFI | 保留 |

12 個 stage 目前都有對應資料。現有工具批次仍需在後續用多批次方式補強 IP / time / UA diversity。






