對照規格 §3.1 的 12 個 stage，目前正式可用資料已改為非 PowerShell scripted attack-like batches。

| Log | 對應 stage | 狀態 |
|---|---|---|
| `collected/nginx01_batch_sqli_sqlmap_randomua_002.log` | stage 2 SQLi | 保留，sqlmap 工具真打 backend |
| `collected/nginx01_batch_xss_zap_fullscan_001.log` | stage 3 XSS | 保留，OWASP ZAP full scan 工具真打 backend |
| `collected/nginx01_batch_command_injection_commix_001.log` | stage 5 Command Injection | 保留，commix 工具真打 backend |
| `LFI_method_record/access3_Local_file_inclusion_1.log` | stage 6 LFI | 保留 |
| `LFI_method_record/access4_Local_file_inclusion_2_wfuzz.log` | stage 6 LFI | 保留 |
| `LFI_method_record/access5_Local_file_inclusion_3_wfuzz.log` | stage 6 LFI | 保留 |

仍待補齊：stage 4、7、8、9、10、11、12。現有工具批次仍需在後續用多批次方式補強 IP / time / UA diversity。
