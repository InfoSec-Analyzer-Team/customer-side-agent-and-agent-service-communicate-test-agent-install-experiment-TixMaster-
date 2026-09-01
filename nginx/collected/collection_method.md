# Nginx Attack Log Collection Method

本資料夾只保留可作為正式資料來源的 Nginx access log。PowerShell Invoke-WebRequest 產生的 scripted attack-like batches 已判定不能作為正式 ML 訓練資料；PowerShell 只能用來輔助啟動工具、切批次與檢查檔案，不作為正式攻擊流量產生工具。

保留原則：

```text
1. request 必須真的打到本機 Nginx / TixMaster lab target
2. access log 必須由 Nginx 自己產生，不手寫偽造 log
3. 惡意資料優先使用專用工具或明確手動漏洞驗證流程產生
4. backend 必須有開，避免整批只打到 Nginx 而變成 502
```

## Current Formal Logs

| Log | Label | Stage | Tool / Method | Count | Notes |
|---|---|---:|---|---:|---|
| `collected/nginx01_batch_sqli_sqlmap_randomua_002.log` | BAHAYA | 2 | sqlmap (`parrotsec/sqlmap`, `--random-agent`) | 378 | SQLi tool traffic through Nginx/backend, 200 responses |
| `collected/nginx01_batch_xss_zap_fullscan_001.log` | BAHAYA | 3 | OWASP ZAP Docker full scan | 790 | XSS active scan traffic; ZAP also emits some SQLi/protocol probes |
| `collected/nginx01_batch_path_traversal_ffuf_002.log` | BAHAYA | 4 | ffuf | 33 | Path traversal payloads against the lab attachment sink |
| `collected/nginx01_batch_double_encoding_ffuf_002.log` | BAHAYA | 7 | ffuf | 34 | Double-encoded traversal payloads against the lab attachment sink |
| `collected/nginx01_batch_url_encoding_count_ffuf_001.log` | BAHAYA | 8 | ffuf | 36 | Single-layer and multi-layer URL-encoded attack payloads against `/api/events?keyword=` |
| `collected/nginx01_batch_special_chars_dense_ffuf_001.log` | BAHAYA | 9 | ffuf | 30 | Dense special-character attack payloads against `/api/events?keyword=` |
| `collected/nginx01_batch_scanner_ua_gobuster_005.log` | BAHAYA | 10 | gobuster | 33 | Scanner User-Agent and directory enumeration traffic against the lab target |
| `collected/nginx01_batch_abnormal_methods_ffuf_002.log` | BAHAYA | 11 | ffuf | 100 | PUT/DELETE/OPTIONS/PATCH/TRACE requests against common lab paths |
| `collected/nginx01_batch_abnormal_url_ffuf_001.log` | BAHAYA | 12 | ffuf | 30 | Deep paths, long paths, repeated parameters, traversal-like segments, and unusual delimiters |
| `collected/nginx01_batch_command_injection_commix_001.log` | BAHAYA | 5 | commix | 1666 | Command injection tool traffic against `/api/events?keyword=` |
| `LFI_method_record/access3_Local_file_inclusion_1.log` | BAHAYA | 6 | Browser/manual LFI payload | 22 | Manual requests against the real attachment sink |
| `LFI_method_record/access4_Local_file_inclusion_2_wfuzz.log` | BAHAYA | 6 | wfuzz | 881 | LFI/path traversal wordlist run against the real attachment sink |
| `LFI_method_record/access5_Local_file_inclusion_3_wfuzz.log` | BAHAYA | 6 | wfuzz | 71 | Additional LFI/path traversal wordlist run |

## Removed From Formal Dataset

以下批次已移除或不再列入 `stage_log_map.txt`：

```text
nginx01_batch_sqli_browserua_001
nginx01_batch_xss_browserua_001
nginx01_batch_path_traversal_encoded_001
nginx01_batch_dicurigai_diverse_probe_001
nginx01_batch_command_injection_browserua_001
nginx01_batch_sqlmap_sqli_001
nginx01_batch_xss_001
nginx01_batch_path_traversal_001
nginx01_batch_nikto_scan_001
nginx01_batch_dicurigai_probe_001
```

## Remaining Replacement Plan

All 12 stages currently have mapped log data. Future work should focus on collecting additional batches across different IP ranges, time windows, and tool/user-agent settings.

## Current Caveats

目前 SQLi、XSS、path traversal、double encoding、URL encoding count、special chars dense、scanner UA、abnormal methods、abnormal URL、command injection 已符合「工具真打 Nginx/backend」的要求，但仍有泛化風險需要後續批次補強：

```text
- 單批 IP 幾乎都來自 Docker bridge，例如 172.17.0.1
- 單批時間集中在短時間內
- sqlmap/commix/wfuzz 這類工具批次仍可能有工具 UA 指紋
```

正式訓練前應使用多批次、不同時間、不同來源環境或不同工具設定補強 IP / time / UA diversity。

Stage 4 使用的 traversal-only payload 清單保存在 `collected/path_traversal_ffuf_payloads_002.txt`。
Stage 7 使用的 double-encoding payload 清單保存在 `collected/double_encoding_ffuf_payloads_001.txt`。
Stage 8 使用的 URL encoding payload 清單保存在 `collected/url_encoding_count_ffuf_payloads_001.txt`。
Stage 9 使用的 special-character payload 清單保存在 `collected/special_chars_dense_ffuf_payloads_001.txt`。
Stage 10 使用的 gobuster wordlist 保存在 `collected/scanner_ua_gobuster_wordlist_001.txt`。
Stage 11 使用的 abnormal-method path 清單保存在 `collected/abnormal_methods_ffuf_paths_001.txt`。
Stage 12 使用的 abnormal-URL payload 清單保存在 `collected/abnormal_url_ffuf_payloads_001.txt`。

## Labeling Rule

Nginx access.log 本身不包含 label。Label 應寫在對應 `.meta.txt`，或由 `stage_log_map.txt` 在轉 dataset 時補上。

```text
BAHAYA    = 明確攻擊 payload 或工具攻擊流量
DICURIGAI = 可疑探測、異常結構或掃描行為，但不一定是確認攻擊
AMAN      = 正常流量
```







