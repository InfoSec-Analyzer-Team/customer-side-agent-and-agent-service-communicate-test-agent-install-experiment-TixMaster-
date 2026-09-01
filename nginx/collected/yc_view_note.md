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







## IP/UA 補強批次

stage 4、7、8、9、10、11、12 已追加第二輪 IP/UA diversity logs。這些批次仍由 ffuf/gobuster 真打 Nginx/backend 產生，目的不是新增 stage，而是降低單一 Docker bridge IP 與固定工具 UA shortcut。

時間 diversity 尚未偽造；需在不同真實時間窗再收 round 003。

補充：stage 11/12 的第二輪已改用 clean-IP batch，避免 Nginx pre-header rejection 造成 Docker bridge IP / '-' UA。


## Night round 補強批次

stage 2、3、5 已追加真實晚上時段批次，沒有修改 timestamp。SQLi 使用 sqlmap random-agent；XSS 與 command injection 使用 ffuf payload wordlist 真打 Nginx/backend，補強時間、IP range 與 UA 分布。

## POST method 補強批次

針對「大多數攻擊 log 都是 GET」的問題，已追加 POST method diversity round。這批不是 PowerShell 偽造 request，也不是手寫 log；PowerShell 只負責切 batch，實際流量由 sqlmap/ffuf 打到本機 Nginx 後由 Nginx 產生 access.log。

由於目前 Nginx 使用 standard `combined` format，request body 不會寫入 access.log；若把 XSS/SQLi payload 放在 POST body，ML parser 其實看不到 payload。因此這輪採用 POST request + query payload，讓 log 同時保留 `POST` method 和攻擊特徵。

新增對應：

```text
stage 2  SQLi                 collected/nginx01_batch_sqli_sqlmap_postquery_night_005.log
stage 3  XSS                  collected/nginx01_batch_xss_ffuf_postquery_night_004.log
stage 4  Path Traversal       collected/nginx01_batch_path_traversal_ffuf_postquery_night_004.log
stage 5  Command Injection    collected/nginx01_batch_command_injection_ffuf_postquery_night_004.log
stage 7  Double Encoding      collected/nginx01_batch_double_encoding_ffuf_postquery_night_004.log
stage 8  URL Encoding Count   collected/nginx01_batch_url_encoding_count_ffuf_postquery_night_004.log
stage 9  Special Chars Dense  collected/nginx01_batch_special_chars_dense_ffuf_postquery_night_004.log
stage 12 Abnormal URL         collected/nginx01_batch_abnormal_url_ffuf_post_night_004.log
```

檢查結果：8 個新增檔案皆為 `bad_format=0`，且每個檔案 method count 都是 `POST`。stage 11 原本已經有 PUT/DELETE/OPTIONS/PATCH/HEAD，因此本輪主要補其他攻擊類別的 method diversity。

## stage 1 Nikto 補強

依 PR #5 的要求，stage 1 已改為合併：

```text
logs/access2_Dicurigai_sensitive_path.log
collected/nginx01_batch_nikto_scan_xff_clean_003.log
```

Nikto 批次是工具真打本機 Nginx/TixMaster 產生；正式掛進 `stage_log_map.txt` 的是 clean subset，保留 `10.99.1.41` 且符合 Nginx combined parser 的 4479 行。這補上原本 map 和 README 說法不一致的問題。

仍需保留 caveat：Nikto 是單一 scanner 工具，UA 指紋仍明顯，這批是 stage 1 coverage 補強，不是 UA diversity 的完整解法。

## bad_format clean subset

已針對 formal map 內仍有 bad_format 的來源建立 clean subset，並將 `stage_log_map.txt` 改指 clean 檔：

```text
stage 0: logs/access1_Aman_clean.log                  removed 1 malformed line
stage 3: collected/nginx01_batch_xss_zap_fullscan_clean_001.log removed 3 ZAP TLS/pre-header lines
stage 6: LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log removed 1 malformed line
```

原始 log 沒有刪，保留作 audit source；正式 ML map 只吃 parser-compatible Nginx combined log。
